"""Shared runtime logic for Environment Secrets Store executors."""

import json
import os
import sys
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../",
    )
)

from sdks.novavision.src.base.component import Component

if __package__:
    from ..models.PackageModel import PackageModel
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        PackageModel,
    )


class EnvironmentSecretsStore(Component):
    """Read explicitly requested secrets from the runtime environment."""

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.load_runtime_environment()
        self.request.model = PackageModel(**self.request.data)

        raw_variable_names = self.request.get_param(
            "variables_storing_secrets"
        )
        self.variable_names = self.parse_variable_names(
            raw_variable_names
        )
        self.secret_values: List[str] = []

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    @staticmethod
    def candidate_dotenv_paths() -> Iterable[Path]:
        """Return supported dotenv locations without exposing their contents."""

        custom_path = os.getenv(
            "ENVIRONMENT_SECRETS_STORE_DOTENV_PATH"
        )
        if custom_path:
            yield Path(custom_path)

        # NovaVision runtime paths.
        yield Path("/opt/app/.env")
        yield Path("/opt/app/environment-secrets-store.env")
        yield Path("/storage/environment-secrets-store.env")
        yield Path("/opt/novavision/.env")

        # Local development fallbacks.
        yield Path.cwd() / ".env"
        yield Path(__file__).resolve().parents[2] / ".env"

    @classmethod
    def load_runtime_environment(cls) -> None:
        """Load available dotenv files while preserving injected variables."""

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
        seen_output_names = set()

        for variable_name in variable_names:
            if not isinstance(variable_name, str):
                raise ValueError(
                    "Environment variable names must be strings."
                )

            cleaned_name = variable_name.strip()
            if not cleaned_name:
                raise ValueError(
                    "Environment variable names cannot be empty."
                )

            output_name = cleaned_name.lower()
            if output_name in seen_output_names:
                raise ValueError(
                    "Environment variable names must be unique after "
                    "lowercasing."
                )

            seen_output_names.add(output_name)
            cleaned_names.append(cleaned_name)

        return cleaned_names

    def read_secret_values(self) -> List[str]:
        """Read requested secret values in configuration order."""

        secret_values: List[str] = []
        missing_variables: List[str] = []

        for variable_name in self.variable_names:
            variable_value = os.getenv(variable_name)

            if variable_value is None:
                missing_variables.append(variable_name)
                continue

            secret_values.append(variable_value)

        if missing_variables:
            raise RuntimeError(
                "Required environment variables were not found: "
                + ", ".join(missing_variables)
            )

        return secret_values

    def read_single_secret(self) -> str:
        """Read exactly one secret for Str output mode."""

        if len(self.variable_names) != 1:
            raise ValueError(
                "Str output requires exactly one environment variable name. "
                "Select List when requesting multiple secrets."
            )

        return self.read_secret_values()[0]
