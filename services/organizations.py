"""
Organization service for the PyTFE SDK.

This module provides methods for interacting with organization-related
endpoints in the Terraform Enterprise/Cloud API.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING

from ..models.organization import (
    Organization,
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationListOptions,
)
from ..exceptions import NotFoundError

if TYPE_CHECKING:
    from ..client import Client


class OrganizationService:
    """Service for managing organizations."""
    
    def __init__(self, client: "Client") -> None:
        """
        Initialize the organization service.
        
        Args:
            client: The PyTFE client instance.
        """
        self._client = client
    
    def list(self, options: Optional[OrganizationListOptions] = None) -> List[Organization]:
        """
        List all organizations.
        
        Args:
            options: Options for listing organizations (pagination, etc.).
            
        Returns:
            List of organizations.
            
        Raises:
            PyTFEException: If the request fails.
        """
        params = options.to_params() if options else {}
        response = self._client.get("organizations", params=params)
        
        data = response.json()
        organizations = []
        
        if "data" in data:
            for org_data in data["data"]:
                # Convert attributes to the format expected by the model
                org_dict = {
                    "id": org_data["id"],
                    "type": org_data["type"],
                    **org_data.get("attributes", {}),
                }
                
                # Handle permissions if present (same logic as read method)
                if "attributes" in org_data and "permissions" in org_data["attributes"]:
                    org_dict["permissions"] = org_data["attributes"]["permissions"]
                
                # Handle relationships if present
                if "relationships" in org_data:
                    # Add relationships to the dict if needed
                    pass
                
                organizations.append(Organization(**org_dict))
        
        return organizations
    
    def read(self, organization_name: str) -> Organization:
        """
        Read a specific organization.
        
        Args:
            organization_name: The name of the organization.
            
        Returns:
            The organization.
            
        Raises:
            NotFoundError: If the organization doesn't exist.
            PyTFEException: If the request fails.
        """
        response = self._client.get(f"organizations/{organization_name}")
        data = response.json()
        
        if "data" not in data:
            raise NotFoundError(f"Organization '{organization_name}' not found")
        
        org_data = data["data"]
        org_dict = {
            "id": org_data["id"],
            "type": org_data["type"],
            **org_data.get("attributes", {}),
        }
        
        # Handle permissions if present
        if "attributes" in org_data and "permissions" in org_data["attributes"]:
            org_dict["permissions"] = org_data["attributes"]["permissions"]
        
        return Organization(**org_dict)
    
    def create(self, request: OrganizationCreateRequest) -> Organization:
        """
        Create a new organization.
        
        Args:
            request: The organization creation request.
            
        Returns:
            The created organization.
            
        Raises:
            ValidationError: If the request data is invalid.
            PyTFEException: If the request fails.
        """
        response = self._client.post("organizations", json_data=request.model_dump())
        data = response.json()
        
        org_data = data["data"]
        org_dict = {
            "id": org_data["id"],
            "type": org_data["type"],
            **org_data.get("attributes", {}),
        }
        
        return Organization(**org_dict)
    
    def update(
        self, 
        organization_name: str, 
        request: OrganizationUpdateRequest
    ) -> Organization:
        """
        Update an existing organization.
        
        Args:
            organization_name: The name of the organization to update.
            request: The organization update request.
            
        Returns:
            The updated organization.
            
        Raises:
            NotFoundError: If the organization doesn't exist.
            ValidationError: If the request data is invalid.
            PyTFEException: If the request fails.
        """
        response = self._client.patch(
            f"organizations/{organization_name}",
            json_data=request.model_dump()
        )
        data = response.json()
        
        org_data = data["data"]
        org_dict = {
            "id": org_data["id"],
            "type": org_data["type"],
            **org_data.get("attributes", {}),
        }
        
        return Organization(**org_dict)
    
    def delete(self, organization_name: str) -> None:
        """
        Delete an organization.
        
        Args:
            organization_name: The name of the organization to delete.
            
        Raises:
            NotFoundError: If the organization doesn't exist.
            PyTFEException: If the request fails.
        """
        self._client.delete(f"organizations/{organization_name}")
    
    def entitlements(self, organization_name: str) -> Dict[str, Any]:
        """
        Get organization entitlements.
        
        Args:
            organization_name: The name of the organization.
            
        Returns:
            Dictionary containing entitlement information.
            
        Raises:
            NotFoundError: If the organization doesn't exist.
            PyTFEException: If the request fails.
        """
        response = self._client.get(f"organizations/{organization_name}/entitlement-set")
        return response.json()
    
    def capacity(self, organization_name: str) -> Dict[str, Any]:
        """
        Get organization capacity information.
        
        Args:
            organization_name: The name of the organization.
            
        Returns:
            Dictionary containing capacity information.
            
        Raises:
            NotFoundError: If the organization doesn't exist.
            PyTFEException: If the request fails.
        """
        response = self._client.get(f"organizations/{organization_name}/capacity")
        return response.json()
    
    def run_queue(
        self, 
        organization_name: str, 
        page_number: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get organization run queue.
        
        Args:
            organization_name: The name of the organization.
            page_number: Page number for pagination.
            page_size: Number of items per page.
            
        Returns:
            Dictionary containing run queue information.
            
        Raises:
            NotFoundError: If the organization doesn't exist.
            PyTFEException: If the request fails.
        """
        params = {}
        if page_number is not None:
            params["page[number]"] = page_number
        if page_size is not None:
            params["page[size]"] = page_size
        
        response = self._client.get(
            f"organizations/{organization_name}/runs/queue",
            params=params
        )
        return response.json()
