"""Response builder for Environment Secrets Store."""

from sdks.novavision.src.helper.package import PackageHelper

if __package__:
    from ..models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
        SecretReferencesOutput,
    )
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
        SecretReferencesOutput,
    )


def build_response(context):
    outputs = PackageOutputs(
        secretReferences=SecretReferencesOutput(
            value=context.secret_references
        )
    )
    response = PackageResponse(outputs=outputs)
    selected_executor = EnvironmentSecretsStoreExecutor(value=response)
    package_configs = PackageConfigs(
        executor=ConfigExecutor(value=selected_executor)
    )
    helper = PackageHelper(
        packageModel=PackageModel,
        packageConfigs=package_configs,
    )
    return helper.build_model(context)
