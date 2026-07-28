"""Encryption helpers for transferring secrets between components."""

import json
from typing import Dict, Sequence

from cryptography.fernet import Fernet, InvalidToken
from sdks.novavision.src.base.environment import Environment

from .environment import read_required_value, read_secrets


ENCRYPTION_KEY_VARIABLE = "ENVIRONMENT_SECRETS_ENCRYPTION_KEY"
SUCCESS_MESSAGE = (
    "Requested secret values were resolved and encrypted successfully."
)
ENCRYPTION_ALGORITHM = "fernet"


def encrypt_secrets(
    secrets: Dict[str, str],
    encryption_key: str,
) -> str:
    """Serialize and encrypt a secret mapping."""

    try:
        cipher = Fernet(
            encryption_key.encode("utf-8")
        )
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f"{ENCRYPTION_KEY_VARIABLE} is not a valid Fernet key."
        ) from error

    serialized = json.dumps(
        secrets,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return cipher.encrypt(serialized).decode("utf-8")


def decrypt_secrets(
    encrypted_payload: str,
    encryption_key: str,
) -> Dict[str, str]:
    """Decrypt an encrypted secret bundle in a trusted downstream component."""

    try:
        cipher = Fernet(
            encryption_key.encode("utf-8")
        )
        decrypted = cipher.decrypt(
            encrypted_payload.encode("utf-8")
        )
        values = json.loads(
            decrypted.decode("utf-8")
        )
    except (InvalidToken, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "Encrypted secret payload could not be decrypted."
        ) from error

    if (
        not isinstance(values, dict)
        or not all(
            isinstance(key, str)
            and isinstance(value, str)
            for key, value in values.items()
        )
    ):
        raise RuntimeError(
            "Decrypted secret payload has an invalid structure."
        )

    return values


def resolve_secure_secrets(
    variable_names: Sequence[str],
) -> Dict[str, str]:
    """Resolve secrets and return only a message plus encrypted payload."""

    environment = Environment()

    secrets = read_secrets(
        environment=environment,
        variable_names=variable_names,
    )

    encryption_key = read_required_value(
        environment=environment,
        variable_name=ENCRYPTION_KEY_VARIABLE,
    )

    encrypted_payload = encrypt_secrets(
        secrets=secrets,
        encryption_key=encryption_key,
    )

    return {
        "message": SUCCESS_MESSAGE,
        "encrypted_payload": encrypted_payload,
        "encryption": ENCRYPTION_ALGORITHM,
    }
