"""Safe local HTTP client for the Environment Secrets Store component."""

import copy
import json
import os
from typing import Any, Dict

import requests


ENDPOINT_URL = os.getenv(
    "NOVAVISION_ENDPOINT_URL",
    "http://127.0.0.1:8000/api",
)


def build_request() -> Dict[str, Any]:
    variable_names = json.loads(
        os.getenv(
            "ENV_SECRET_NAMES",
            '["ENV_SECRET_TEST"]',
        )
    )

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


def masked_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask every dynamic output value before printing the response."""

    result = copy.deepcopy(response_data)

    try:
        outputs = result[
            "configs"
        ]["executor"]["value"]["value"]["outputs"]
    except (KeyError, TypeError):
        return result

    if not isinstance(outputs, dict):
        return result

    for output in outputs.values():
        if isinstance(output, dict) and "value" in output:
            output["value"] = "***REDACTED***"

    return result


def main() -> None:
    response = requests.post(
        ENDPOINT_URL,
        json=build_request(),
        timeout=30,
    )
    response.raise_for_status()
    print(
        json.dumps(
            masked_response(response.json()),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
