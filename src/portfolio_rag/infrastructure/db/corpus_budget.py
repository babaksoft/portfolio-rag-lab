"""Persist corpus inference reservations across processes and interrupted runs."""

import sqlite3
from contextlib import closing
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from uuid import uuid4

_TOTAL_LIMIT_USD = Decimal("10")
_PILOT_LIMIT_USD = Decimal("2")
_LEDGER_UNITS_PER_USD = 1_000_000_000
"""Scale of existing SQLite integer charges, retained for ledger compatibility."""


class DbCorpusBudget:
    """Reserve and settle inference charges expressed in US dollars."""

    def __init__(self, path: Path) -> None:
        """Use one persistent ledger for all runs in the checkout.

        Args:
            path:
                SQLite ledger path shared by all runs in the checkout.
        """
        self._path: Path = path

    def reserve(self, cost_usd: Decimal, *, pilot: bool) -> str:
        """Atomically reserve the maximum charge before sending an attempt.

        Args:
            cost_usd:
                Estimated maximum charge in US dollars.
            pilot:
                Whether the charge also counts against the pilot limit.

        Returns:
            The reservation ID used to settle the charge.

        Raises:
            ValueError:
                The reservation would exceed a spend limit.
        """
        attempt = uuid4().hex
        charge = _to_ledger_units(cost_usd)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS charges ("
                "attempt TEXT PRIMARY KEY, pilot INTEGER NOT NULL, cost INTEGER NOT NULL)"
            )
            total, pilot_total = connection.execute(
                "SELECT COALESCE(SUM(cost), 0), "
                "COALESCE(SUM(CASE WHEN pilot THEN cost ELSE 0 END), 0) FROM charges"
            ).fetchone()
            if total + charge > _to_ledger_units(_TOTAL_LIMIT_USD) or (
                pilot and pilot_total + charge > _to_ledger_units(_PILOT_LIMIT_USD)
            ):
                raise ValueError("the corpus inference budget would be exceeded")
            connection.execute(
                "INSERT INTO charges VALUES (?, ?, ?)", (attempt, pilot, charge)
            )
        return attempt

    def settle(self, attempt: str, cost_usd: Decimal) -> None:
        """Replace a reservation with a charge calculated from reported usage.

        Args:
            attempt:
                Reservation ID returned by reserve.
            cost_usd:
                Charge in US dollars calculated from the provider's token counts.
        """
        charge = _to_ledger_units(cost_usd)
        with closing(sqlite3.connect(self._path)) as connection, connection:
            connection.execute(
                "UPDATE charges SET cost = ? WHERE attempt = ?", (charge, attempt)
            )


def _to_ledger_units(cost_usd: Decimal) -> int:
    """Convert dollars to the stored integer scale, rounding up if needed."""
    return int(
        (cost_usd * _LEDGER_UNITS_PER_USD).to_integral_value(rounding=ROUND_CEILING)
    )
