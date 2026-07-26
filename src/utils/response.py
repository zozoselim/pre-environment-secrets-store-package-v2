"""Response builders for Environment Secrets Store output modes."""

from sdks.novavision.src.helper.package import PackageHelper

if __package__:
    from ..models.PackageModel import (
        ConfigExecutor,
        ListExecutor,
        ListOutputs,
        ListResponse,
        PackageConfigs,
        PackageModel,
        SecretStringOutput,
        SecretsListOutput,
        StrExecutor,
        StrOutputs,
        StrResponse,
    )
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        ConfigExecutor,
        ListExecutor,
        ListOutputs,
        ListResponse,
        PackageConfigs,
        PackageModel,
        SecretStringOutput,
        SecretsListOutput,
        StrExecutor,
        StrOutputs,
        StrResponse,
    )


def _build_package(context, selected_executor):
    executor = ConfigExecutor(value=selected_executor)
    package_configs = PackageConfigs(executor=executor)
    package_helper = PackageHelper(
        packageModel=PackageModel,
        packageConfigs=package_configs,
    )
    return package_helper.build_model(context)


def build_response_str(context):
    """Build a response containing one secret as a string."""

    secrets_output = SecretStringOutput(
        value=context.secret_value,
    )
    response = StrResponse(
        outputs=StrOutputs(secrets=secrets_output),
    )
    return _build_package(
        context=context,
        selected_executor=StrExecutor(value=response),
    )


def build_response_list(context):
    """Build a response containing secrets as an ordered list."""

    secrets_output = SecretsListOutput(
        value=context.secret_values,
    )
    response = ListResponse(
        outputs=ListOutputs(secrets=secrets_output),
    )
    return _build_package(
        context=context,
        selected_executor=ListExecutor(value=response),
    )
