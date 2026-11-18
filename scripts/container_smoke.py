#!/usr/bin/env python3
"""Build and verify the local two-container runtime."""

import subprocess
import time
from collections.abc import Sequence

COMPOSE_COMMAND = ("docker", "compose")
SHUTDOWN_GRACE_SECONDS = 10
SHUTDOWN_BOUND_SECONDS = 15


def _run_compose(arguments: Sequence[str]) -> None:
    """Run a Docker Compose command and require it to succeed.

    Args:
        arguments:
            Arguments appended to the Docker Compose command.
    """
    subprocess.run([*COMPOSE_COMMAND, *arguments], check=True)


def _capture_compose(arguments: Sequence[str]) -> str:
    """Run a Docker Compose command and return its standard output.

    Args:
        arguments:
            Arguments appended to the Docker Compose command.

    Returns:
        Captured standard output with surrounding whitespace removed.
    """
    result = subprocess.run(
        [*COMPOSE_COMMAND, *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _verify_runtime() -> None:
    """Verify runtime identities, image contents, and UI-to-API communication."""
    for service in ("api", "ui"):
        user_id = _capture_compose(("exec", "-T", service, "id", "-u"))
        if user_id != "10001":
            message = f"{service} runs as UID {user_id}, expected 10001."
            raise RuntimeError(message)

        _run_compose(("exec", "-T", service, "test", "!", "-e", "/app/.env"))
        _run_compose(("exec", "-T", service, "test", "!", "-x", "/usr/local/bin/uv"))

    client_smoke = (
        "from portfolio_rag.ui import PortfolioApiClient, UiSettings; "
        "result = PortfolioApiClient(UiSettings()).answer_message("
        "'container smoke test'); assert result.is_placeholder"
    )
    _run_compose(("exec", "-T", "ui", "python", "-c", client_smoke))


def _stop_runtime() -> float:
    """Stop the composed runtime and return elapsed seconds.

    Returns:
        Seconds required for Compose to stop and remove the runtime.
    """
    started_at = time.monotonic()
    _run_compose(("down", "--timeout", str(SHUTDOWN_GRACE_SECONDS)))
    return time.monotonic() - started_at


def main() -> None:
    """Build, start, verify, and stop the local container runtime."""
    try:
        _run_compose(("up", "--build", "--wait", "--wait-timeout", "120"))
        _verify_runtime()
    finally:
        shutdown_seconds = _stop_runtime()

    if shutdown_seconds > SHUTDOWN_BOUND_SECONDS:
        message = (
            "Containers exceeded the "
            f"{SHUTDOWN_GRACE_SECONDS}-second shutdown grace period."
        )
        raise RuntimeError(message)

    print(
        "Container smoke test passed; shutdown completed in "
        f"{shutdown_seconds:.1f} seconds."
    )


if __name__ == "__main__":
    main()
