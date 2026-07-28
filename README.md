# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that validates
access to explicitly configured environment variables at runtime without
returning their values.

## Configuration

`variables_storing_secrets` accepts a JSON list:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

The component constructs NovaVision's `Environment` SDK and checks that every
requested variable exists and is non-empty.

## Outputs

The component never returns the secret values. It exposes two safe outputs:

```json
{
  "secretReferences": [
    "ACCESS_TOKEN",
    "DATABASE_PASSWORD"
  ],
  "message": "Requested secret values were accessed successfully. Only safe environment references were returned."
}
```

`secretReferences` contains environment-variable names, not their values. A
trusted downstream package receives these references and resolves the real
values from its own NovaVision runtime environment:

```python
from sdks.novavision.src.base.environment import Environment

environment = Environment()

for secret_reference in secret_references:
    secret_value = environment.get_environment_variable(
        secret_reference
    )

    if secret_value is None or not str(secret_value).strip():
        raise RuntimeError(
            f"Secret could not be resolved: {secret_reference}"
        )

    # Use secret_value internally. Never print or return it.
```

The downstream component should return only a safe status message.

## Security properties

- Secret values are never included in this component's outputs.
- Secret values are never printed or logged.
- Workflow connections carry only environment-variable names.
- The downstream component resolves values directly from its own environment.
- Every downstream runtime/container must have access to the same required
  environment variables.

This is secret-reference passing and masking, not encryption.

## NovaVision environment loading

The package does not hardcode a dotenv path. It uses NovaVision's `Environment`
class and lets the SDK load the runtime environment. In the verified OpenCV
image, the SDK loads values from `/opt/app/.env`.

## Clean install test

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
```
