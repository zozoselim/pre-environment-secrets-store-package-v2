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
    """Return only safe secret references."""

    package_outputs = PackageOutputs(
        secretReferences=SecretReferencesOutput(
            value=context.secret_references,
        ),
    )

    package_response = PackageResponse(
        outputs=package_outputs,
    )

    component_executor = EnvironmentSecretsStoreExecutor(
        value=package_response,
    )

    package_configs = PackageConfigs(
        executor=ConfigExecutor(
            value=component_executor,
        ),
    )

    package_helper = PackageHelper(
        packageModel=PackageModel,
        packageConfigs=package_configs,
    )

    return package_helper.build_model(context)
