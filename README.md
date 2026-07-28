# Environment Secrets Store

Validates environment-variable names through NovaVision's `Environment` SDK and outputs only a JSON string containing safe references.

Example configuration:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

Output:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

Secret values are never included in workflow output.
