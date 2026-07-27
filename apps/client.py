"""NovaVision runtime client for Environment Secrets Store."""

import copy
import json
import os
import sys
import time
import uuid
from typing import Any, Dict, List, Set


DEFAULT_COMPONENT_UID = "Kba9Cw"
DEFAULT_TIMEOUT_SECONDS = 30.0
REDACTED_VALUE = "***REDACTED***"


def parse_variable_names(raw_value: str) -> List[str]:
    """Parse and validate requested environment variable names."""

    try:
        variable_names = json.loads(raw_value)
    except json.JSONDecodeError as error:
        raise ValueError(
            "ENV_SECRET_NAMES must be a valid JSON list."
        ) from error

    if not isinstance(variable_names, list) or not variable_names:
        raise ValueError(
            "ENV_SECRET_NAMES must contain at least one variable name."
        )

    cleaned_names: List[str] = []
    seen_output_names: Set[str] = set()

    for variable_name in variable_names:
        if not isinstance(variable_name, str):
            raise ValueError(
                "Environment variable names must be strings."
            )

        cleaned_name = variable_name.strip()

        if not cleaned_name:
            raise ValueError(
                "Environment variable names cannot be empty."
            )

        output_name = cleaned_name.lower()

        if output_name in seen_output_names:
            raise ValueError(
                "Environment variable names must remain unique "
                "after lowercasing."
            )

        seen_output_names.add(output_name)
        cleaned_names.append(cleaned_name)

    return cleaned_names



def parse_output_type(raw_value: str) -> str:
    """Validate the selected secret output mode."""

    normalized = raw_value.strip().lower()
    mapping = {
        "str": "Str",
        "string": "Str",
        "list": "List",
    }

    if normalized not in mapping:
        raise ValueError(
            "ENV_SECRET_OUTPUT_TYPE must be Str or List."
        )

    return mapping[normalized]

def build_request(
    variable_names: List[str],
    component_uid: str,
    flow_uid: str,
    output_type: str = "Str",
) -> Dict[str, Any]:
    """Build a request matching NovaVision's single-executor schema."""

    selected_output_type = parse_output_type(output_type)

    if selected_output_type == "Str" and len(variable_names) != 1:
        raise ValueError(
            "Str output requires exactly one environment variable name."
        )

    return {
        "type": "component",
        "name": "EnvironmentSecretsStore",
        "configs": {
            "executor": {
                "name": "ConfigExecutor",
                "value": {
                    "name": "EnvironmentSecretsStore",
                    "value": {
                        "name": "EnvironmentSecretsStore",
                        "inputs": {
                            "name": "EnvironmentSecretsStore",
                        },
                        "configs": {
                            "output_type": {
                                "name": "output_type",
                                "value": {
                                    "name": selected_output_type,
                                    "value": selected_output_type,
                                    "type": "string",
                                    "field": "option",
                                },
                                "type": "object",
                                "field": "dependentDropdownlist",
                                "restart": True,
                            },
                            "variables_storing_secrets": {
                                "name": "variables_storing_secrets",
                                "value": json.dumps(
                                    variable_names
                                ),
                                "type": "string",
                                "field": "textInput",
                                "placeHolder": (
                                    '["OPENAI_API_KEY", '
                                    '"DATABASE_PASSWORD"]'
                                ),
                            },
                        },
                    },
                    "type": "object",
                    "field": "option",
                },
                "type": "executor",
                "field": "dependentDropdownlist",
            }
        },
        "debug": "False",
        "api": "True",
        "uID": component_uid,
        "flowUID": flow_uid,
        "matchedID": None,
        "status": "success",
    }


def mask_secret_values(
    value: Any,
    secret_output_names: Set[str],
) -> Any:
    """Recursively mask requested secret values."""

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

        if key == "value" and object_name == "secrets":
            if isinstance(nested_value, dict):
                masked[key] = {
                    secret_name: REDACTED_VALUE
                    for secret_name in nested_value
                }
            elif isinstance(nested_value, list):
                masked[key] = [
                    REDACTED_VALUE
                    for _ in nested_value
                ]
            else:
                masked[key] = REDACTED_VALUE
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
    """Mask NovaVision output metadata and direct secret mappings."""

    masked = copy.deepcopy(secrets_output)

    if "value" in masked:
        value = masked["value"]
        if isinstance(value, dict):
            masked["value"] = {
                secret_name: REDACTED_VALUE
                for secret_name in value
            }
        elif isinstance(value, list):
            masked["value"] = [
                REDACTED_VALUE
                for _ in value
            ]
        else:
            masked["value"] = REDACTED_VALUE
        return masked

    return {
        key: (
            REDACTED_VALUE
            if key.lower() in secret_output_names
            else mask_secret_values(
                nested_value,
                secret_output_names,
            )
        )
        for key, nested_value in masked.items()
    }

def masked_response(
    response_data: Dict[str, Any],
    variable_names: List[str],
) -> Dict[str, Any]:
    """Return a safe copy with requested secret values masked."""

    secret_output_names = {
        variable_name.lower()
        for variable_name in variable_names
    }

    return mask_secret_values(
        copy.deepcopy(response_data),
        secret_output_names,
    )


def create_runtime_client():
    """Create NovaVision's Redis-backed runtime client."""

    try:
        from sdks.novavision.src.base.application import (
            Application,
        )
        from sdks.novavision.src.base.environment import (
            Environment,
        )
        from sdks.novavision.src.base.redis import MqttClient
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "NovaVision SDK could not be imported. "
            "Run this client inside the NovaVision runtime image."
        ) from error

    application = Application()
    environment = Environment()

    return MqttClient(
        application=application,
        environment=environment,
    )


def wait_until_subscribed(
    pubsub,
    timeout_seconds: float = 5.0,
) -> None:
    """Wait until Redis confirms the response subscription."""

    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        message = pubsub.get_message(timeout=0.25)

        if message and message.get("type") == "subscribe":
            return

    raise TimeoutError(
        "Response channel subscription could not be confirmed."
    )


def wait_for_response(
    pubsub,
    component_uid: str,
    flow_uid: str,
    timeout_seconds: float,
) -> Dict[str, Any]:
    """Wait for the matching NovaVision response message."""

    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        message = pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=0.5,
        )

        if not message:
            continue

        raw_data = message.get("data")

        if not isinstance(raw_data, (str, bytes)):
            continue

        try:
            response_data = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            continue

        if response_data.get("uID") != component_uid:
            continue

        response_flow_uid = response_data.get("flowUID")

        if (
            response_flow_uid is not None
            and response_flow_uid != flow_uid
        ):
            continue

        return response_data

    raise TimeoutError(
        "NovaVision runtime response timed out."
    )


def run_runtime_request(
    payload: Dict[str, Any],
    component_uid: str,
    timeout_seconds: float,
) -> Dict[str, Any]:
    """Publish the request and receive its runtime response."""

    runtime_client = create_runtime_client()
    response_pubsub = runtime_client.initialize_pubsub_client(
        "response"
    )

    try:
        wait_until_subscribed(response_pubsub)

        subscriber_count = runtime_client._publish(
            component_uid,
            json.dumps(payload),
        )

        if not subscriber_count:
            raise RuntimeError(
                "No NovaVision executor is subscribed to component "
                f"UID {component_uid}."
            )

        return wait_for_response(
            pubsub=response_pubsub,
            component_uid=component_uid,
            flow_uid=payload["flowUID"],
            timeout_seconds=timeout_seconds,
        )
    finally:
        response_pubsub.close()


def main() -> int:
    raw_variable_names = os.getenv(
        "ENV_SECRET_NAMES",
        '["ENV_SECRET_TEST"]',
    )

    component_uid = os.getenv(
        "NOVAVISION_COMPONENT_UID",
        DEFAULT_COMPONENT_UID,
    ).strip()

    raw_output_type = os.getenv(
        "ENV_SECRET_OUTPUT_TYPE",
        "Str",
    )

    try:
        timeout_seconds = float(
            os.getenv(
                "NOVAVISION_CLIENT_TIMEOUT",
                str(DEFAULT_TIMEOUT_SECONDS),
            )
        )
    except ValueError:
        print(
            "[FAILED] NOVAVISION_CLIENT_TIMEOUT "
            "must be a number."
        )
        return 2

    if not component_uid:
        print(
            "[FAILED] NOVAVISION_COMPONENT_UID "
            "cannot be empty."
        )
        return 2

    try:
        variable_names = parse_variable_names(
            raw_variable_names
        )
        output_type = parse_output_type(
            raw_output_type
        )
    except ValueError as error:
        print(f"[FAILED] Client configuration error: {error}")
        return 2

    flow_uid = f"environment-secrets-client-{uuid.uuid4()}"

    payload = build_request(
        variable_names=variable_names,
        component_uid=component_uid,
        flow_uid=flow_uid,
        output_type=output_type,
    )

    try:
        response_data = run_runtime_request(
            payload=payload,
            component_uid=component_uid,
            timeout_seconds=timeout_seconds,
        )
    except TimeoutError as error:
        print(f"[FAILED] {error}")
        return 3
    except RuntimeError as error:
        print(f"[FAILED] {error}")
        return 4
    except Exception as error:
        print(
            "[FAILED] Unexpected NovaVision runtime error: "
            f"{type(error).__name__}"
        )
        return 5

    safe_response = masked_response(
        response_data,
        variable_names,
    )

    if response_data.get("status") != "success":
        print(
            "[FAILED] Environment Secrets Store "
            "runtime execution failed."
        )
        print(
            json.dumps(
                safe_response,
                indent=2,
                ensure_ascii=False,
            )
        )
        return 6

    print(
        "[SUCCESS] Environment Secrets Store "
        "runtime execution completed."
    )
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