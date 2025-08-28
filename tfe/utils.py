"""
Utility functions for Terraform Enterprise/Cloud API.

This module provides utility functions for common operations
like JSONAPI handling and response processing.
"""

from typing import Any


def deserialize_jsonapi(data: dict[str, Any], model_class: type) -> Any:
    """Deserialize JSONAPI response to a model instance."""
    if not data:
        return None

    if "data" not in data:
        return data

    jsonapi_data = data["data"]

    if isinstance(jsonapi_data, list):
        # Handle list of resources
        return [deserialize_single_resource(item, model_class) for item in jsonapi_data]
    else:
        # Handle single resource
        return deserialize_single_resource(jsonapi_data, model_class)


def deserialize_single_resource(
    resource_data: dict[str, Any], model_class: type
) -> Any:
    """Deserialize a single JSONAPI resource to a model instance."""
    if "attributes" not in resource_data:
        return resource_data

    # Extract attributes and ID
    attributes = resource_data.get("attributes", {})
    resource_id = resource_data.get("id")

    # Add ID to attributes if it exists
    if resource_id:
        attributes["id"] = resource_id

    # Handle relationships if they exist
    relationships = resource_data.get("relationships", {})
    for rel_name, rel_data in relationships.items():
        if "data" in rel_data:
            rel_value = rel_data["data"]
            if isinstance(rel_value, dict) and "id" in rel_value:
                attributes[f"{rel_name}_id"] = rel_value["id"]
            elif isinstance(rel_value, list):
                attributes[f"{rel_name}_ids"] = [
                    item.get("id") for item in rel_value if "id" in item
                ]

    try:
        return model_class(**attributes)
    except Exception:
        # If model creation fails, return the attributes
        return attributes


def prepare_jsonapi_data(data: dict[str, Any], resource_type: str) -> dict[str, Any]:
    """Prepare data for JSONAPI format."""
    jsonapi_data = {"data": {"type": resource_type, "attributes": {}}}

    # Extract ID if present
    if "id" in data:
        jsonapi_data["data"]["id"] = data.pop("id")

    # Move all remaining data to attributes
    jsonapi_data["data"]["attributes"] = data

    return jsonapi_data


def build_query_params(**kwargs: Any) -> dict[str, Any]:
    """Build query parameters for API requests."""
    params: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is not None:
            if isinstance(value, list | tuple):
                params[key] = value
            else:
                params[key] = str(value)
    return params
