# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that retrieves explicitly requested environment variables at runtime. Secret values are not embedded in the workflow definition or source code.

## Output Type

The component uses one `EnvironmentSecretsStore` executor. Its **Output Type** configuration selects the returned value shape:

- **Str**: Returns one secret value as a string.
- **List**: Returns all requested secret values as a list, in the same order as `variables_storing_secrets`.

### Str example

Configuration:

```json
["ENV_SECRET_TEST"]
```

Output:

```text
novavision-test-123
```

`Str` requires exactly one environment variable name. Selecting more than one produces a clear validation error.

### List example

Configuration:

```json
["API_KEY", "DATABASE_PASSWORD"]
```

Output:

```json
[
  "api-key-value",
  "database-password-value"
]
```

The list preserves the configuration order. Secret names are not included in the output.

## NovaVision environment loading

NovaVision normally injects environment variables into the container. The executor also loads mounted dotenv files from these locations when available:

- `/opt/app/.env`
- `/opt/app/environment-secrets-store.env`
- `/storage/environment-secrets-store.env`
- `/opt/novavision/.env`
- local `.env` for development
- the optional path in `ENVIRONMENT_SECRETS_STORE_DOTENV_PATH`

Already injected environment variables take precedence because dotenv loading uses `override=False`.

For the current NovaVision local deployment, `/storage/environment-secrets-store.env` is persistent across container restarts.

## Package structure

```text
src/
  executors/
    EnvironmentSecretsStore.py  # single runtime executor with run()
  models/
    PackageModel.py              # output type selector and response schemas
  utils/
    response.py                  # Str/List response builders
```

## Package image

Use the existing NovaVision **Open CV** image. A separate custom image is not required.

## Security

- Never commit `.env` files or real credentials.
- Never log or print secret values.
- Test with a fake variable such as `ENV_SECRET_TEST`.
- Connect secret outputs only to trusted downstream components.
- The NovaVision Raw output panel displays returned values, so do not include real credentials in screenshots.

## Local schema export

Run from the NovaVision image/runtime repository where the package is mounted under `components/EnvironmentSecretsStore`:

```powershell
python apps/export.py
```

This creates `data.json`.

## Local client test

String mode:

```powershell
$env:ENV_SECRET_TEST = "novavision-test-123"
$env:ENV_SECRET_NAMES = '["ENV_SECRET_TEST"]'
$env:ENV_SECRET_OUTPUT_TYPE = "Str"
python apps/client.py
```

List mode:

```powershell
$env:ENV_SECRET_NAMES = '["ENV_SECRET_TEST", "SECOND_SECRET"]'
$env:ENV_SECRET_OUTPUT_TYPE = "List"
python apps/client.py
```

The client masks secret values before printing the response.

## Clean install test

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
```

## Workflow usage

1. Add the Environment Secrets Store package.
2. Keep the package linked to the Open CV image.
3. Select `Str` or `List` from **Output Type** inside the executor configuration.
4. Set `variables_storing_secrets`.
5. Run the flow and connect the output to a compatible downstream component.

## Compatibility note

`Str` and `List` are output modes, not separate executor files. Both modes are handled by `EnvironmentSecretsStore.run()`.
