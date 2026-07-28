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
    from ..utils.environment import parse_variable_names
    from ..utils.response import build_response
    from ..utils.security import resolve_secure_secrets
else:
    # NovaVision executor dosyasını doğrudan çalıştırdığında.
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        PackageModel,
    )
    from components.EnvironmentSecretsStore.src.utils.environment import (
        parse_variable_names,
    )
    from components.EnvironmentSecretsStore.src.utils.response import (
        build_response,
    )
    from components.EnvironmentSecretsStore.src.utils.security import (
        resolve_secure_secrets,
    )


class EnvironmentSecretsStore(Component):
    """Resolve requested secrets and expose only an encrypted bundle."""

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.request.model = PackageModel(
            **self.request.data
        )

        self.variable_names = parse_variable_names(
            self.request.get_param(
                "variables_storing_secrets"
            )
        )

        self.secure_result: Dict[str, str] = {}

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def run(self):
        """Resolve and encrypt secrets, then build the NovaVision response."""

        self.secure_result = resolve_secure_secrets(
            self.variable_names
        )

        return build_response(
            context=self
        )


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()
