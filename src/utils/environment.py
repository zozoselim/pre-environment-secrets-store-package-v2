import json
import re
from typing import Dict, List, Sequence, Union

from sdks.novavision.src.base.environment import Environment


_ENV_NAME_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*"
)


def parse_variable_names(
    raw_variable_names: Union[str, Sequence[str]],
) -> List[str]:
    if isinstance(raw_variable_names, str):
        try:
            variable_names = json.loads(
                raw_variable_names
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "variables_storing_secrets must be "
                "a valid JSON list."
            ) from error
    elif isinstance(raw_variable_names, (list, tuple)):
        variable_names = list(raw_variable_names)
    else:
        raise ValueError(
            "variables_storing_secrets must be a JSON list."
        )

    if not variable_names:
        raise ValueError(
            "At least one environment variable is required."
        )

    cleaned_names = []
    seen_names = set()

    for variable_name in variable_names:
        if not isinstance(variable_name, str):
            raise ValueError(
                "Environment variable names must be strings."
            )

        cleaned_name = variable_name.strip()

        if not _ENV_NAME_PATTERN.fullmatch(cleaned_name):
            raise ValueError(
                f"Invalid environment variable name: "
                f"{cleaned_name!r}."
            )

        normalized_name = cleaned_name.lower()

        if normalized_name in seen_names:
            raise ValueError(
                "Environment variable names must be unique."
            )

        seen_names.add(normalized_name)
        cleaned_names.append(cleaned_name)

    return cleaned_names


def read_secrets(
    variable_names: Sequence[str],
) -> Dict[str, str]:
    secrets: Dict[str, str] = {}
    missing_variables: List[str] = []

    for variable_name in variable_names:
        value = Environment.get_environment_variable(
            variable_name
        )

        if value is None:
            missing_variables.append(variable_name)
            continue

        secrets[variable_name.lower()] = value

    if missing_variables:
        raise RuntimeError(
            "Required environment variables were not found: "
            + ", ".join(missing_variables)
        )

    return secrets