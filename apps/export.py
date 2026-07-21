"""Export the NovaVision package JSON schema to data.json."""

import json
import os
import sys

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "../../../",
    )
)

from components.EnvironmentSecretsStore.src.models.PackageModel import (
    PackageModel as Package,
)


if hasattr(Package, "model_json_schema"):
    schema = Package.model_json_schema()
else:
    schema = json.loads(Package.schema_json())

with open("data.json", "w", encoding="utf-8") as file:
    json.dump(schema, file, indent=2, ensure_ascii=False)
