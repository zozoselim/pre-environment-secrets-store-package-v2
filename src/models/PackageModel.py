import json
import re
from typing import Dict, Literal, Union

from pydantic import Field, field_validator

from sdks.novavision.src.base.model import (
    Config,
    Configs,
    Inputs,
    Output,
    Outputs,
    Package,
    Request,
    Response,
)


class EmptyInputs(Inputs):
    """Environment Secrets Store does not require workflow input."""

    pass


class VariablesStoringSecrets(Config):
    """JSON list containing environment variable names."""

    name: Literal[
        "variables_storing_secrets"
    ] = "variables_storing_secrets"

    value: str = Field(min_length=2)

    type: Literal["string"] = "string"
    field: Literal["textInput"] = "textInput"

    placeHolder: Literal[
        '["OPENAI_API_KEY", "DATABASE_PASSWORD"]'
    ] = '["OPENAI_API_KEY", "DATABASE_PASSWORD"]'

    @field_validator("value")
    @classmethod
    def validate_variable_names(cls, value: str) -> str:
        try:
            variable_names = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Value must be a valid JSON list."
            ) from error

        if not isinstance(variable_names, list):
            raise ValueError(
                "Value must be a JSON list."
            )

        if not variable_names:
            raise ValueError(
                "At least one environment variable name is required."
            )

        cleaned_names = []
        seen_names = set()

        for variable_name in variable_names:
            if not isinstance(variable_name, str):
                raise ValueError(
                    "Environment variable names must be strings."
                )

            cleaned_name = variable_name.strip()

            if not re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*",
                cleaned_name,
            ):
                raise ValueError(
                    "Invalid environment variable name: "
                    f"{cleaned_name}"
                )

            if cleaned_name in seen_names:
                raise ValueError(
                    "Duplicate environment variable name: "
                    f"{cleaned_name}"
                )

            seen_names.add(cleaned_name)
            cleaned_names.append(cleaned_name)

        return json.dumps(cleaned_names)


class SecretsOutput(Output):
    """Requested secrets mapped by environment variable name."""

    name: Literal["secrets"] = "secrets"
    value: Dict[str, str]
    type: Literal["object"] = "object"

    class Config:
        title = "Secrets"


class EnvironmentSecretsStoreConfigs(Configs):
    variables_storing_secrets: VariablesStoringSecrets


class PackageOutputs(Outputs):
    secrets: SecretsOutput


class PackageRequest(Request):
    inputs: EmptyInputs = Field(default_factory=EmptyInputs)
    configs: EnvironmentSecretsStoreConfigs

    class Config:
        json_schema_extra = {
            "target": "configs",
        }


class PackageResponse(Response):
    outputs: PackageOutputs


class EnvironmentSecretsStoreExecutor(Config):
    name: Literal[
        "EnvironmentSecretsStore"
    ] = "EnvironmentSecretsStore"

    value: Union[
        PackageRequest,
        PackageResponse,
    ]

    type: Literal["object"] = "object"
    field: Literal["option"] = "option"

    class Config:
        title = "Environment Secrets Store"

        json_schema_extra = {
            "target": {
                "value": 0,
            }
        }


class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"

    value: EnvironmentSecretsStoreExecutor

    type: Literal["executor"] = "executor"
    field: Literal[
        "dependentDropdownlist"
    ] = "dependentDropdownlist"

    class Config:
        title = "Task"

        json_schema_extra = {
            "target": "value",
        }


class PackageConfigs(Configs):
    executor: ConfigExecutor


class PackageModel(Package):
    configs: PackageConfigs
    type: Literal["component"] = "component"

    name: Literal[
        "EnvironmentSecretsStore"
    ] = "EnvironmentSecretsStore"