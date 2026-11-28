import ast
import sys
from collections.abc import Iterator
from importlib.util import resolve_name
from pathlib import Path

import pytest

PACKAGE = "portfolio_rag"
SOURCE = Path(__file__).resolve().parents[1] / "src" / PACKAGE

# Some values and contracts are imported through their package re-exports.
APPLICATION_CONTRACTS = (
    "portfolio_rag.application.identity",
    "portfolio_rag.application.AuthenticationError",
    "portfolio_rag.application.AuthorizationError",
    "portfolio_rag.application.IdentityResolver",
    "portfolio_rag.application.IdentityVerifier",
)
ANSWER_VALUE = (
    "portfolio_rag.application.services.AnswerMessageResult",
    "portfolio_rag.application.services.answer_message.AnswerMessageResult",
)
HTTP_DOMAIN_TYPES = (
    "portfolio_rag.domain.identity",
    "portfolio_rag.domain.AuthenticatedPrincipal",
    "portfolio_rag.domain.Identity",
)
LOGGING_HELPER = (
    "portfolio_rag.observability",
    "portfolio_rag.JsonLogFormatter",
    "portfolio_rag.bind_correlation_id",
    "portfolio_rag.configure_structured_logging",
    "portfolio_rag.current_correlation_id",
    "portfolio_rag.reset_correlation_id",
)
DEPENDENCIES = {
    "": ("portfolio_rag.observability",),
    "observability": (),
    "validation": (),
    "domain": ("pydantic",),
    "application": ("portfolio_rag.domain", "portfolio_rag.validation", "pydantic"),
    "infrastructure": (
        "portfolio_rag.domain",
        *APPLICATION_CONTRACTS,
        *ANSWER_VALUE,
        "portfolio_rag.application.services.GenerationResponse",
        "portfolio_rag.validation",
        *LOGGING_HELPER,
    ),
    "api": (
        "portfolio_rag.application.services",
        *APPLICATION_CONTRACTS,
        *HTTP_DOMAIN_TYPES,
        "portfolio_rag.validation",
        *LOGGING_HELPER,
        "fastapi",
        "starlette",
        "pydantic",
        "pydantic_settings",
    ),
    "ui": (*LOGGING_HELPER, "streamlit", "httpx", "pydantic", "pydantic_settings"),
    "composition": (
        "portfolio_rag.api",
        "portfolio_rag.application",
        "portfolio_rag.domain",
        "portfolio_rag.infrastructure",
        "portfolio_rag.ui",
        *LOGGING_HELPER,
    ),
}
ADAPTER_LAYERS = {"composition", "infrastructure"}


def _import_targets(source: str, package: str) -> Iterator[tuple[int, str]]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = resolve_name("." * node.level + module, package)
            for alias in node.names:
                yield node.lineno, f"{module}.{alias.name}"


def _import_allowed(layer: str, target: str) -> bool:
    root = target.split(".", 1)[0]
    if root in sys.stdlib_module_names:
        return True
    if root != PACKAGE and layer in ADAPTER_LAYERS:
        return True

    allowed = DEPENDENCIES[layer]
    if layer:
        allowed = (*allowed, f"{PACKAGE}.{layer}")
    return any(
        target == prefix or target.startswith(f"{prefix}.") for prefix in allowed
    )


def _dependency_violations(source_dir: Path) -> list[str]:
    violations = []
    for path in sorted(source_dir.rglob("*.py")):
        relative_path = path.relative_to(source_dir)
        layer = relative_path.parts[0] if len(relative_path.parts) > 1 else path.stem
        if layer == "__init__":
            layer = ""
        if layer not in DEPENDENCIES:
            violations.append(f"{relative_path}: no dependency rules for {layer!r}")
            continue

        package = ".".join((PACKAGE, *relative_path.parent.parts))
        for line, target in _import_targets(path.read_text(encoding="utf-8"), package):
            if not _import_allowed(layer, target):
                violations.append(f"{relative_path}:{line}: forbidden import {target}")
    return violations


def test_package_dependencies_follow_architecture() -> None:
    violations = _dependency_violations(SOURCE)
    assert violations == [], "\n".join(violations)


@pytest.mark.parametrize(
    ("path", "source", "target"),
    [
        ("domain/identity.py", "import fastapi", "fastapi"),
        (
            "domain/identity.py",
            "if TYPE_CHECKING:\n    from portfolio_rag import application",
            "portfolio_rag.application",
        ),
        (
            "api/__init__.py",
            "from portfolio_rag.composition import create_app as startup",
            "portfolio_rag.composition.create_app",
        ),
        (
            "api/routes/__init__.py",
            "from ...infrastructure.db import Database as Database",
            "portfolio_rag.infrastructure.db.Database",
        ),
        (
            "application/__init__.py",
            "from portfolio_rag.infrastructure.db import Database",
            "portfolio_rag.infrastructure.db.Database",
        ),
        (
            "infrastructure/db/repository.py",
            "from portfolio_rag.application.services import ResolveIdentityService",
            "portfolio_rag.application.services.ResolveIdentityService",
        ),
        ("ui/app.py", "from portfolio_rag import api", "portfolio_rag.api"),
        ("api/app.py", "import sqlalchemy", "sqlalchemy"),
        (
            "api/dependencies.py",
            "from portfolio_rag.domain import Identity, IdentityRepository",
            "portfolio_rag.domain.IdentityRepository",
        ),
        (
            "__init__.py",
            "from .composition import create_app",
            "portfolio_rag.composition.create_app",
        ),
        ("observability.py", "from . import api", "portfolio_rag.api"),
    ],
)
def test_dependency_check_rejects_forbidden_imports_and_reexports(
    tmp_path: Path, path: str, source: str, target: str
) -> None:
    module = tmp_path / path
    module.parent.mkdir(parents=True, exist_ok=True)
    module.write_text(source, encoding="utf-8")

    line = 2 if source.startswith("if ") else 1
    assert _dependency_violations(tmp_path) == [
        f"{path}:{line}: forbidden import {target}"
    ]


def test_dependency_check_accepts_application_values_and_runtime_logging(
    tmp_path: Path,
) -> None:
    infrastructure = tmp_path / "infrastructure"
    infrastructure.mkdir()
    (infrastructure / "adapter.py").write_text(
        "from portfolio_rag.application.services import AnswerMessageResult\n"
        "from portfolio_rag import configure_structured_logging\n",
        encoding="utf-8",
    )

    assert _dependency_violations(tmp_path) == []
