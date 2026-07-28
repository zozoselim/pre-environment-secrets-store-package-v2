"""NovaVision executor for Environment Secrets Store."""

import os
import sys
from typing import Dict, List, Union


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
    """Validate secrets and expose a safe downstream context."""

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

        self.secret_context: Dict[
            str,
            Union[str, List[str]],
        ] = {}

    @staticmethod
    def bootstrap(config: dict = None) -> dict:
        return {}

    def run(self):
        """Validate secret access and return only safe metadata."""

        references = validate_secret_access(
            self.variable_names
        )

        self.secret_context = {
            "message": (
                "Requested secret values are available "
                "to trusted workflow components."
            ),
            "references": references,
        }

        return build_response(
            context=self
        )


if __name__ == "__main__":
    from sdks.novavision.src.helper.executor import Executor

    Executor(sys.argv[1]).run()
