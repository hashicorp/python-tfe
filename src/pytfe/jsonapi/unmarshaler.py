"""Core unmarshaling functions"""

from typing import Any, TypeVar

from pydantic import BaseModel

from .metadata import FieldMetadata, get_model_metadata, is_pydantic_model
from .types import IncludedIndex, JSONAPINode, JSONAPIResponse

T = TypeVar("T", bound=BaseModel)


def unmarshal_payload(response_dict: dict[str, Any], model_class: type[T]) -> T:
    """Unmarshal a single resource JSON:API response into a Pydantic model.

    Equivalent to jsonapi.UnmarshalPayload() in Go.

    Args:
        response_dict: Full JSON:API response dictionary
        model_class: Target Pydantic model class

    Returns:
        Instance of model_class with data populated from response

    Example:
        >>> response = requests.get("/api/v2/workspaces/ws-123").json()
        >>> workspace = unmarshal_payload(response, Workspace)
        >>> print(workspace.name)
        >>> print(workspace.project.name if workspace.project else "No project")
    """
    jsonapi_response: JSONAPIResponse = JSONAPIResponse(response_dict)

    if jsonapi_response.is_collection():
        raise ValueError("Expected single resource, got collection")

    # Type narrowing for mypy
    assert isinstance(jsonapi_response.data, dict), "Expected data to be a dict"

    data_node = JSONAPINode(jsonapi_response.data)

    return unmarshal_node(data_node, model_class, jsonapi_response.included_index)


def unmarshal_many_payload(
    response_dict: dict[str, Any], model_class: type[T]
) -> list[T]:
    """Unmarshal a collection JSON:API response into list of Pydantic models.

    Equivalent to jsonapi.UnmarshalManyPayload() in Go.

    Args:
        response_dict: Full JSON:API response dictionary
        model_class: Target Pydantic model class

    Returns:
        List of model_class instances
    """
    jsonapi_response: JSONAPIResponse = JSONAPIResponse(response_dict)

    if not jsonapi_response.is_collection():
        raise ValueError("Expected collection, got single resource")

    models: list[T] = []

    # After is_collection() check, data must be a list
    # mypy has trouble inferring this, so we assert
    data_list = jsonapi_response.data
    if not isinstance(data_list, list):  # pragma: no cover
        raise ValueError("Expected data to be a list")

    for data_item in data_list:
        if not isinstance(data_item, dict):
            continue  # type: ignore[unreachable]
        data_node = JSONAPINode(data_item)
        model = unmarshal_node(data_node, model_class, jsonapi_response.included_index)
        models.append(model)

    return models


def unmarshal_node(
    node: JSONAPINode, model_class: type[T], included_index: IncludedIndex | None = None
) -> T:
    """Recursively unmarshal a JSON:API node into a Pydantic model.

    This is the core recursive function - equivalent to unmarshalNode() in Go.

    Args:
        node: JSON:API resource node
        model_class: Target Pydantic model class
        included_index: Index of included resources for relationship resolution

    Returns:
        Instance of model_class with all fields populated
    """
    # Get metadata for all fields in the model
    field_metadata = get_model_metadata(model_class)

    # Dictionary to collect values for Pydantic model construction
    model_data: dict[str, Any] = {}

    # Process each field
    for field_name, meta in field_metadata.items():
        if meta.jsonapi_type == "primary":
            # Primary ID field
            model_data[field_name] = node.id

        elif meta.jsonapi_type == "attribute":
            # Attribute field - extract from node.attributes
            value = node.attributes.get(meta.jsonapi_name)
            if value is not None:
                model_data[field_name] = value

        elif meta.jsonapi_type == "relation":
            # Full relationship object - resolve from included
            model_data[field_name] = unmarshal_relationship(
                node, meta, included_index, is_many=meta.is_list
            )

        elif meta.jsonapi_type == "polyrelation":
            # Polymorphic relationship - resolve based on type
            model_data[field_name] = unmarshal_polyrelation(node, meta, included_index)

    # Construct the Pydantic model with collected data
    return model_class(**model_data)


def unmarshal_relationship(
    node: JSONAPINode,
    field_meta: FieldMetadata,
    included_index: IncludedIndex | None,
    is_many: bool = False,
) -> Any:
    """Unmarshal a relationship field.

    Equivalent to the relationship processing in Go's unmarshalNode.

    Args:
        node: Parent resource node
        field_meta: Metadata about the relationship field
        included_index: Index of included resources
        is_many: True if this is a to-many relationship (list)

    Returns:
        Resolved relationship object(s) or None
    """
    rel_linkage = node.get_relationship_linkage(field_meta.jsonapi_name)

    if not rel_linkage:
        return None if not is_many else []

    if is_many:
        # To-many relationship - list of resources
        if not isinstance(rel_linkage, list):
            return []

        resolved_items = []
        inner_type = field_meta.inner_type
        if inner_type is None:
            return []
        for linkage_item in rel_linkage:
            resolved = resolve_relationship_linkage(
                linkage_item, inner_type, included_index
            )
            if resolved:
                resolved_items.append(resolved)

        return resolved_items
    else:
        # To-one relationship - single resource
        if not isinstance(rel_linkage, dict):
            return None
        inner_type = field_meta.inner_type
        if inner_type is None:
            return None
        return resolve_relationship_linkage(rel_linkage, inner_type, included_index)


def resolve_relationship_linkage(
    linkage: dict[str, Any],
    target_model_class: type,
    included_index: IncludedIndex | None,
) -> Any:
    """Resolve a relationship linkage to a full object.

    This is equivalent to Go's fullNode() + recursive unmarshalNode().

    Args:
        linkage: Relationship data with type and id
        target_model_class: The model class to instantiate
        included_index: Index of included resources

    Returns:
        Resolved model instance or stub with only ID
    """
    if isinstance(linkage, dict):
        # Try to get full node from included index
        full_node = None
        if included_index:
            full_node = included_index.resolve_relationship(linkage)

        if full_node:
            # Found in included array - recursively unmarshal full object
            if is_pydantic_model(target_model_class):
                return unmarshal_node(full_node, target_model_class, included_index)
            else:
                # Not a Pydantic model, return as-is
                return full_node._raw_data
        else:
            # Not in included - create stub with only ID
            stub_data = {"id": linkage.get("id")}

            if is_pydantic_model(target_model_class):
                try:
                    return target_model_class(**stub_data)
                except Exception:
                    return None
            else:
                return stub_data
    else:
        return None  # type: ignore[unreachable]


def unmarshal_polyrelation(
    node: JSONAPINode, field_meta: FieldMetadata, included_index: IncludedIndex | None
) -> Any:
    """Unmarshal a polymorphic relationship (choice type).

    Equivalent to Go's polyrelation handling with choiceStructMapping.

    Args:
        node: Parent resource node
        field_meta: Metadata about the polyrelation field
        included_index: Index of included resources

    Returns:
        Choice object with appropriate field populated
    """
    rel_linkage = node.get_relationship_linkage(field_meta.jsonapi_name)

    if not rel_linkage or not isinstance(rel_linkage, dict):
        return None

    resource_type = rel_linkage.get("type")

    # Get the choice class
    choice_class = field_meta.inner_type

    if not is_pydantic_model(choice_class):
        return None

    # Get full node from included
    full_node = None
    if included_index:
        full_node = included_index.resolve_relationship(rel_linkage)

    if not full_node:
        # No included data, create empty choice
        if choice_class is None:
            return None
        return choice_class()

    # Find which field in the choice class matches this type
    if choice_class is None:
        return None
    choice_metadata = get_model_metadata(choice_class)

    for choice_field_name, choice_field_meta in choice_metadata.items():
        # Check if this field's type matches the resource type
        field_type = choice_field_meta.inner_type or choice_field_meta.field_type

        if is_pydantic_model(field_type):
            # Get the jsonapi type from the target model
            target_metadata = get_model_metadata(field_type)
            primary_field = next(
                (m for m in target_metadata.values() if m.jsonapi_type == "primary"),
                None,
            )

            if primary_field and primary_field.jsonapi_name == resource_type:
                # This is the matching field!
                resolved_obj: Any = unmarshal_node(
                    full_node, field_type, included_index
                )
                return choice_class(**{choice_field_name: resolved_obj})

    # No matching field found, return empty choice
    return choice_class()
