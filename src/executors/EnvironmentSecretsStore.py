"""Runtime executor for the Environment Secrets Store component."""

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

        variable_names = self.request.get_param(
            "variables_storing_secrets"
        )

        self.variable_names: List[str] = [
            variable_name.strip()
            for variable_name in (variable_names or [])
        ]

        self.secrets: Dict[str, str] = {}

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def read_secrets(self) -> Dict[str, str]:
        """Read secrets without logging or exposing their values."""

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

            output_name = variable_name.lower()
            secrets[output_name] = os.environ[variable_name]

        if missing_variables:
            missing_names = ", ".join(missing_variables)

            raise RuntimeError(
                "Required environment variables were not found: "
                f"{missing_names}"
            )

        return secrets

    def run(self):
        """Retrieve secrets and build the component response."""

        self.secrets = self.read_secrets()

        return build_response(context=self)

if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()