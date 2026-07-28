# Environment Secrets Store

The component checks whether configured environment variables can be
accessed through NovaVision's `Environment` SDK.

Secret values are never returned, printed, or logged.

## Output

The component has one string output:

```text
message
```

Successful execution returns:

```text
Requested secret values were accessed successfully.
```

This output can be connected directly to the `secretText` input of
Secret Output Viewer in `Str` mode. The viewer then confirms that the
connection and upstream message were received successfully.
