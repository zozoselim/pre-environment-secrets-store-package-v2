import importlib
import os
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def _register_package(name: str, path: Path) -> None:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


def _prepare_imports() -> None:
    """
    Create the package hierarchy required by the executor.

    NovaVision SDK is supplied by the NovaVision runtime. Unit tests use
    minimal fake modules so executor logic can also be tested locally.
    """

    _register_package("novavision", SRC_DIR)
    _register_package("novavision.package", SRC_DIR)
    _register_package(
        "novavision.package.executors",
        SRC_DIR / "executors",
    )
    _register_package(
        "novavision.package.models",
        SRC_DIR / "models",
    )
    _register_package(
        "novavision.package.utils",
        SRC_DIR / "utils",
    )

    for module_name in [
        "sdks",
        "sdks.novavision",
        "sdks.novavision.src",
        "sdks.novavision.src.base",
    ]:
        module = types.ModuleType(module_name)
        module.__path__ = []
        sys.modules[module_name] = module

    component_module = types.ModuleType(
        "sdks.novavision.src.base.component"
    )

    class FakeComponent:
        def __init__(self, request=None, bootstrap=None):
            self.request = request
            self.bootstrap_data = bootstrap

    component_module.Component = FakeComponent

    sys.modules[
        "sdks.novavision.src.base.component"
    ] = component_module

    model_module = types.ModuleType(
        "novavision.package.models.PackageModel"
    )

    class FakePackageModel:
        def __init__(self, **data):
            self.data = data

    model_module.PackageModel = FakePackageModel

    sys.modules[
        "novavision.package.models.PackageModel"
    ] = model_module

    response_module = types.ModuleType(
        "novavision.package.utils.response"
    )

    def fake_build_response(context):
        return {"secrets": context.secrets}

    response_module.build_response = fake_build_response

    sys.modules[
        "novavision.package.utils.response"
    ] = response_module


_prepare_imports()

executor_module = importlib.import_module(
    "novavision.package.executors.EnvironmentSecretsStore"
)

EnvironmentSecretsStore = (
    executor_module.EnvironmentSecretsStore
)


def make_context(variable_names, output_type="List"):
    context = object.__new__(EnvironmentSecretsStore)
    context.variable_names = variable_names
    context.output_type = output_type
    context.secrets = None
    return context


def test_single_executor_file_only():
    executors_dir = SRC_DIR / "executors"

    assert (
        executors_dir / "EnvironmentSecretsStore.py"
    ).is_file()
    assert not (executors_dir / "Str.py").exists()
    assert not (executors_dir / "List.py").exists()


def test_executor_contains_run_method():
    assert callable(
        getattr(EnvironmentSecretsStore, "run", None)
    )


def test_parse_variable_names_from_json_string():
    result = EnvironmentSecretsStore.parse_variable_names(
        '["MY_SECRET_A", "MY_SECRET_B"]'
    )

    assert result == [
        "MY_SECRET_A",
        "MY_SECRET_B",
    ]


def test_parse_variable_names_from_list():
    result = EnvironmentSecretsStore.parse_variable_names(
        ["MY_SECRET_A"]
    )

    assert result == ["MY_SECRET_A"]


@pytest.mark.parametrize(
    "invalid_value",
    [
        "not-json",
        "{}",
        "[]",
        '[""]',
        "[123]",
        '["API_KEY", "api_key"]',
    ],
)
def test_rejects_invalid_variable_names(invalid_value):
    with pytest.raises(ValueError):
        EnvironmentSecretsStore.parse_variable_names(
            invalid_value
        )


def test_reads_requested_variables_in_order(
    monkeypatch,
):
    monkeypatch.setenv("MY_SECRET_A", "alpha")
    monkeypatch.setenv("MY_SECRET_B", "beta")

    context = make_context(
        ["MY_SECRET_A", "MY_SECRET_B"]
    )

    assert context.read_secret_values() == [
        "alpha",
        "beta",
    ]


def test_missing_variable_error_does_not_expose_secret(
    monkeypatch,
):
    monkeypatch.setenv(
        "PRESENT_SECRET",
        "do-not-print-me",
    )
    monkeypatch.delenv(
        "MISSING_SECRET",
        raising=False,
    )

    context = make_context(
        [
            "PRESENT_SECRET",
            "MISSING_SECRET",
        ]
    )

    with pytest.raises(RuntimeError) as error:
        context.read_secret_values()

    message = str(error.value)

    assert "MISSING_SECRET" in message
    assert "do-not-print-me" not in message


def test_loads_custom_dotenv_path(
    tmp_path,
    monkeypatch,
):
    dotenv_path = tmp_path / ".env"

    dotenv_path.write_text(
        "ENV_SECRET_TEST=novavision-test-123\n",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "ENVIRONMENT_SECRETS_STORE_DOTENV_PATH",
        str(dotenv_path),
    )
    monkeypatch.delenv(
        "ENV_SECRET_TEST",
        raising=False,
    )

    EnvironmentSecretsStore.load_runtime_environment()

    assert (
        os.getenv("ENV_SECRET_TEST")
        == "novavision-test-123"
    )


def test_run_returns_string_in_str_mode(
    monkeypatch,
):
    context = make_context(
        ["ENV_SECRET_TEST"],
        output_type="Str",
    )
    call_order = []

    monkeypatch.setattr(
        EnvironmentSecretsStore,
        "load_runtime_environment",
        classmethod(
            lambda cls: call_order.append("load")
        ),
    )

    def fake_read_secret_values():
        call_order.append("read")
        return ["secret-value"]

    monkeypatch.setattr(
        context,
        "read_secret_values",
        fake_read_secret_values,
    )

    response = context.run()

    assert call_order == ["load", "read"]
    assert context.secrets == "secret-value"
    assert response == {
        "secrets": "secret-value",
    }


def test_run_returns_list_in_list_mode(
    monkeypatch,
):
    context = make_context(
        ["MY_SECRET_A", "MY_SECRET_B"],
        output_type="List",
    )

    monkeypatch.setattr(
        EnvironmentSecretsStore,
        "load_runtime_environment",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        context,
        "read_secret_values",
        lambda: ["alpha", "beta"],
    )

    response = context.run()

    assert context.secrets == ["alpha", "beta"]
    assert response == {
        "secrets": ["alpha", "beta"],
    }


def test_str_mode_rejects_multiple_values(
    monkeypatch,
):
    context = make_context(
        ["MY_SECRET_A", "MY_SECRET_B"],
        output_type="Str",
    )

    monkeypatch.setattr(
        EnvironmentSecretsStore,
        "load_runtime_environment",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        context,
        "read_secret_values",
        lambda: ["alpha", "beta"],
    )

    with pytest.raises(ValueError) as error:
        context.run()

    assert "exactly one" in str(error.value)


def test_run_rejects_unknown_output_type(
    monkeypatch,
):
    context = make_context(
        ["MY_SECRET_A"],
        output_type="Unknown",
    )

    monkeypatch.setattr(
        EnvironmentSecretsStore,
        "load_runtime_environment",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        context,
        "read_secret_values",
        lambda: ["alpha"],
    )

    with pytest.raises(ValueError) as error:
        context.run()

    assert "Str or List" in str(error.value)
