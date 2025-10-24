import re

from loguru import logger

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_PMC_ID_CHARS = {str(num) for num in range(0, 10)} | {"P", "M", "C"}


def validate_email(email: str) -> None:
    """Raise ValueError if email is not valid."""
    if not EMAIL_RE.fullmatch(email):
        raise ValueError(f"Invalid email format: {email}")
    logger.info(f"Email is valid! {email}")


def validate_pmc_id(pmc_id: str) -> None:
    """Raise ValueError if PMC ID is not valid."""
    pmc_id = pmc_id.upper()
    if not all(char in VALID_PMC_ID_CHARS for char in pmc_id):
        raise ValueError(f"Invalid characters in PMC ID: {pmc_id}")
    if pmc_id.startswith("PMC") and not pmc_id[3:].isdigit():
        raise ValueError(f"PMC ID is incorrectly formatted: {pmc_id}")
    if not pmc_id.startswith("PMC") and not all(char.isdigit() for char in pmc_id):
        raise ValueError(f"PMC ID is incorrectly formatted: {pmc_id}")
    logger.info(f"PMC ID is valid! {pmc_id}")
