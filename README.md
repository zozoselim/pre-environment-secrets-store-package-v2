# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that retrieves explicitly configured environment variables at runtime. Secret values are not embedded in the workflow definition or source code.

## Runtime architecture

The package exposes one NovaVision executor:

```text
EnvironmentSecretsStore
```

`Str` and `List` are output-mode selections inside that executor. They are not separate executor files.

```text
EnvironmentSecretsStore.run()
├── output_type = Str  -> one secret string
└── output_type = List -> ordered secret list
```

## Configuration

`variables_storing_secrets` accepts a JSON list:

```json
["MY_SECRET_A", "MY_SECRET_B"]
```

### Str mode

Str mode requires exactly one environment variable name:

```json
["OPENAI_API_KEY"]
```

Output:

```text
"secret-value"
```

### List mode

List mode accepts one or more names and preserves their order:

```json
["API_KEY", "DATABASE_PASSWORD"]
```

Output:

```json
["api-key-value", "database-password-value"]
```

Missing variables cause an error that contains variable names only, never secret values.

## NovaVision environment loading

NovaVision normally injects environment variables into the container. The executor also loads mounted dotenv files from these locations when available:

- `/opt/app/.env`
- `/opt/app/environment-secrets-store.env`
- `/storage/environment-secrets-store.env`
- `/opt/novavision/.env`
- local `.env` for development
- the optional path in `ENVIRONMENT_SECRETS_STORE_DOTENV_PATH`

Already injected environment variables take precedence because dotenv loading uses `override=False`.

## Package image

Use the existing NovaVision **Open CV** image. A separate custom image is not required for this package.

## Security

- Never commit `.env` files or real credentials.
- Never log or print output values.
- Test with a fake variable such as `ENV_SECRET_TEST`.
- Connect the `secrets` output only to trusted downstream components.

## Local schema export

Run from the image/runtime repository where the package is mounted under `components/EnvironmentSecretsStore`:

```powershell
python apps/export.py
```

This creates `data.json`.

## Local client test

Str mode:

```powershell
$env:ENV_SECRET_TEST = "novavision-test-123"
$env:ENV_SECRET_NAMES = '["ENV_SECRET_TEST"]'
$env:ENV_SECRET_OUTPUT_TYPE = "Str"
python apps/client.py
```

List mode:

```powershell
$env:ENV_SECRET_NAMES = '["API_KEY", "DATABASE_PASSWORD"]'
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
