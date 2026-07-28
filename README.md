# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that retrieves an
explicitly configured list of environment variables at runtime. Secret values
are never embedded in the workflow definition or returned as plaintext output.

## Behavior

`variables_storing_secrets` accepts a JSON list:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

The component reads those values through NovaVision's
`Environment` SDK and returns one static object output named `secrets`:

```json
{
  "message": "Requested secret values were resolved and encrypted successfully.",
  "encrypted_payload": "gAAAAA...",
  "encryption": "fernet"
}
```

The Preview panel can display the success message and encrypted payload, but it
does not receive the plaintext secret values.

## Required encryption key

Add a Fernet key to the same NovaVision runtime environment used by both the
Environment Secrets Store component and the trusted downstream component:

```text
ENVIRONMENT_SECRETS_ENCRYPTION_KEY=<fernet-key>
```

Generate a key once:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Do not commit the generated key. The same key must be available to the trusted
downstream component that decrypts the payload.

## Downstream decryption

A trusted downstream component can decrypt the payload with:

```python
from sdks.novavision.src.base.environment import Environment
from components.EnvironmentSecretsStore.src.utils.security import (
    ENCRYPTION_KEY_VARIABLE,
    decrypt_secrets,
)

environment = Environment()
key = environment.get_environment_variable(
    ENCRYPTION_KEY_VARIABLE
)

secrets = decrypt_secrets(
    encrypted_payload=encrypted_payload,
    encryption_key=key,
)
```

Only the downstream executor should use the decrypted mapping. Never log or
return it from that component.

## NovaVision environment loading

The package does not hardcode a dotenv path. It constructs NovaVision's
`Environment` class, and the SDK loads its configured runtime environment. In
the verified Open CV image, the application values are loaded from
`/opt/app/.env`.

## Package image

Use a NovaVision-compatible image that contains the SDK and receives the
required environment variables. The existing Open CV image satisfies those
requirements, but OpenCV itself is not used by this package.

## Security boundary

Encryption prevents plaintext values from appearing in the workflow Preview
or response. It does not protect secrets from a user who has administrator
access to the container or to the shared encryption key.

## Clean install test

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
```

## Compatibility note

The output schema remains one static `secrets: object` port. No extra executor,
dynamic output type, or additional `Union` was added, which avoids the earlier
NovaVision schema parsing problem.
