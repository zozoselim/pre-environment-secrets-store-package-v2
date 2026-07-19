"""Runtime executor for the Environment Secrets Store component."""

import json
import os
import sys
from typing import Dict, List

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


class EnvironmentSecretsStore(Component):
    """Reads configured secrets from environment variables."""

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
    def parse_variable_names(
        raw_variable_names,
    ) -> List[str]:
        if isinstance(raw_variable_names, list):
            variable_names = raw_variable_names
        elif isinstance(raw_variable_names, str):
            try:
                variable_names = json.loads(raw_variable_names)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "variables_storing_secrets must be "
                    "a valid JSON list."
                ) from error
        else:
            raise ValueError(
                "variables_storing_secrets must be "
                "a JSON list."
            )

        if not isinstance(variable_names, list):
            raise ValueError(
                "variables_storing_secrets must be "
                "a JSON list."
            )

        return [
            variable_name.strip()
            for variable_name in variable_names
        ]

    def read_secrets(self) -> Dict[str, str]:
        if not self.variable_names:
            raise ValueError(
                "At least one environment variable name is required."
            )

        secrets: Dict[str, str] = {}
        missing_variables: List[str] = []

        for variable_name in self.variable_names:
            if variable_name not in os.environ:
                missing_variables.append(variable_name)
                continue

            secrets[variable_name.lower()] = os.environ[
                variable_name
            ]

        if missing_variables:
            raise RuntimeError(
                "Required environment variables were not found: "
                + ", ".join(missing_variables)
            )

        return secrets

    def run(self):
        self.secrets = self.read_secrets()
        return build_response(context=self)


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()