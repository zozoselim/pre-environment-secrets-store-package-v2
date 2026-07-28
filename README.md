# Environment Secrets Store

The component reads explicitly requested values through NovaVision's
`Environment` SDK, encrypts them with Fernet, and exposes the authenticated
ciphertext to downstream workflow components.

## Runtime environment

Both this package and the trusted consumer package must receive the same key:

```text
NOVAVISION_SECRET_TRANSPORT_KEY=<Fernet key>
```

Generate a key once:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Example component configuration:

```json
["ACCESS_TOKEN", "DATABASE_PASSWORD"]
```

Outputs:

- `encryptedSecrets`: encrypted string connected to the trusted consumer
- `message`: safe status message

Plaintext secret values are never returned, printed, or logged. NovaVision's
current output model has no hidden/secret port type, so the ciphertext itself
may appear in the output panel. It cannot be decrypted without the transport
key.
