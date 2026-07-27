"""Response builder for the Environment Secrets Store component."""

from sdks.novavision.src.helper.package import PackageHelper

if __package__:
    # Clean install veya package import sırasında.
    from ..models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
        SecretsOutput,
    )
else:
    # NovaVision dosyayı doğrudan runtime içinde çalıştırdığında.
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
    """Build a response containing requested secrets as an object output."""

    secrets_output = SecretsOutput(
        value=context.secrets,
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
