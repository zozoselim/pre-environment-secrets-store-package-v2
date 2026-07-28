"""Response builder for Environment Secrets Store."""

from sdks.novavision.src.helper.package import PackageHelper

if __package__:
    from ..models.PackageModel import (
        ConfigExecutor,
        EncryptedSecretsOutput,
        EnvironmentSecretsStoreExecutor,
        MessageOutput,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
    )
else:
    from components.EnvironmentSecretsStore.src.models.PackageModel import (
        ConfigExecutor,
        EncryptedSecretsOutput,
        EnvironmentSecretsStoreExecutor,
        MessageOutput,
        PackageConfigs,
        PackageModel,
        PackageOutputs,
        PackageResponse,
    )


def build_response(context):
    """Return ciphertext and a plaintext-free success message."""

    outputs = PackageOutputs(
        encryptedSecrets=EncryptedSecretsOutput(
            value=context.encrypted_secrets
        ),
        message=MessageOutput(value=context.message),
    )
    response = PackageResponse(outputs=outputs)
    selected_executor = EnvironmentSecretsStoreExecutor(
        value=response
    )
    package_configs = PackageConfigs(
        executor=ConfigExecutor(value=selected_executor)
    )
    helper = PackageHelper(
        packageModel=PackageModel,
        packageConfigs=package_configs,
    )
    return helper.build_model(context)
