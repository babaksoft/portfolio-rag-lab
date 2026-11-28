# Coding Agent Guide

## Tooling and layout

- Use Python 3.12 and `uv`; do not introduce another environment or dependency
  manager.
- Put first-party packages under `src/portfolio_rag/` and tests under `tests/`.
- Use absolute imports from `portfolio_rag`; do not use relative imports.
- Export public architecture symbols from their owning package's `__init__.py`.
  Import them from that boundary outside the package and from their defining
  module within it.
- Put inbound adapters under `api/` and `ui/`. Put outbound adapters under
  `infrastructure/`, organized by capability.
- Use Ruff for formatting and linting, mypy for type checking, and pytest for
  tests. Run all local checks with `./scripts/quality.sh`.
- Keep `master` as the default branch. Before handing off a change, run the
  configured quality command when available and always run `git diff --check`.

## Python conventions

- Use `snake_case` for modules, functions, methods, variables, and attributes;
  `PascalCase` for classes and type aliases; and `UPPER_SNAKE_CASE` for
  constants. Name private implementation details with a single leading
  underscore. Avoid unexplained abbreviations.
- Add complete parameter and return type hints to first-party production
  callables and type all production class attributes. `self` and `cls` need no
  annotation. Tests, fixtures, and one-line local callbacks are exempt unless
  an annotation improves clarity or is required by the type checker.
- Give every first-party Python module, class, and callable a Google-style
  docstring. This includes constructors, dunder methods, property accessors,
  protocol methods, overrides, local callbacks, tests, and fixtures.
- Document public class and instance attributes and all Pydantic fields in the
  class docstring's `Attributes:` section. Document constructor parameters
  that initialize private attributes in the `__init__` docstring's `Args:`
  section.
- Omit empty `Args:` sections and omit `Returns:` for `None`. Under `Args:`,
  `Raises:`, and `Attributes:`, put each name on its own line and indent its
  description beneath it.
- Use single blank lines to separate logical phases within a callable.
  If a callable needs several phases or section-label comments, prefer extracting
  well-named helpers.
- Prefer module-level functions in production code and tests. Nest a function
  only when a required closure or another design constraint calls for it.
- Give every Pydantic model field a useful `Field(description=...)`. For fields
  persisted outside process memory, also document storage meaning, nullability
  or default behavior, lifecycle, and units or format wherever those facts are
  not obvious from the type and name.
- Use Pydantic models consistently for structured domain and application values
  and for boundary contracts. Prefer `ConfigDict(frozen=True, extra="forbid")`
  for value-like models unless anticipated mutation or extra attributes are
  part of the contract. Use a dataclass only when a concrete performance or
  interoperability requirement justifies the inconsistency.
- Implement each application use case as a narrow, verb-led `*Service` class
  under `application/services/`, in a matching `snake_case` module, with one
  public `execute()` operation. Do not group unrelated operations in broad
  services.
- Name domain behavior by its role, such as `*Policy`, `*Strategy`, or
  `*Validator`. Use `*Service` only for domain behavior that belongs to no
  entity or value object.

## Test conventions

- Use private module-level functions (prefixed with `_`) to create test values,
  fakes, and simulated behavior.
- Limit test helpers to Arrange logic. Exercise the code under test and make
  all assertions in the `test_*` function.

## Persistence conventions

- Put persistence code under `src/portfolio_rag/infrastructure/db/`, mapped
  models under `db/models/`, and adapters under `db/repositories/`. Group
  closely related models in a suitably named module.
- Prefix database-backed repository classes with `Db` (for example,
  `DbIdentityRepository`); keep domain repository protocols unprefixed (for
  example, `IdentityRepository`).
- Name domain values naturally (for example, `Identity`) and suffix their
  persistence models with `Model` (for example, `IdentityModel`). This and the
  repository naming rule must allow both boundary types to be imported without
  redundant aliases.
- Give variable-length string columns purpose-specific maximum lengths,
  preferably multiples of 16, and match user-authored domain validation maxima
  to them. Exact bounded internal values may use their known maximum length.

## Change policy

- Keep changes in small, independently verifiable slices. A slice should
  normally contain 200–500 meaningful changed lines; split work above roughly
  800 meaningful lines or work containing more than one major design decision.
  Treat generated and mechanical changes separately from conceptual changes.
- Update only documentation whose truth changed, and keep provider, framework,
  and advanced-retrieval choices deferred until their planned stage.
- Never add secrets. Put only names and safe placeholder values in
  `.env.example`.
- Keep local secret files out of coding-session tool inputs and outputs. Use
  synthetic credentials to test secret loading.
- Do not create commits, tags, branches, pull requests, or remote resources
  unless the user explicitly requests them. Preserve unrelated user changes.
