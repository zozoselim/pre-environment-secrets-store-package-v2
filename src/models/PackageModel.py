import json
import re
from typing import Literal, Union

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
_TRANSPORT_KEY_VARIABLE = "NOVAVISION_SECRET_TRANSPORT_KEY"


class EmptyInputs(Inputs):
    """Environment Secrets Store does not require workflow input."""

    pass


class VariablesStoringSecrets(Config):
    """JSON list containing environment-variable names to encrypt."""

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
        '["ACCESS_TOKEN", "DATABASE_PASSWORD"]'
    ] = '["ACCESS_TOKEN", "DATABASE_PASSWORD"]'

    @validator("value")
    def validate_variable_names(cls, value: str) -> str:
        try:
            variable_names = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Value must be a valid JSON list of "
                "environment variable names."
            ) from error

        if not isinstance(variable_names, list) or not variable_names:
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

            if not _ENV_NAME_PATTERN.fullmatch(cleaned_name):
                raise ValueError(
                    "Invalid environment variable name: "
                    f"{cleaned_name!r}."
                )

            if cleaned_name == _TRANSPORT_KEY_VARIABLE:
                raise ValueError(
                    f"{_TRANSPORT_KEY_VARIABLE} is reserved for "
                    "encrypted secret transport."
                )

            normalized_name = cleaned_name.lower()

            if normalized_name in seen_names:
                raise ValueError(
                    "Environment variable names must be unique."
                )

            seen_names.add(normalized_name)
            cleaned_names.append(cleaned_name)

        return json.dumps(cleaned_names)

    class Config:
        title = "Variables Storing Secrets"
        json_schema_extra = {
            "shortDescription": (
                "JSON list of environment-variable names. Values are "
                "encrypted before being exposed to downstream components."
            )
        }


class EncryptedSecretsOutput(Output):
    """Authenticated ciphertext containing the requested secret values."""

    name: Literal["encryptedSecrets"] = "encryptedSecrets"
    value: str
    type: Literal["string"] = "string"

    class Config:
        title = "Encrypted Secrets"


class MessageOutput(Output):
    """Safe execution status that never contains secret values."""

    name: Literal["message"] = "message"
    value: str
    type: Literal["string"] = "string"

    class Config:
        title = "Message"


class EnvironmentSecretsStoreConfigs(Configs):
    variables_storing_secrets: VariablesStoringSecrets


class PackageOutputs(Outputs):
    encryptedSecrets: EncryptedSecretsOutput
    message: MessageOutput


class PackageRequest(Request):
    inputs: EmptyInputs = Field(default_factory=EmptyInputs)
    configs: EnvironmentSecretsStoreConfigs

    class Config:
        json_schema_extra = {"target": "configs"}


class PackageResponse(Response):
    outputs: PackageOutputs


class EnvironmentSecretsStoreExecutor(Config):
    name: Literal[
        "EnvironmentSecretsStore"
    ] = "EnvironmentSecretsStore"

    value: Union[PackageRequest, PackageResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"

    class Config:
        title = "Environment Secrets Store"
        json_schema_extra = {"target": {"value": 0}}


class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"
    value: EnvironmentSecretsStoreExecutor
    type: Literal["executor"] = "executor"
    field: Literal[
        "dependentDropdownlist"
    ] = "dependentDropdownlist"

    class Config:
        title = "Task"
        json_schema_extra = {"target": "value"}


class PackageConfigs(Configs):
    executor: ConfigExecutor


class PackageModel(Package):
    configs: PackageConfigs
    type: Literal["component"] = "component"
    name: Literal[
        "EnvironmentSecretsStore"
    ] = "EnvironmentSecretsStore"
