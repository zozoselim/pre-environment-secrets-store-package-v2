import json
import re
from pathlib import Path
from typing import Dict, List, Literal, Union

from pydantic import Field, create_model, validator

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
_SCHEMA_NAMES_PATH = (
    Path(__file__).resolve().parents[2]
    / "resources"
    / "secret_outputs.json"
)


def _validate_names(variable_names: List[str]) -> List[str]:
    if not isinstance(variable_names, list) or not variable_names:
        raise ValueError("At least one environment variable name is required.")

    cleaned_names: List[str] = []
    seen_names = set()
    seen_output_names = set()

    for variable_name in variable_names:
        if not isinstance(variable_name, str):
            raise ValueError("Environment variable names must be strings.")

        cleaned_name = variable_name.strip()
        if not _ENV_NAME_PATTERN.fullmatch(cleaned_name):
            raise ValueError(
                f"Invalid environment variable name: {cleaned_name!r}."
            )

        if cleaned_name in seen_names:
            raise ValueError(
                f"Duplicate environment variable name: {cleaned_name}."
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

    return cleaned_names


def load_declared_secret_names() -> List[str]:
    """Load non-secret variable names used to generate visual output ports."""

    try:
        raw_names = json.loads(_SCHEMA_NAMES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(
            f"Output schema file was not found: {_SCHEMA_NAMES_PATH}"
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "resources/secret_outputs.json must contain a valid JSON list."
        ) from error

    return _validate_names(raw_names)


DECLARED_SECRET_NAMES = load_declared_secret_names()
DECLARED_OUTPUT_NAMES = [name.lower() for name in DECLARED_SECRET_NAMES]
DEFAULT_VARIABLES_JSON = json.dumps(DECLARED_SECRET_NAMES)


class EmptyInputs(Inputs):
    """Environment Secrets Store does not require workflow input."""

    pass


class VariablesStoringSecrets(Config):
    """JSON list containing names of environment variables to retrieve."""

    name: Literal[
        "variables_storing_secrets"
    ] = "variables_storing_secrets"

    value: str = Field(
        default=DEFAULT_VARIABLES_JSON,
        min_length=2,
    )

    type: Literal["string"] = "string"
    field: Literal["textInput"] = "textInput"

    placeHolder: Literal[
        '["OPENAI_API_KEY", "DATABASE_PASSWORD"]'
    ] = '["OPENAI_API_KEY", "DATABASE_PASSWORD"]'

    @validator("value")
    def validate_variable_names(cls, value: str) -> str:
        """Validate the UI list and keep it aligned with generated ports."""

        try:
            variable_names = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Value must be a valid JSON list of environment variable names."
            ) from error

        cleaned_names = _validate_names(variable_names)

        if cleaned_names != DECLARED_SECRET_NAMES:
            raise ValueError(
                "Configured secret names must match the generated output schema: "
                f"{DECLARED_SECRET_NAMES}. Update resources/secret_outputs.json, "
                "export the package schema again, and redeploy."
            )

        return json.dumps(cleaned_names)

    class Config:
        title = "Variables Storing Secrets"
        json_schema_extra = {
            "shortDescription": (
                "JSON list of environment variable names. Visual output ports "
                "are generated from resources/secret_outputs.json."
            )
        }


class SecretOutput(Output):
    """One requested secret exposed as its own string output."""

    name: str
    value: str
    type: Literal["string"] = "string"

    class Config:
        title = "Secret"


_output_fields = {
    output_name: (SecretOutput, ...)
    for output_name in DECLARED_OUTPUT_NAMES
}

PackageOutputs = create_model(
    "PackageOutputs",
    __base__=Outputs,
    **_output_fields,
)


class EnvironmentSecretsStoreConfigs(Configs):
    variables_storing_secrets: VariablesStoringSecrets


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
