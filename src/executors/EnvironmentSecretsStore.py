"""Runtime executor for the Environment Secrets Store component."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import load_dotenv

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../",
    )
)

from sdks.novavision.src.base.component import Component

from components.EnvironmentSecretsStore.src.models.PackageModel import (
    PackageModel,
)
from components.EnvironmentSecretsStore.src.utils.response import (
    build_response,
)


_ENV_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class EnvironmentSecretsStore(Component):
    """Read explicitly requested secrets from the runtime environment."""

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.request.model = PackageModel(**self.request.data)

        raw_variable_names = self.request.get_param(
            "variables_storing_secrets"
        )
        self.variable_names = self.parse_variable_names(
            raw_variable_names
        )
        self.secrets: Dict[str, str] = {}

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    @staticmethod
    def candidate_dotenv_paths() -> Iterable[Path]:
        """Return supported dotenv locations without exposing contents."""

        custom_path = os.getenv(
            "ENVIRONMENT_SECRETS_STORE_DOTENV_PATH"
        )
        if custom_path:
            yield Path(custom_path)

        # NovaVision application/runtime locations.
        yield Path("/opt/app/.env")
        yield Path("/opt/novavision/.env")

        # Local development fallbacks.
        yield Path.cwd() / ".env"
        yield Path(__file__).resolve().parents[2] / ".env"

    @classmethod
    def load_runtime_environment(cls) -> None:
        """Load mounted dotenv files while preserving injected variables."""

        loaded_paths = set()
        for dotenv_path in cls.candidate_dotenv_paths():
            resolved_path = dotenv_path.expanduser()
            path_key = str(resolved_path)

            if path_key in loaded_paths or not resolved_path.is_file():
                continue

            load_dotenv(
                dotenv_path=resolved_path,
                override=False,
            )
            loaded_paths.add(path_key)

    @staticmethod
    def parse_variable_names(raw_variable_names) -> List[str]:
        """Parse the UI value into a validated list of variable names."""

        if isinstance(raw_variable_names, list):
            variable_names = raw_variable_names
        elif isinstance(raw_variable_names, str):
            try:
                variable_names = json.loads(raw_variable_names)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "variables_storing_secrets must be a valid JSON list."
                ) from error
        else:
            raise ValueError(
                "variables_storing_secrets must be a JSON list."
            )

        if not isinstance(variable_names, list) or not variable_names:
            raise ValueError(
                "variables_storing_secrets must contain at least one name."
            )

        cleaned_names: List[str] = []
        seen_names = set()
        seen_output_names = set()

        for variable_name in variable_names:
            if not isinstance(variable_name, str):
                raise ValueError(
                    "Environment variable names must be strings."
                )

            cleaned_name = variable_name.strip()
            if not _ENV_NAME_PATTERN.fullmatch(cleaned_name):
                raise ValueError(
                    "Invalid environment variable name: "
                    f"{cleaned_name!r}."
                )

            if cleaned_name in seen_names:
                raise ValueError(
                    "Duplicate environment variable name: "
                    f"{cleaned_name}."
                )

            output_name = cleaned_name.lower()
            if output_name in seen_output_names:
                raise ValueError(
                    "Environment variable names must be unique after "
                    "lowercasing."
                )

            seen_names.add(cleaned_name)
            seen_output_names.add(output_name)
            cleaned_names.append(cleaned_name)

        return cleaned_names

    def read_secrets(self) -> Dict[str, str]:
        """Read requested variables without logging or hardcoding values."""

        secrets: Dict[str, str] = {}
        missing_variables: List[str] = []

        for variable_name in self.variable_names:
            variable_value = os.getenv(variable_name)

            if variable_value is None:
                missing_variables.append(variable_name)
                continue

            secrets[variable_name.lower()] = variable_value

        if missing_variables:
            raise RuntimeError(
                "Required environment variables were not found: "
                + ", ".join(missing_variables)
            )

        return secrets

    def run(self):
        """Reload the application environment and create separate outputs."""

        # NovaVision may generate/update /opt/app/.env after the worker starts.
        self.load_runtime_environment()
        self.secrets = self.read_secrets()

        return build_response(
            context=self,
            secrets=self.secrets,
        )


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()
