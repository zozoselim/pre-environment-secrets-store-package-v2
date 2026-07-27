# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that retrieves explicitly configured environment variables at runtime. Secret values are not embedded in the workflow definition or source code.

## Runtime architecture

The package exposes one NovaVision executor:

```text
EnvironmentSecretsStore
```

There is no `Str` or `List` executor and no output-type selector. The executor has a real `run()` method and always returns one static `secrets` object.

```text
EnvironmentSecretsStore.run()
├── reads variables_storing_secrets
├── resolves each name from the runtime environment
└── returns one secrets object
```

## Configuration

`variables_storing_secrets` accepts a JSON list of environment variable names:

```json
["OPENAI_API_KEY", "DATABASE_PASSWORD"]
```

The values are read only at runtime. The output keeps the variable names as keys:

```json
{
  "OPENAI_API_KEY": "...",
  "DATABASE_PASSWORD": "..."
}
```

The NovaVision output port is always:

```text
secrets: object
```

This static output avoids nested `Str/List` schema unions while still making all requested secrets available to downstream components.

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

```powershell
$env:ENV_SECRET_TEST = "novavision-test-123"
$env:ENV_SECRET_NAMES = '["ENV_SECRET_TEST"]'
python apps/client.py
```

Multiple names:

```powershell
$env:ENV_SECRET_NAMES = '["API_KEY", "DATABASE_PASSWORD"]'
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
