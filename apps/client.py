"""Safe HTTP client for the Environment Secrets Store component."""

import copy
import json
import os
import sys
from typing import Any, Dict, List, Set

import requests


DEFAULT_ENDPOINT_URL = "http://127.0.0.1:8000/api"
DEFAULT_TIMEOUT_SECONDS = 30
REDACTED_VALUE = "***REDACTED***"


def parse_variable_names(raw_value: str) -> List[str]:
    """Parse and validate environment variable names supplied to the client."""

    try:
        variable_names = json.loads(raw_value)
    except json.JSONDecodeError as error:
        raise ValueError(
            "ENV_SECRET_NAMES geçerli bir JSON listesi olmalıdır."
        ) from error

    if not isinstance(variable_names, list) or not variable_names:
        raise ValueError(
            "ENV_SECRET_NAMES en az bir değişken adı içermelidir."
        )

    cleaned_names: List[str] = []
    seen_output_names: Set[str] = set()

    for variable_name in variable_names:
        if not isinstance(variable_name, str):
            raise ValueError(
                "Environment variable adlarının tamamı string olmalıdır."
            )

        cleaned_name = variable_name.strip()

        if not cleaned_name:
            raise ValueError(
                "Environment variable adı boş olamaz."
            )

        output_name = cleaned_name.lower()

        if output_name in seen_output_names:
            raise ValueError(
                "Environment variable adları küçük harfe çevrildiğinde "
                "benzersiz olmalıdır."
            )

        seen_output_names.add(output_name)
        cleaned_names.append(cleaned_name)

    return cleaned_names


def build_request(variable_names: List[str]) -> Dict[str, Any]:
    """Create the NovaVision component request payload."""

    return {
        "name": "EnvironmentSecretsStore",
        "type": "component",
        "uID": "environment-secrets-store-client",
        "configs": {
            "executor": {
                "name": "ConfigExecutor",
                "type": "executor",
                "field": "dependentDropdownlist",
                "value": {
                    "name": "EnvironmentSecretsStore",
                    "type": "object",
                    "field": "option",
                    "value": {
                        "inputs": {},
                        "configs": {
                            "variables_storing_secrets": {
                                "name": "variables_storing_secrets",
                                "value": json.dumps(variable_names),
                                "type": "string",
                                "field": "textInput",
                            }
                        },
                    },
                },
            }
        },
    }


def mask_secret_values(
    value: Any,
    secret_output_names: Set[str],
) -> Any:
    """Recursively mask secret values without modifying the original object."""

    if isinstance(value, list):
        return [
            mask_secret_values(item, secret_output_names)
            for item in value
        ]

    if not isinstance(value, dict):
        return value

    masked: Dict[str, Any] = {}
    object_name = value.get("name")

    for key, nested_value in value.items():
        normalized_key = str(key).lower()

        if normalized_key in secret_output_names:
            masked[key] = REDACTED_VALUE
            continue

        if (
            key == "value"
            and object_name == "secrets"
            and isinstance(nested_value, dict)
        ):
            masked[key] = {
                secret_name: REDACTED_VALUE
                for secret_name in nested_value
            }
            continue

        if key == "secrets" and isinstance(nested_value, dict):
            masked[key] = mask_secrets_output(
                nested_value,
                secret_output_names,
            )
            continue

        masked[key] = mask_secret_values(
            nested_value,
            secret_output_names,
        )

    return masked


def mask_secrets_output(
    secrets_output: Dict[str, Any],
    secret_output_names: Set[str],
) -> Dict[str, Any]:
    """Mask both NovaVision output metadata and direct secrets mappings."""

    masked = copy.deepcopy(secrets_output)

    if isinstance(masked.get("value"), dict):
        masked["value"] = {
            secret_name: REDACTED_VALUE
            for secret_name in masked["value"]
        }
        return masked

    return {
        key: (
            REDACTED_VALUE
            if key.lower() in secret_output_names
            else mask_secret_values(value, secret_output_names)
        )
        for key, value in masked.items()
    }


def masked_response(
    response_data: Dict[str, Any],
    variable_names: List[str],
) -> Dict[str, Any]:
    """Return a deeply copied response with all requested secrets masked."""

    secret_output_names = {
        variable_name.lower()
        for variable_name in variable_names
    }

    return mask_secret_values(
        copy.deepcopy(response_data),
        secret_output_names,
    )


def main() -> int:
    endpoint_url = os.getenv(
        "NOVAVISION_ENDPOINT_URL",
        DEFAULT_ENDPOINT_URL,
    )

    raw_variable_names = os.getenv(
        "ENV_SECRET_NAMES",
        '["ENV_SECRET_TEST"]',
    )

    try:
        variable_names = parse_variable_names(raw_variable_names)
    except ValueError as error:
        print(f"[FAILED] Client configuration error: {error}")
        return 2

    try:
        response = requests.post(
            endpoint_url,
            json=build_request(variable_names),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        print("[FAILED] NovaVision runtime request timed out.")
        return 3
    except requests.ConnectionError:
        print("[FAILED] NovaVision runtime connection could not be established.")
        return 4
    except requests.RequestException as error:
        print(
            "[FAILED] NovaVision runtime request failed: "
            f"{type(error).__name__}"
        )
        return 5

    try:
        response_data = response.json()
    except ValueError:
        print(
            "[FAILED] NovaVision runtime returned a non-JSON response. "
            f"HTTP status: {response.status_code}"
        )
        return 6

    safe_response = masked_response(
        response_data,
        variable_names,
    )

    if not response.ok:
        print(
            "[FAILED] NovaVision runtime rejected the request. "
            f"HTTP status: {response.status_code}"
        )
        print(
            json.dumps(
                safe_response,
                indent=2,
                ensure_ascii=False,
            )
        )
        return 7

    print("[SUCCESS] Environment Secrets Store request completed.")
    print(
        json.dumps(
            safe_response,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())