"""Response builders for Environment Secrets Store output modes."""

from sdks.novavision.src.helper.package import PackageHelper

if __package__:
    from ..models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        EnvironmentSecretsStoreOutputs,
        EnvironmentSecretsStoreResponse,
        PackageConfigs,
        PackageModel,
        SecretsOutput,
    )
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        ConfigExecutor,
        EnvironmentSecretsStoreExecutor,
        EnvironmentSecretsStoreOutputs,
        EnvironmentSecretsStoreResponse,
        PackageConfigs,
        PackageModel,
        SecretsOutput,
    )


def _build_package(context, response):
    component_executor = EnvironmentSecretsStoreExecutor(
        value=response,
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


def build_response_str(context):
    """Build a response containing one secret as a string."""

    secrets_output = SecretsOutput(
        value=context.secret_value,
        type="string",
    )

    response = EnvironmentSecretsStoreResponse(
        outputs=EnvironmentSecretsStoreOutputs(
            secrets=secrets_output,
        ),
    )

    return _build_package(
        context=context,
        response=response,
    )


def build_response_list(context):
    """Build a response containing secrets as an ordered list."""

    secrets_output = SecretsOutput(
        value=context.secret_values,
        type="object",
    )

    response = EnvironmentSecretsStoreResponse(
        outputs=EnvironmentSecretsStoreOutputs(
            secrets=secrets_output,
        ),
    )

    return _build_package(
        context=context,
        response=response,
    )