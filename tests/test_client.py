import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = PROJECT_ROOT / "apps" / "client.py"

spec = importlib.util.spec_from_file_location(
    "environment_secrets_store_client",
    CLIENT_PATH,
)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


def test_parse_variable_names():
    assert client.parse_variable_names(
        '["ACCESS_TOKEN"]'
    ) == ["ACCESS_TOKEN"]


def test_build_request_contains_configuration():
    payload = client.build_request(
        variable_names=["ACCESS_TOKEN"],
        component_uid="component-1",
        flow_uid="flow-1",
    )

    configured = (
        payload["configs"]["executor"]["value"]["value"]
        ["configs"]["variables_storing_secrets"]["value"]
    )
    assert json.loads(configured) == ["ACCESS_TOKEN"]
