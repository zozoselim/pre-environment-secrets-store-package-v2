import importlib.util
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = PROJECT_ROOT / "apps" / "client.py"

spec = importlib.util.spec_from_file_location(
    "environment_secrets_client",
    CLIENT_PATH,
)

client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class FakeResponse:
    def __init__(
        self,
        response_data,
        status_code=200,
        json_error=False,
    ):
        self.response_data = response_data
        self.status_code = status_code
        self.ok = 200 <= status_code < 400
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("Invalid JSON")

        return self.response_data


def test_parse_variable_names():
    result = client.parse_variable_names(
        '["ENV_SECRET_TEST", "API_KEY"]'
    )

    assert result == [
        "ENV_SECRET_TEST",
        "API_KEY",
    ]


def test_parse_variable_names_rejects_invalid_json():
    try:
        client.parse_variable_names("invalid-json")
    except ValueError as error:
        assert "JSON" in str(error)
    else:
        raise AssertionError(
            "Invalid JSON value should raise ValueError."
        )


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

    values = (
        masked["configs"]["executor"]["value"]["value"]
        ["outputs"]["secrets"]["value"]
    )

    assert values == {
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


def test_main_success_masks_output(
    monkeypatch,
    capsys,
):
    response_data = {
        "outputs": {
            "secrets": {
                "name": "secrets",
                "value": {
                    "env_secret_test": (
                        "novavision-test-123"
                    )
                },
            }
        }
    }

    def fake_post(*args, **kwargs):
        assert kwargs["timeout"] == (
            client.DEFAULT_TIMEOUT_SECONDS
        )

        return FakeResponse(response_data)

    monkeypatch.setattr(
        client.requests,
        "post",
        fake_post,
    )

    monkeypatch.setenv(
        "ENV_SECRET_NAMES",
        '["ENV_SECRET_TEST"]',
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 0
    assert "[SUCCESS]" in output
    assert client.REDACTED_VALUE in output
    assert "novavision-test-123" not in output


def test_main_handles_connection_error(
    monkeypatch,
    capsys,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "Connection failed."
        )

    monkeypatch.setattr(
        client.requests,
        "post",
        fake_post,
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 4
    assert "[FAILED]" in output


def test_main_handles_http_error_and_masks_response(
    monkeypatch,
    capsys,
):
    response_data = {
        "error": "Request failed.",
        "secrets": {
            "value": {
                "env_secret_test": (
                    "novavision-test-123"
                )
            }
        },
    }

    monkeypatch.setattr(
        client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            response_data,
            status_code=400,
        ),
    )

    monkeypatch.setenv(
        "ENV_SECRET_NAMES",
        '["ENV_SECRET_TEST"]',
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 7
    assert "HTTP status: 400" in output
    assert client.REDACTED_VALUE in output
    assert "novavision-test-123" not in output


def test_main_handles_non_json_response(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            {},
            status_code=500,
            json_error=True,
        ),
    )

    result = client.main()
    output = capsys.readouterr().out

    assert result == 6
    assert "non-JSON" in output
    assert "HTTP status: 500" in output