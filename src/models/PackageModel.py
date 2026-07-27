import json
import re
from typing import List, Literal, Union

from pydantic import Field, validator

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


_ENV_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class EmptyInputs(Inputs):
    """Environment Secrets Store does not require workflow input."""

    pass


class OutputTypeStr(Config):
    name: Literal["Str"] = "Str"
    value: Literal["Str"] = "Str"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "Str"


class OutputTypeList(Config):
    name: Literal["List"] = "List"
    value: Literal["List"] = "List"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"

    class Config:
        title = "List"


class OutputType(Config):
    """Select the output payload type without changing the executor."""

    name: Literal["output_type"] = "output_type"
    value: Union[OutputTypeStr, OutputTypeList]
    type: Literal["object"] = "object"
    field: Literal[
        "dependentDropdownlist"
    ] = "dependentDropdownlist"
    restart: Literal[True] = True

    class Config:
        title = "Output Type"
        json_schema_extra = {
            "shortDescription": (
                "Str returns one secret as a string. List returns all "
                "requested secret values in configuration order."
            )
        }


class VariablesStoringSecrets(Config):
    """JSON list containing names of environment variables to retrieve."""

    name: Literal[
        "variables_storing_secrets"
    ] = "variables_storing_secrets"

    value: str = Field(
        default='["ENV_SECRET_TEST"]',
        min_length=2,
    )

    type: Literal["string"] = "string"
    field: Literal["textInput"] = "textInput"

    placeHolder: Literal[
        '["OPENAI_API_KEY", "DATABASE_PASSWORD"]'
    ] = '["OPENAI_API_KEY", "DATABASE_PASSWORD"]'

    @validator("value")
    def validate_variable_names(cls, value: str) -> str:
        """Validate and normalize the JSON list stored by the UI text field."""

        try:
            variable_names = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Value must be a valid JSON list of environment variable names."
            ) from error

        if not isinstance(variable_names, list):
            raise ValueError("Value must be a JSON list.")

        if not variable_names:
            raise ValueError(
                "At least one environment variable name is required."
            )

        cleaned_names = []
        seen_names = set()
        seen_output_names = set()

        for variable_name in variable_names:
            if not isinstance(variable_name, str):
                raise ValueError(
                    "Environment variable names must be strings."
                )

            cleaned_name = variable_name.strip()

            if not _ENV_NAME_PATTERN.fullmatch(cleaned_name):
                raise ValueError(
                    "Invalid environment variable name: "
                    f"{cleaned_name!r}."
                )

            if cleaned_name in seen_names:
                raise ValueError(
                    "Duplicate environment variable name: "
                    f"{cleaned_name}."
                )

            output_name = cleaned_name.lower()
            if output_name in seen_output_names:
                raise ValueError(
                    "Environment variable names must remain unique after "
                    f"lowercasing: {cleaned_name}."
                )

            seen_names.add(cleaned_name)
            seen_output_names.add(output_name)
            cleaned_names.append(cleaned_name)

        return json.dumps(cleaned_names)

    class Config:
        title = "Variables Storing Secrets"
        json_schema_extra = {
            "shortDescription": (
                "JSON list of environment variable names. Secret values are "
                "read only at runtime. Str requires one name; List accepts "
                "one or more names."
            )
        }


class SecretsOutput(Output):
    """Secret value returned as either a string or an ordered list."""

    name: Literal["secrets"] = "secrets"
    value: Union[str, List[str]]
    type: str = "string"

    @validator("type", pre=True, always=True)
    def set_type_based_on_value(cls, value, values):
        output_value = values.get("value")

        if isinstance(output_value, list):
            return "list"

        return "string"

    class Config:
        title = "Secrets"


class EnvironmentSecretsStoreConfigs(Configs):
    output_type: OutputType
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
    """Expose one Environment Secrets Store runtime executor."""

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
