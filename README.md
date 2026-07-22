# Environment Secrets Store

Environment Secrets Store is a NovaVision workflow component that retrieves an explicitly configured list of environment variables at runtime. Secret values are not embedded in the workflow definition or source code.

## Behavior

The `variables_storing_secrets` configuration accepts a JSON list:

```json
["MY_SECRET_A", "MY_SECRET_B"]
```

The component reads those names from the runtime environment and produces one object output named `secrets`:

```json
{
  "my_secret_a": "value-a",
  "my_secret_b": "value-b"
}
```

Output keys are lowercase. Missing variables cause an error that contains variable names only, never secret values.

## NovaVision environment loading

NovaVision normally injects environment variables into the container. The executor also loads mounted dotenv files from these locations when available:

- `/opt/app/.env`
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

Start the NovaVision service, then set a fake value:

```powershell
$env:ENV_SECRET_TEST = "novavision-test-123"
$env:ENV_SECRET_NAMES = '["ENV_SECRET_TEST"]'
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
3. Set `variables_storing_secrets`, for example:

   ```json
   ["ENV_SECRET_TEST"]
   ```

4. Deploy locally.
5. Connect the `secrets` object output to a trusted component that accepts object input.

## NovaVision compatibility note

Roboflow dynamically creates one visual output port per requested variable. NovaVision package schemas are static, so this implementation exposes a single object output whose lowercase keys correspond to the requested variables. Exact runtime-created visual ports require NovaVision platform support.
