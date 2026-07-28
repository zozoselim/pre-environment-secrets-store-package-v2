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
        StatusOutput,
    )
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
        StatusOutput,
    )


def build_response(context):
    """Return one non-secret string status output."""

    package_outputs = PackageOutputs(
        message=StatusOutput(
            value=context.message,
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
