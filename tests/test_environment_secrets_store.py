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

    environment_module = types.ModuleType(
        "sdks.novavision.src.base.environment"
    )

    class FakeEnvironment:
        @staticmethod
        def get_environment_variable(variable):
            return os.getenv(variable)

    environment_module.Environment = FakeEnvironment
    sys.modules[
        "sdks.novavision.src.base.environment"
    ] = environment_module

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
        return {
            "secretReferences": (
                context.secret_references
            )
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


def test_only_one_executor_file_exists():
    executors_dir = SRC_DIR / "executors"

    assert (
        executors_dir / "EnvironmentSecretsStore.py"
    ).is_file()
    assert not (executors_dir / "Str.py").exists()
    assert not (executors_dir / "List.py").exists()


def test_executor_has_run_method():
    assert callable(
        getattr(
            EnvironmentSecretsStore,
            "run",
            None,
        )
    )


def test_parse_variable_names():
    assert environment_utils.parse_variable_names(
        '["ACCESS_TOKEN", "DATABASE_PASSWORD"]'
    ) == [
        "ACCESS_TOKEN",
        "DATABASE_PASSWORD",
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
    ],
)
def test_rejects_invalid_names(invalid_value):
    with pytest.raises(ValueError):
        environment_utils.parse_variable_names(
            invalid_value
        )


def test_validate_access_returns_references_only(
    monkeypatch,
):
    monkeypatch.setenv(
        "ACCESS_TOKEN",
        "do-not-expose-me",
    )

    result = environment_utils.validate_secret_access(
        ["ACCESS_TOKEN"]
    )

    assert result == ["ACCESS_TOKEN"]
    assert "do-not-expose-me" not in str(result)


def test_missing_secret_fails(monkeypatch):
    monkeypatch.delenv(
        "MISSING_SECRET",
        raising=False,
    )

    with pytest.raises(RuntimeError) as error:
        environment_utils.validate_secret_access(
            ["MISSING_SECRET"]
        )

    assert "MISSING_SECRET" in str(error.value)


def test_executor_returns_only_references(
    monkeypatch,
):
    request = FakeRequest(
        '["ACCESS_TOKEN"]'
    )
    executor = EnvironmentSecretsStore(
        request=request,
        bootstrap={},
    )

    monkeypatch.setattr(
        executor_module,
        "validate_secret_access",
        lambda names: ["ACCESS_TOKEN"],
    )

    response = executor.run()

    assert executor.secret_references == [
        "ACCESS_TOKEN"
    ]
    assert response == {
        "secretReferences": [
            "ACCESS_TOKEN"
        ]
    }
    assert "do-not-expose-me" not in str(response)
