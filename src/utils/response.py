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


def build_response(context, secrets: Dict[str, str]):
    """Build one explicitly named string output for each requested secret."""

    output_values = {
        output_name: SecretOutput(
            name=output_name,
            value=secret_value,
        )
        for output_name, secret_value in secrets.items()
    }

    package_outputs = PackageOutputs(**output_values)
    package_response = PackageResponse(outputs=package_outputs)

    component_executor = EnvironmentSecretsStoreExecutor(
        value=package_response,
    )
    executor = ConfigExecutor(value=component_executor)
    package_configs = PackageConfigs(executor=executor)

    package_helper = PackageHelper(
        packageModel=PackageModel,
        packageConfigs=package_configs,
    )

    return package_helper.build_model(context)
