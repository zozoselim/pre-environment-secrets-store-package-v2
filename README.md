# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that retrieves an explicitly configured list of environment variables at runtime. Secret values are not embedded in the workflow definition or source code.

## Behavior

The `variables_storing_secrets` configuration accepts a JSON list:

```json
["MY_SECRET_A", "MY_SECRET_B"]
```

The component reads those variables at runtime and creates one separately named string output for each requested secret:

```text
my_secret_a -> "value-a"
my_secret_b -> "value-b"
```

Output names are the lowercase forms of the environment variable names. Missing variables cause an error containing variable names only, never secret values.

## NovaVision environment loading

The executor reads already injected process environment variables and also loads mounted dotenv files from these locations when available:

- `/opt/app/.env`
- `/opt/novavision/.env`
- local `.env` for development
- the optional path in `ENVIRONMENT_SECRETS_STORE_DOTENV_PATH`

The dotenv files are reloaded before every execution because NovaVision may generate or update `/opt/app/.env` after the package worker starts.

## Package image

Use an existing NovaVision image that contains the NovaVision SDK, Python, and `python-dotenv`. The existing **Open CV** image can provide this runtime; this component does not use OpenCV image-processing functions.

## Security

- Never commit `.env` files or real credentials.
- Never log or print output values.
- Error messages contain missing variable names only.
- Connect secret outputs only to trusted downstream components.

## Example

Application `.env`:

```env
OPENAI_API_KEY=example-only
DATABASE_PASSWORD=example-only
```

Component configuration:

```json
["OPENAI_API_KEY", "DATABASE_PASSWORD"]
```

Runtime outputs:

```text
openai_api_key
database_password
```

## Local client test

```powershell
$env:ENV_SECRET_TEST = "novavision-test-123"
$env:ENV_SECRET_NAMES = '["ENV_SECRET_TEST"]'
python apps/client.py
```

The client masks all output values before printing the response.

## Clean install test

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
```

## NovaVision dynamic-output note

The response model permits dynamic output keys using `PackageOutputs.Config.extra = "allow"`. The runtime response therefore contains one output object per requested secret. Whether NovaVision's visual editor creates new connection ports immediately from runtime-added keys depends on the platform's dynamic-port support. The package code itself no longer wraps the values inside a single `secrets` object.
