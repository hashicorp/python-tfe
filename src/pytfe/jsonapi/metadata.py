"""Field metadata extractors for Pydantic models."""

import inspect
from typing import Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from pydantic.fields import FieldInfo


class FieldMetadata:
    """Metadata about a Pydantic model field."""

    def __init__(
        self,
        field_name: str,
        field_type: type,
        jsonapi_type: str | None = None,
        jsonapi_name: str | None = None,
        is_optional: bool = False,
        is_list: bool = False,
        inner_type: type | None = None,
    ):
        self.field_name = field_name
        self.field_type = field_type
        self.jsonapi_type = jsonapi_type or self._infer_jsonapi_type()
        self.jsonapi_name = jsonapi_name or self._convert_to_jsonapi_name(field_name)
        self.is_optional = is_optional
        self.is_list = is_list
        self.inner_type = inner_type

    def _infer_jsonapi_type(self) -> str:
        """Infer JSON:API type from field name patterns."""
        if self.field_name == "id":
            return "primary"
        return "attribute"

    def _convert_to_jsonapi_name(self, field_name: str) -> str:
        """Convert Python field name to JSON:API name (snake_case to kebab-case)."""
        return field_name.replace("_", "-")


def get_model_metadata(model_class: type[BaseModel]) -> dict[str, FieldMetadata]:
    """Extract metadata for all fields in a Pydantic model.

    Returns:
        Dict mapping field name to FieldMetadata
    """
    metadata: dict[str, FieldMetadata] = {}

    # Get type hints
    try:
        type_hints = get_type_hints(model_class, include_extras=True)
    except Exception:
        type_hints = {}

    # Iterate through model fields
    for field_name, field_info in model_class.model_fields.items():
        field_type = type_hints.get(field_name, field_info.annotation)

        # Check for Field metadata
        jsonapi_type = None
        jsonapi_name = None

        if isinstance(field_info, FieldInfo):
            # Extract custom metadata from Field()
            if field_info.json_schema_extra and isinstance(
                field_info.json_schema_extra, dict
            ):
                jsonapi_type = field_info.json_schema_extra.get("jsonapi_type")
                jsonapi_name = field_info.json_schema_extra.get("jsonapi_name")
            else:
                jsonapi_type = None
                jsonapi_name = None

            # If no explicit jsonapi_name, use the Pydantic alias if available
            if not jsonapi_name and field_info.alias:
                jsonapi_name = field_info.alias

        # Handle Optional types
        is_optional = False
        is_list = False
        inner_type = field_type

        origin = get_origin(field_type)
        args = get_args(field_type)

        # Check for Optional (Union with None) - handles both Optional[X] and X | None
        import types

        if origin is types.UnionType or (
            hasattr(types, "Union") and origin is getattr(types, "Union", None)
        ):
            if type(None) in args:
                is_optional = True
                # Get the non-None type
                inner_type = next(
                    (arg for arg in args if arg is not type(None)), field_type
                )

        # Check for List
        if get_origin(inner_type) is list:
            is_list = True
            list_args = get_args(inner_type)
            if list_args:
                inner_type = list_args[0]

        # Ensure proper types for FieldMetadata
        jsonapi_type_str: str | None = None
        if jsonapi_type is not None:
            jsonapi_type_str = (
                str(jsonapi_type) if not isinstance(jsonapi_type, str) else jsonapi_type
            )

        jsonapi_name_str: str | None = None
        if jsonapi_name is not None:
            jsonapi_name_str = (
                str(jsonapi_name) if not isinstance(jsonapi_name, str) else jsonapi_name
            )

        metadata[field_name] = FieldMetadata(
            field_name=field_name,
            field_type=field_type,  # type: ignore[arg-type]
            jsonapi_type=jsonapi_type_str,
            jsonapi_name=jsonapi_name_str,
            is_optional=is_optional,
            is_list=is_list,
            inner_type=inner_type,
        )

    return metadata


def is_pydantic_model(obj: Any) -> bool:
    """Check if object is a Pydantic model class."""
    try:
        return inspect.isclass(obj) and issubclass(obj, BaseModel)
    except TypeError:
        return False
