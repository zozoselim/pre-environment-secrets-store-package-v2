"""Response builder for the Environment Secrets Store component."""

from typing import Dict

from sdks.novavision.src.helper.package import PackageHelper

from components.EnvironmentSecretsStore.src.models.PackageModel import (
    ConfigExecutor,
    EnvironmentSecretsStoreExecutor,
    PackageConfigs,
    PackageModel,
    PackageOutputs,
    PackageResponse,
    SecretOutput,
)


def create_secret_outputs(secrets: Dict[str, str]) -> Dict[str, SecretOutput]:
    """Create one separately named output model for each secret."""

    return {
        output_name: SecretOutput(
            name=output_name,
            value=secret_value,
        )
        for output_name, secret_value in secrets.items()
    }


def build_response(
    context,
    secrets: Dict[str, str],
):
    """Build a NovaVision response with one output per requested secret."""

    dynamic_outputs = create_secret_outputs(secrets)
    package_outputs = PackageOutputs(**dynamic_outputs)
    package_response = PackageResponse(outputs=package_outputs)

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
