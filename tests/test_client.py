import importlib.util
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = PROJECT_ROOT / "apps" / "client.py"

spec = importlib.util.spec_from_file_location(
    "environment_secrets_client",
    CLIENT_PATH,
)

client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class FakePubSub:
    def __init__(self, messages):
        self.messages = list(messages)
        self.closed = False

    def get_message(self, **kwargs):
        if self.messages:
            return self.messages.pop(0)

        return None

    def close(self):
        self.closed = True


class FakeRuntimeClient:
    def __init__(
        self,
        pubsub,
        subscriber_count=1,
    ):
        self.pubsub = pubsub
        self.subscriber_count = subscriber_count
        self.published_key = None
        self.published_message = None

    def initialize_pubsub_client(self, channel):
        assert channel == "response"
        return self.pubsub

    def _publish(self, key, message):
        self.published_key = key
        self.published_message = message
        return self.subscriber_count


def test_parse_variable_names():
    result = client.parse_variable_names(
        '["ENV_SECRET_TEST", "API_KEY"]'
    )

    assert result == [
        "ENV_SECRET_TEST",
        "API_KEY",
    ]


def test_parse_variable_names_rejects_invalid_json():
    with pytest.raises(ValueError) as error:
        client.parse_variable_names("invalid-json")

    assert "JSON" in str(error.value)


def test_build_request_matches_runtime_schema():
    payload = client.build_request(
        variable_names=["ENV_SECRET_TEST"],
        component_uid="Kba9Cw",
        flow_uid="flow-test-1",
    )

    assert payload["status"] == "success"
    assert payload["api"] == "True"
    assert payload["debug"] == "False"
    assert payload["uID"] == "Kba9Cw"
    assert payload["flowUID"] == "flow-test-1"

    selected_executor = payload["configs"]["executor"]["value"]
    assert selected_executor["name"] == "EnvironmentSecretsStore"
    assert selected_executor["value"]["name"] == (
        "EnvironmentSecretsStore"
    )

    output_type = (
        selected_executor["value"]["configs"]
        ["output_type"]["value"]
    )
    assert output_type["name"] == "Str"
    assert output_type["value"] == "Str"

    config_value = (
        selected_executor["value"]
        ["configs"]["variables_storing_secrets"]["value"]
    )

    assert json.loads(config_value) == [
        "ENV_SECRET_TEST"
    ]


def test_build_request_supports_list_output():
    payload = client.build_request(
        variable_names=["SECRET_A", "SECRET_B"],
        component_uid="Kba9Cw",
        flow_uid="flow-list-1",
        output_type="List",
    )

    selected_executor = payload["configs"]["executor"]["value"]
    assert selected_executor["name"] == "EnvironmentSecretsStore"

    output_type = (
        selected_executor["value"]["configs"]
        ["output_type"]["value"]
    )
    assert output_type["name"] == "List"
    assert output_type["value"] == "List"


def test_build_request_rejects_multiple_names_for_str():
    with pytest.raises(ValueError) as error:
        client.build_request(
            variable_names=["SECRET_A", "SECRET_B"],
            component_uid="Kba9Cw",
            flow_uid="flow-str-1",
            output_type="Str",
        )

    assert "exactly one" in str(error.value)


def test_parse_output_type_accepts_string_alias():
    assert client.parse_output_type("string") == "Str"
    assert client.parse_output_type("list") == "List"


def test_masked_response_hides_secret_values():
    original_response = {
        "configs": {
            "executor": {
                "value": {
                    "value": {
                        "outputs": {
                            "secrets": {
                                "name": "secrets",
                                "type": "object",
                                "value": {
                                    "env_secret_test": (
                                        "novavision-test-123"
                                    ),
                                    "api_key": "fake-api-key",
                                },
                            }
                        }
                    }
                }
            }
        }
    }

    masked = client.masked_response(
        original_response,
        [
            "ENV_SECRET_TEST",
            "API_KEY",
        ],
    )

    masked_values = (
        masked["configs"]["executor"]["value"]["value"]
        ["outputs"]["secrets"]["value"]
    )

    assert masked_values == {
        "env_secret_test": client.REDACTED_VALUE,
        "api_key": client.REDACTED_VALUE,
    }

    original_values = (
        original_response["configs"]["executor"]["value"]
        ["value"]["outputs"]["secrets"]["value"]
    )

    assert original_values["env_secret_test"] == (
        "novavision-test-123"
    )


def test_masked_response_hides_string_output():
    response = {
        "outputs": {
            "secrets": {
                "name": "secrets",
                "type": "string",
                "value": "novavision-test-123",
            }
        }
    }

    masked = client.masked_response(
        response,
        ["ENV_SECRET_TEST"],
    )

    assert masked["outputs"]["secrets"]["value"] == (
        client.REDACTED_VALUE
    )


def test_masked_response_hides_list_output():
    response = {
        "outputs": {
            "secrets": {
                "name": "secrets",
                "type": "object",
                "value": ["secret-a", "secret-b"],
            }
        }
    }

    masked = client.masked_response(
        response,
        ["SECRET_A", "SECRET_B"],
    )

    assert masked["outputs"]["secrets"]["value"] == [
        client.REDACTED_VALUE,
        client.REDACTED_VALUE,
    ]


def test_run_runtime_request_publishes_and_receives(
    monkeypatch,
):
    payload = client.build_request(
        variable_names=["ENV_SECRET_TEST"],
        component_uid="Kba9Cw",
        flow_uid="flow-test-1",
    )

    response_data = {
        "status": "success",
        "uID": "Kba9Cw",
        "flowUID": "flow-test-1",
    }

    pubsub = FakePubSub(
        [
            {
                "type": "subscribe",
                "data": 1,
            },
            {
                "type": "message",
                "data": json.dumps(response_data),
            },
        ]
    )

    runtime_client = FakeRuntimeClient(pubsub)

    monkeypatch.setattr(
        client,
        "create_runtime_client",
        lambda: runtime_client,
    )

    result = client.run_runtime_request(
        payload=payload,
        component_uid="Kba9Cw",
        timeout_seconds=1,
    )

    assert result == response_data
    assert runtime_client.published_key == "Kba9Cw"
    assert json.loads(
        runtime_client.published_message
    ) == payload
    assert pubsub.closed is True


def test_run_runtime_request_requires_subscriber(
    monkeypatch,
):
    pubsub = FakePubSub(
        [
            {
                "type": "subscribe",
                "data": 1,
            }
        ]
    )

    runtime_client = FakeRuntimeClient(
        pubsub=pubsub,
        subscriber_count=0,
    )

    monkeypatch.setattr(
        client,
        "create_runtime_client",
        lambda: runtime_client,
    )

    payload = client.build_request(
        variable_names=["ENV_SECRET_TEST"],
        component_uid="Kba9Cw",
        flow_uid="flow-test-1",
    )

    with pytest.raises(RuntimeError) as error:
        client.run_runtime_request(
            payload=payload,
            component_uid="Kba9Cw",
            timeout_seconds=1,
        )

    assert "No NovaVision executor" in str(
        error.value
    )
    assert pubsub.closed is True


def test_main_success_masks_output(
    monkeypatch,
    capsys,
):
    response_data = {
        "status": "success",
        "uID": "Kba9Cw",
        "flowUID": "flow-test-1",
        "configs": {
            "executor": {
                "value": {
                    "value": {
                        "outputs": {
                            "secrets": {
                                "name": "secrets",
                                "value": "novavision-test-123",
                            }
                        }
                    }
                }
            }
        },
    }

    monkeypatch.setenv(
        "ENV_SECRET_NAMES",
        '["ENV_SECRET_TEST"]',
    )

    monkeypatch.setenv(
        "NOVAVISION_COMPONENT_UID",
        "Kba9Cw",
    )

    monkeypatch.setattr(
        client,
        "run_runtime_request",
        lambda **kwargs: response_data,
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 0
    assert "[SUCCESS]" in output
    assert client.REDACTED_VALUE in output
    assert "novavision-test-123" not in output


def test_main_handles_timeout(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        client,
        "run_runtime_request",
        lambda **kwargs: (
            _raise_timeout()
        ),
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 3
    assert "[FAILED]" in output
    assert "timed out" in output


def _raise_timeout():
    raise TimeoutError(
        "NovaVision runtime response timed out."
    )


def test_main_handles_runtime_error_response(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        client,
        "run_runtime_request",
        lambda **kwargs: {
            "status": "error",
            "uID": "Kba9Cw",
        },
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 6
    assert "[FAILED]" in output
    assert "runtime execution failed" in output


def test_main_rejects_invalid_timeout(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv(
        "NOVAVISION_CLIENT_TIMEOUT",
        "not-a-number",
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 2
    assert "must be a number" in output