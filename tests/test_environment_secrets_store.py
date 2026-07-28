import base64
import importlib
import os
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
TEST_KEY = base64.urlsafe_b64encode(
    b"0" * 32
).decode("utf-8")


def _register_package(
    name: str,
    path: Path,
) -> None:
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
        def __init__(self):
            pass

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
            "secrets": context.secure_result,
        }

    response_module.build_response = fake_build_response
    sys.modules[
        "novavision.package.utils.response"
    ] = response_module


_prepare_imports()


environment_utils = importlib.import_module(
    "novavision.package.utils.environment"
)
security_utils = importlib.import_module(
    "novavision.package.utils.security"
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
    assert environment_utils.parse_variable_names(
        '["MY_SECRET_A", "MY_SECRET_B"]'
    ) == [
        "MY_SECRET_A",
        "MY_SECRET_B",
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


def test_encrypt_and_decrypt_round_trip():
    source = {
        "access_token": "secret-value",
        "database_password": "another-secret",
    }

    encrypted = security_utils.encrypt_secrets(
        secrets=source,
        encryption_key=TEST_KEY,
    )

    assert "secret-value" not in encrypted
    assert "another-secret" not in encrypted

    assert security_utils.decrypt_secrets(
        encrypted_payload=encrypted,
        encryption_key=TEST_KEY,
    ) == source


def test_resolve_secure_secrets_never_returns_plaintext(
    monkeypatch,
):
    monkeypatch.setenv(
        "ACCESS_TOKEN",
        "do-not-expose-me",
    )
    monkeypatch.setenv(
        security_utils.ENCRYPTION_KEY_VARIABLE,
        TEST_KEY,
    )

    result = security_utils.resolve_secure_secrets(
        ["ACCESS_TOKEN"]
    )

    assert result["message"] == (
        security_utils.SUCCESS_MESSAGE
    )
    assert result["encryption"] == "fernet"
    assert "do-not-expose-me" not in str(result)

    decrypted = security_utils.decrypt_secrets(
        encrypted_payload=result["encrypted_payload"],
        encryption_key=TEST_KEY,
    )

    assert decrypted == {
        "access_token": "do-not-expose-me",
    }


def test_missing_encryption_key_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "ACCESS_TOKEN",
        "do-not-expose-me",
    )
    monkeypatch.delenv(
        security_utils.ENCRYPTION_KEY_VARIABLE,
        raising=False,
    )

    with pytest.raises(RuntimeError) as error:
        security_utils.resolve_secure_secrets(
            ["ACCESS_TOKEN"]
        )

    assert (
        security_utils.ENCRYPTION_KEY_VARIABLE
        in str(error.value)
    )
    assert "do-not-expose-me" not in str(error.value)


def test_executor_run_returns_encrypted_bundle(
    monkeypatch,
):
    request = FakeRequest(
        '["ACCESS_TOKEN"]'
    )
    executor = EnvironmentSecretsStore(
        request=request,
        bootstrap={},
    )

    encrypted_result = {
        "message": security_utils.SUCCESS_MESSAGE,
        "encrypted_payload": "encrypted-token",
        "encryption": "fernet",
    }

    monkeypatch.setattr(
        executor_module,
        "resolve_secure_secrets",
        lambda variable_names: encrypted_result,
    )

    response = executor.run()

    assert executor.secure_result == encrypted_result
    assert response == {
        "secrets": encrypted_result,
    }


def test_executor_run_does_not_expose_plaintext_in_logs(
    monkeypatch,
    capsys,
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
        "resolve_secure_secrets",
        lambda variable_names: {
            "message": security_utils.SUCCESS_MESSAGE,
            "encrypted_payload": "encrypted-token",
            "encryption": "fernet",
        },
    )

    executor.run()
    captured = capsys.readouterr()

    assert "ACCESS_TOKEN" not in captured.out
    assert "ACCESS_TOKEN" not in captured.err
