"""Response builder for the Environment Secrets Store component."""

from sdks.novavision.src.helper.package import PackageHelper

if __package__:
    from ..models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        MessageOutput,
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
        MessageOutput,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
        SecretReferencesOutput,
    )


SUCCESS_MESSAGE = (
    "Requested secret values were accessed successfully. "
    "Only safe environment references were returned."
)


def build_response(context):
    """Build a response containing references and a safe status message."""

    package_outputs = PackageOutputs(
        secretReferences=SecretReferencesOutput(
            value=context.secret_references,
        ),
        message=MessageOutput(
            value=SUCCESS_MESSAGE,
        ),
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
