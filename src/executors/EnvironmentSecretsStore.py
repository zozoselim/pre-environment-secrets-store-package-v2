"""NovaVision executor for Environment Secrets Store."""

import os
import sys
from typing import List


sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../",
    )
)


from sdks.novavision.src.base.component import Component


if __package__:
    from ..models.PackageModel import PackageModel
    from ..utils.environment import (
        parse_variable_names,
        validate_secret_access,
    )
    from ..utils.response import build_response
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        PackageModel,
    )
    from components.EnvironmentSecretsStore.src.utils.environment import (
        parse_variable_names,
        validate_secret_access,
    )
    from components.EnvironmentSecretsStore.src.utils.response import (
        build_response,
    )


class EnvironmentSecretsStore(Component):
    """Validate secrets and expose only safe environment references."""

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

        self.secret_references: List[str] = []

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def run(self):
        """Validate secret access and build a reference-only response."""

        self.secret_references = validate_secret_access(
            self.variable_names
        )

        return build_response(
            context=self
        )


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()
