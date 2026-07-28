import importlib
import os
import sys
import types
from pathlib import Path

import pytest
from cryptography.fernet import Fernet


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
            "encryptedSecrets": context.encrypted_secrets,
            "message": context.message,
        }

    response_module.build_response = fake_build_response
    sys.modules[
        "novavision.package.utils.response"
    ] = response_module


_prepare_imports()

environment_utils = importlib.import_module(
    "novavision.package.utils.environment"
)
crypto_utils = importlib.import_module(
    "novavision.package.utils.crypto"
)
executor_module = importlib.import_module(
    "novavision.package.executors.EnvironmentSecretsStore"
)
EnvironmentSecretsStore = executor_module.EnvironmentSecretsStore


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


def test_single_executor_and_run_method():
    executors_dir = SRC_DIR / "executors"
    assert (executors_dir / "EnvironmentSecretsStore.py").is_file()
    assert callable(getattr(EnvironmentSecretsStore, "run", None))


def test_parse_variable_names():
    assert environment_utils.parse_variable_names(
        '["ACCESS_TOKEN", "DATABASE_PASSWORD"]'
    ) == ["ACCESS_TOKEN", "DATABASE_PASSWORD"]


@pytest.mark.parametrize(
    "invalid_value",
    [
        "not-json",
        "{}",
        "[]",
        '[""]',
        "[123]",
        '["API_KEY", "api_key"]',
        '["NOVAVISION_SECRET_TRANSPORT_KEY"]',
    ],
)
def test_rejects_invalid_variable_names(invalid_value):
    with pytest.raises(ValueError):
        environment_utils.parse_variable_names(invalid_value)


def test_reads_secrets_and_transport_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ACCESS_TOKEN", "private-value")
    monkeypatch.setenv(
        "NOVAVISION_SECRET_TRANSPORT_KEY",
        key,
    )

    assert environment_utils.read_secrets(
        ["ACCESS_TOKEN"]
    ) == {"ACCESS_TOKEN": "private-value"}
    assert environment_utils.read_transport_key() == key


def test_encrypts_without_exposing_plaintext():
    key = Fernet.generate_key().decode()
    token = crypto_utils.encrypt_secret_values(
        {"ACCESS_TOKEN": "do-not-expose-me"},
        key,
    )

    assert "do-not-expose-me" not in token
    plaintext = Fernet(key.encode()).decrypt(
        token.encode()
    ).decode()
    assert "do-not-expose-me" in plaintext


def test_executor_returns_ciphertext_and_safe_message(
    monkeypatch,
    capsys,
):
    key = Fernet.generate_key().decode()
    request = FakeRequest('["ACCESS_TOKEN"]')
    executor = EnvironmentSecretsStore(
        request=request,
        bootstrap={},
    )

    monkeypatch.setattr(
        executor_module,
        "read_secrets",
        lambda names: {"ACCESS_TOKEN": "do-not-expose-me"},
    )
    monkeypatch.setattr(
        executor_module,
        "read_transport_key",
        lambda: key,
    )

    response = executor.run()
    captured = capsys.readouterr()

    assert "do-not-expose-me" not in str(response)
    assert "do-not-expose-me" not in captured.out
    assert "do-not-expose-me" not in captured.err
    assert response["message"].startswith("1 secret value")
    assert Fernet(key.encode()).decrypt(
        response["encryptedSecrets"].encode()
    )
