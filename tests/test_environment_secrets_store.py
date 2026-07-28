import importlib
import os
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def _register_package(
    name: str,
    path: Path,
) -> None:
    """Register a minimal Python package for local tests."""

    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


def _prepare_imports() -> None:
    """
    Create the package hierarchy required by the executor.

    NovaVision SDK exists inside the runtime container. Local tests use
    minimal fake modules that reproduce only the required SDK behavior.
    """

    _register_package(
        "novavision",
        SRC_DIR,
    )

    _register_package(
        "novavision.package",
        SRC_DIR,
    )

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

    # ------------------------------------------------------------------
    # Fake NovaVision Environment
    # ------------------------------------------------------------------

    environment_module = types.ModuleType(
        "sdks.novavision.src.base.environment"
    )

    class FakeEnvironment:
        """
        Local replacement for NovaVision's Environment class.

        The real SDK implementation was verified inside the container:

        @staticmethod
        def get_environment_variable(variable):
            return os.getenv(variable)
        """

        @staticmethod
        def get_environment_variable(variable):
            return os.getenv(variable)

    environment_module.Environment = FakeEnvironment

    sys.modules[
        "sdks.novavision.src.base.environment"
    ] = environment_module

    # ------------------------------------------------------------------
    # Fake NovaVision Component
    # ------------------------------------------------------------------

    component_module = types.ModuleType(
        "sdks.novavision.src.base.component"
    )

    class FakeComponent:
        def __init__(
            self,
            request=None,
            bootstrap=None,
        ):
            self.request = request
            self.bootstrap_data = bootstrap

    component_module.Component = FakeComponent

    sys.modules[
        "sdks.novavision.src.base.component"
    ] = component_module

    # ------------------------------------------------------------------
    # Fake PackageModel
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Fake response builder
    # ------------------------------------------------------------------

    response_module = types.ModuleType(
        "novavision.package.utils.response"
    )

    def fake_build_response(context):
        return {
            "secrets": context.secrets,
        }

    response_module.build_response = fake_build_response

    sys.modules[
        "novavision.package.utils.response"
    ] = response_module


_prepare_imports()


environment_utils = importlib.import_module(
    "novavision.package.utils.environment"
)

executor_module = importlib.import_module(
    "novavision.package.executors.EnvironmentSecretsStore"
)

EnvironmentSecretsStore = (
    executor_module.EnvironmentSecretsStore
)


class FakeRequest:
    """Minimal request object used by executor tests."""

    def __init__(self, variable_names):
        self.data = {
            "type": "component",
            "name": "EnvironmentSecretsStore",
            "configs": {},
        }

        self.model = None

        self.params = {
            "variables_storing_secrets": variable_names,
        }

    def get_param(self, name):
        return self.params[name]


def test_single_executor_file_only():
    executors_dir = SRC_DIR / "executors"

    assert (
        executors_dir / "EnvironmentSecretsStore.py"
    ).is_file()

    assert not (
        executors_dir / "Str.py"
    ).exists()

    assert not (
        executors_dir / "List.py"
    ).exists()


def test_executor_contains_run_method():
    assert callable(
        getattr(
            EnvironmentSecretsStore,
            "run",
            None,
        )
    )


def test_parse_variable_names_from_json_string():
    result = environment_utils.parse_variable_names(
        '["MY_SECRET_A", "MY_SECRET_B"]'
    )

    assert result == [
        "MY_SECRET_A",
        "MY_SECRET_B",
    ]


def test_parse_variable_names_from_list():
    result = environment_utils.parse_variable_names(
        [
            "MY_SECRET_A",
        ]
    )

    assert result == [
        "MY_SECRET_A",
    ]


@pytest.mark.parametrize(
    "invalid_value",
    [
        "not-json",
        "{}",
        "[]",
        '[""]',
        "[123]",
        '["API_KEY", "api_key"]',
        '["API KEY"]',
        '["1INVALID_NAME"]',
    ],
)
def test_rejects_invalid_variable_names(
    invalid_value,
):
    with pytest.raises(ValueError):
        environment_utils.parse_variable_names(
            invalid_value
        )


def test_parse_variable_names_trims_whitespace():
    result = environment_utils.parse_variable_names(
        '["  MY_SECRET_A  "]'
    )

    assert result == [
        "MY_SECRET_A",
    ]


def test_reads_requested_variables_through_sdk(
    monkeypatch,
):
    monkeypatch.setenv(
        "MY_SECRET_A",
        "alpha",
    )

    monkeypatch.setenv(
        "MY_SECRET_B",
        "beta",
    )

    result = environment_utils.read_secrets(
        [
            "MY_SECRET_A",
            "MY_SECRET_B",
        ]
    )

    assert result == {
        "my_secret_a": "alpha",
        "my_secret_b": "beta",
    }


def test_read_secrets_uses_environment_sdk(
    monkeypatch,
):
    calls = []

    def fake_get_environment_variable(
        variable,
    ):
        calls.append(variable)

        values = {
            "MY_SECRET_A": "alpha",
            "MY_SECRET_B": "beta",
        }

        return values.get(variable)

    monkeypatch.setattr(
        environment_utils.Environment,
        "get_environment_variable",
        staticmethod(
            fake_get_environment_variable
        ),
    )

    result = environment_utils.read_secrets(
        [
            "MY_SECRET_A",
            "MY_SECRET_B",
        ]
    )

    assert calls == [
        "MY_SECRET_A",
        "MY_SECRET_B",
    ]

    assert result == {
        "my_secret_a": "alpha",
        "my_secret_b": "beta",
    }


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

    with pytest.raises(RuntimeError) as error:
        environment_utils.read_secrets(
            [
                "PRESENT_SECRET",
                "MISSING_SECRET",
            ]
        )

    message = str(error.value)

    assert "MISSING_SECRET" in message
    assert "do-not-print-me" not in message


def test_executor_initializes_request_model():
    request = FakeRequest(
        '["MY_SECRET_A"]'
    )

    executor = EnvironmentSecretsStore(
        request=request,
        bootstrap={},
    )

    assert request.model is not None

    assert executor.variable_names == [
        "MY_SECRET_A",
    ]

    assert executor.secrets == {}


def test_executor_run_reads_secrets_and_builds_response(
    monkeypatch,
):
    request = FakeRequest(
        '["MY_SECRET_A", "MY_SECRET_B"]'
    )

    executor = EnvironmentSecretsStore(
        request=request,
        bootstrap={},
    )

    calls = []

    def fake_read_secrets(variable_names):
        calls.append(
            list(variable_names)
        )

        return {
            "my_secret_a": "alpha",
            "my_secret_b": "beta",
        }

    monkeypatch.setattr(
        executor_module,
        "read_secrets",
        fake_read_secrets,
    )

    response = executor.run()

    assert calls == [
        [
            "MY_SECRET_A",
            "MY_SECRET_B",
        ]
    ]

    assert executor.secrets == {
        "my_secret_a": "alpha",
        "my_secret_b": "beta",
    }

    assert response == {
        "secrets": {
            "my_secret_a": "alpha",
            "my_secret_b": "beta",
        }
    }


def test_executor_run_does_not_expose_secrets_in_logs(
    monkeypatch,
    capsys,
):
    request = FakeRequest(
        '["MY_SECRET_A"]'
    )

    executor = EnvironmentSecretsStore(
        request=request,
        bootstrap={},
    )

    monkeypatch.setattr(
        executor_module,
        "read_secrets",
        lambda variable_names: {
            "my_secret_a": "do-not-print-me",
        },
    )

    executor.run()

    captured = capsys.readouterr()

    assert "do-not-print-me" not in captured.out
    assert "do-not-print-me" not in captured.err