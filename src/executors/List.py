"""Return requested environment secrets as an ordered list."""

import os
import sys

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../../",
    )
)

from sdks.novavision.src.helper.executor import Executor

if __package__:
    from .EnvironmentSecretsStore import EnvironmentSecretsStore
    from ..utils.response import build_response_list
else:
    from components.EnvironmentSecretsStore.src.executors.EnvironmentSecretsStore import (
        EnvironmentSecretsStore,
    )
    from components.EnvironmentSecretsStore.src.utils.response import (
        build_response_list,
    )


class List(EnvironmentSecretsStore):
    """NovaVision executor for list output mode."""

    def run(self):
        self.load_runtime_environment()
        self.secret_values = self.read_secret_values()
        return build_response_list(context=self)


if __name__ == "__main__":
    Executor(sys.argv[1]).run()
