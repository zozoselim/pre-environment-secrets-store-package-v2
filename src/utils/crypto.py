"""Authenticated encryption helpers for workflow secret transport."""

import json
from typing import Mapping

from cryptography.fernet import Fernet


def encrypt_secret_values(
    secret_values: Mapping[str, str],
    transport_key: str,
) -> str:
    """Serialize and encrypt secret values as one URL-safe string."""

    if not secret_values:
        raise ValueError("At least one secret value is required.")

    try:
        cipher = Fernet(transport_key.encode("utf-8"))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            "NOVAVISION_SECRET_TRANSPORT_KEY is not a valid Fernet key."
        ) from error

    payload = json.dumps(
        dict(secret_values),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return cipher.encrypt(payload).decode("utf-8")
