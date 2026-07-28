"""NovaVision executor for Environment Secrets Store."""

import os
import sys

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../",
    )
)

from sdks.novavision.src.base.component import Component

if __package__:
    from ..models.PackageModel import PackageModel
    from ..utils.crypto import encrypt_secret_values
    from ..utils.environment import (
        parse_variable_names,
        read_secrets,
        read_transport_key,
    )
    from ..utils.response import build_response
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        PackageModel,
    )
    from components.EnvironmentSecretsStore.src.utils.crypto import (
        encrypt_secret_values,
    )
    from components.EnvironmentSecretsStore.src.utils.environment import (
        parse_variable_names,
        read_secrets,
        read_transport_key,
    )
    from components.EnvironmentSecretsStore.src.utils.response import (
        build_response,
    )


class EnvironmentSecretsStore(Component):
    """Encrypt requested environment values for downstream components."""

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.request.model = PackageModel(**self.request.data)
        self.variable_names = parse_variable_names(
            self.request.get_param("variables_storing_secrets")
        )
        self.encrypted_secrets = ""
        self.message = ""

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def run(self):
        secret_values = read_secrets(self.variable_names)
        transport_key = read_transport_key()

        self.encrypted_secrets = encrypt_secret_values(
            secret_values,
            transport_key,
        )
        self.message = (
            f"{len(secret_values)} secret value(s) were encrypted "
            "and delivered successfully."
        )

        return build_response(context=self)


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()
