import json
import os

import pytest

os.environ.setdefault("NAME", "OpenCV/test")

from components.EnvironmentSecretsStore.src.executors.EnvironmentSecretsStore import (
    EnvironmentSecretsStore,
)
from components.EnvironmentSecretsStore.src.models.PackageModel import (
    DECLARED_OUTPUT_NAMES,
    DECLARED_SECRET_NAMES,
    PackageOutputs,
    SecretOutput,
)


def make_context(variable_names):
    context = object.__new__(EnvironmentSecretsStore)
    context.variable_names = variable_names
    return context


def test_generated_output_schema_matches_resource_file():
    assert DECLARED_SECRET_NAMES == ["ENV_SECRET_TEST"]
    assert DECLARED_OUTPUT_NAMES == ["env_secret_test"]

    output = PackageOutputs(
        env_secret_test=SecretOutput(
            name="env_secret_test",
            value="masked-test-value",
        )
    )
    assert output.env_secret_test.name == "env_secret_test"


def test_parse_variable_names_from_json_string():
    assert EnvironmentSecretsStore.parse_variable_names(
        '["ENV_SECRET_TEST"]'
    ) == ["ENV_SECRET_TEST"]


def test_rejects_config_that_does_not_match_generated_ports():
    with pytest.raises(ValueError):
        EnvironmentSecretsStore.validate_declared_outputs(["OTHER_SECRET"])


def test_reads_and_lowercases_requested_variables(monkeypatch):
    monkeypatch.setenv("ENV_SECRET_TEST", "alpha")
    context = make_context(["ENV_SECRET_TEST"])

    assert context.read_secrets() == {
        "env_secret_test": "alpha",
    }


def test_missing_variable_error_does_not_contain_secret_values(monkeypatch):
    monkeypatch.delenv("ENV_SECRET_TEST", raising=False)
    context = make_context(["ENV_SECRET_TEST"])

    with pytest.raises(RuntimeError) as error:
        context.read_secrets()

    message = str(error.value)
    assert "ENV_SECRET_TEST" in message
