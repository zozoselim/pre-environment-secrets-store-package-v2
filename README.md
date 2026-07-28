# Environment Secrets Store

Environment Secrets Store validates that configured environment
variables are available through NovaVision's `Environment` SDK.

## Final workflow design

The component has one output:

```text
secretReferences
```

For this configuration:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

the output is:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

These are environment-variable names, not secret values.

A trusted downstream component receives the references and resolves the
real values through the same NovaVision `Environment` SDK. It may use
those values internally, but it must never print, log, or return them.

```text
EnvironmentSecretsStore.secretReferences
            ↓
DownstreamComponent.secretList
            ↓
Environment().get_environment_variable(reference)
            ↓
Secret used internally
            ↓
Safe success message
```

## Why references are used

NovaVision's inspected `Param` and `Output` models do not expose a native
hidden/secret output type. Sending the real token through a regular
string or object output may expose it in Preview. Passing only the
environment-variable name avoids that problem.

## Runtime environment

The package does not hardcode `/opt/app/.env`. It creates NovaVision's
`Environment()` object and lets the SDK load the runtime environment.

## Security rules

- Never return or log secret values.
- Never commit `.env` files.
- Connect `secretReferences` only to trusted components.
- A downstream component must resolve references through the SDK.
