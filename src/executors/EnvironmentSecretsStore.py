"""NovaVision executor for Environment Secrets Store."""

import os
import sys
from typing import Dict


# NovaVision executor dosyayı doğrudan çalıştırdığında
# proje kökünün import edilebilmesini sağlar.
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../",
    )
)


from sdks.novavision.src.base.component import Component


if __package__:
    # Clean install veya Python paketi olarak import edildiğinde.
    from ..models.PackageModel import PackageModel
    from ..utils.environment import (
        parse_variable_names,
        read_secrets,
    )
    from ..utils.response import build_response
else:
    # NovaVision executor dosyasını doğrudan çalıştırdığında.
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        PackageModel,
    )
    from components.EnvironmentSecretsStore.src.utils.environment import (
        parse_variable_names,
        read_secrets,
    )
    from components.EnvironmentSecretsStore.src.utils.response import (
        build_response,
    )


class EnvironmentSecretsStore(Component):
    """Read requested secrets from the NovaVision runtime environment."""

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.request.model = PackageModel(
            **self.request.data
        )

        raw_variable_names = self.request.get_param(
            "variables_storing_secrets"
        )

        self.variable_names = parse_variable_names(
            raw_variable_names
        )

        self.secrets: Dict[str, str] = {}

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def run(self):
        """Read secrets and return the NovaVision response."""

        self.secrets = read_secrets(
            self.variable_names
        )

        return build_response(
            context=self
        )


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()