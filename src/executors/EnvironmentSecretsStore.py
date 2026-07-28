"""NovaVision executor for Environment Secrets Store."""

import json
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
    """Validate requested secrets and expose only their names."""

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.request.model = PackageModel(**self.request.data)
        self.variable_names = parse_variable_names(
            self.request.get_param("variables_storing_secrets")
        )
        self.secret_references = ""

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def run(self):
        references = validate_secret_access(self.variable_names)

        # NovaVision transfers strings more reliably than arbitrary objects.
        # Only variable names are serialized. Secret values never enter output.
        self.secret_references = json.dumps(references)

        return build_response(context=self)


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()
