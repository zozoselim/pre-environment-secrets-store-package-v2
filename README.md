# Environment Secrets Store v0.4.0

The component validates requested environment variables through
NovaVision's `Environment` SDK and outputs only their names as a JSON
string.

Example configuration:

```json
["DOCKER_NETWORK"]
```

Output:

```json
["DOCKER_NETWORK"]
```

The actual secret value never enters the workflow output.
