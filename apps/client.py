"""Safe local HTTP client for the Environment Secrets Store component."""

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
    """Mask secret values before printing the server response."""

    try:
        secrets = response_data[
            "configs"
        ]["executor"]["value"]["value"]["outputs"]["secrets"]["value"]
        response_data = dict(response_data)
        masked = {
            key: "***REDACTED***"
            for key in secrets
        }
        response_data["configs"]["executor"]["value"]["value"][
            "outputs"
        ]["secrets"]["value"] = masked
    except (KeyError, TypeError):
        pass

    return response_data


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
