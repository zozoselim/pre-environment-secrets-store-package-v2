import os

import pytest

os.environ.setdefault("NAME", "OpenCV/test")

from components.EnvironmentSecretsStore.src.executors.EnvironmentSecretsStore import (
    EnvironmentSecretsStore,
)
from components.EnvironmentSecretsStore.src.utils.response import (
    create_secret_outputs,
)


def make_context(variable_names):
    context = object.__new__(EnvironmentSecretsStore)
    context.variable_names = variable_names
    return context


def test_parse_variable_names_from_json_string():
    assert EnvironmentSecretsStore.parse_variable_names(
        '["MY_SECRET_A", "MY_SECRET_B"]'
    ) == ["MY_SECRET_A", "MY_SECRET_B"]


def test_reads_and_lowercases_requested_variables(monkeypatch):
    monkeypatch.setenv("MY_SECRET_A", "alpha")
    monkeypatch.setenv("MY_SECRET_B", "beta")

    context = make_context(["MY_SECRET_A", "MY_SECRET_B"])

    assert context.read_secrets() == {
        "my_secret_a": "alpha",
        "my_secret_b": "beta",
    }


def test_creates_one_separate_output_per_secret():
    outputs = create_secret_outputs(
        {
            "my_secret_a": "alpha",
            "my_secret_b": "beta",
        }
    )

    assert set(outputs) == {"my_secret_a", "my_secret_b"}
    assert outputs["my_secret_a"].name == "my_secret_a"
    assert outputs["my_secret_a"].value == "alpha"
    assert outputs["my_secret_a"].type == "string"


def test_missing_variable_error_does_not_contain_secret_values(monkeypatch):
    monkeypatch.setenv("PRESENT_SECRET", "do-not-print-me")
    monkeypatch.delenv("MISSING_SECRET", raising=False)

    context = make_context(["PRESENT_SECRET", "MISSING_SECRET"])

    with pytest.raises(RuntimeError) as error:
        context.read_secrets()

    message = str(error.value)
    assert "MISSING_SECRET" in message
    assert "do-not-print-me" not in message
