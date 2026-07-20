"""Response builder for the Environment Secrets Store component."""

import json

from sdks.novavision.src.helper.package import PackageHelper

from components.EnvironmentSecretsStore.src.models.PackageModel import (
    ConfigExecutor,
    EnvironmentSecretsStoreExecutor,
    PackageConfigs,
    PackageModel,
    PackageOutputs,
    PackageResponse,
    SecretsOutput,
)


def build_response(context):
    """Build the NovaVision response containing retrieved secrets."""

    secrets_json = json.dumps(
        context.secrets,
        ensure_ascii=False,
    )

    secrets_output = SecretsOutput(
        value=secrets_json,
    )

    package_outputs = PackageOutputs(
        secrets=secrets_output,
    )

    package_response = PackageResponse(
        outputs=package_outputs,
    )

    component_executor = EnvironmentSecretsStoreExecutor(
        value=package_response,
    )

    executor = ConfigExecutor(
        value=component_executor,
    )

    package_configs = PackageConfigs(
        executor=executor,
    )

    package_helper = PackageHelper(
        packageModel=PackageModel,
        packageConfigs=package_configs,
    )

    return package_helper.build_model(context)