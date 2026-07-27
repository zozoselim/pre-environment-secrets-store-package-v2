"""Return one requested environment secret as a string."""

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
    from ..utils.response import build_response_str
else:
    from components.EnvironmentSecretsStore.src.executors.EnvironmentSecretsStore import (
        EnvironmentSecretsStore,
    )
    from components.EnvironmentSecretsStore.src.utils.response import (
        build_response_str,
    )


class Str(EnvironmentSecretsStore):
    """NovaVision executor for string output mode."""

    def run(self):
        self.load_runtime_environment()
        self.secret_value = self.read_single_secret()
        return build_response_str(context=self)


if __name__ == "__main__":
    Executor(sys.argv[1]).run()
