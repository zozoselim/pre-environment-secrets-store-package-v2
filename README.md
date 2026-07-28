# Environment Secrets Store

The component validates configured environment variables through NovaVision's
`Environment` SDK and exposes only their names as a safe object/list output.

Example input:

```json
["DOCKER_NETWORK", "ACCESS_TOKEN"]
```

Output:

```json
["DOCKER_NETWORK", "ACCESS_TOKEN"]
```

Secret values are not written to workflow output. Trusted downstream components
receive the references and resolve the actual values from the same NovaVision
runtime environment.
