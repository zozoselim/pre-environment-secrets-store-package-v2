# Environment Secrets Store

The component validates configured environment variables through
NovaVision's `Environment` SDK.

It returns one safe object output:

```json
{
  "message": "Requested secret values are available to trusted workflow components.",
  "references": ["ACCESS_TOKEN", "DATABASE_PASSWORD"]
}
```

The object contains only environment-variable names. It never contains
the corresponding secret values.

Connect:

```text
EnvironmentSecretsStore.secretContext
    -> SecretOutputViewer.secretContext
```

The trusted downstream component resolves the real values through the
same NovaVision `Environment` SDK, uses them internally, and returns only
a success message.

Important: if the downstream component runs in another container, the
same environment variables must also be injected into that container.
