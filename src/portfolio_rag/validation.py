"""Reusable string-validation patterns shared by Pydantic and other validators."""

LOWER_KEBAB_CASE_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
"""Lowercase ASCII letters and digits grouped by single hyphens."""

SHA256_HEX_PATTERN = r"^[0-9a-f]{64}$"
"""A lowercase hexadecimal SHA-256 digest."""

NON_BLANK_PATTERN = r"\S"
"""At least one non-whitespace character anywhere in the string."""

GIT_CHECKOUT_NAME_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$"
"""An ASCII checkout basename starting with a letter or digit."""

GIT_SHA1_PATTERN = r"^[a-f0-9]{40}$"
"""A full lowercase hexadecimal Git SHA-1 object ID."""

GIT_PATH_PART_PATTERN = r"[A-Za-z0-9._-]+"
"""Characters allowed in one component of a literal Git source path."""

SINGLE_LINE_PATTERN = r"^[^\r\n]+$"
"""A nonempty line containing neither a carriage return nor a line feed."""

POSTGRES_IDENTIFIER_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
"""The restricted ASCII form used for PostgreSQL database and role names."""
