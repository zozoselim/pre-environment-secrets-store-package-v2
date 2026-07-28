# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that reads an
explicitly configured list of environment variables at runtime.

## Behavior

`variables_storing_secrets` accepts a JSON list:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

The component reads those values through NovaVision's `Environment` SDK. Secret
values are kept only in the executor's memory and are not returned in the
workflow output.

The visible output contains only:

```json
{
  "message": "Requested secret values were accessed successfully."
}
```

If any requested variable is missing or empty, execution fails without printing
the secret values.

## NovaVision environment loading

The package does not hardcode a dotenv path. It constructs NovaVision's
`Environment` class and lets the SDK load the runtime environment. In the
verified OpenCV image, values are loaded from `/opt/app/.env`.

## Important limitation

This success-only version validates that secret values can be accessed, but it
does not transfer those values to another workflow component. A downstream
component cannot recover a secret from the success message.

## Clean install test

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
```
