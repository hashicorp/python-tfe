"""
Example integration test template for local development.

This file shows how to create integration tests for your local development.
Copy this file to your tests/ directory and modify for your needs.

Requirements:
1. Set environment variables: TFE_TOKEN and TFE_ORG
2. Ensure your token has appropriate permissions
3. Be careful - this makes real API calls to HCP Terraform!

Usage:
    cp examples/integration_test_example.py tests/test_local_integration.py
    export TFE_TOKEN="your-token"
    export TFE_ORG="your-org"
    pytest tests/test_local_integration.py -v -s
"""

import os
import pytest
from tfe._http import HTTPTransport
from tfe.resources.projects import Projects
from tfe.config import TFEConfig


@pytest.fixture
def real_projects_client():
    """Create a real Projects client for local integration testing"""
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")
    
    if not token or not org:
        pytest.skip("TFE_TOKEN and TFE_ORG environment variables required")
    
    config = TFEConfig()
    transport = HTTPTransport(
        config.address,
        token,
        timeout=config.timeout,
        verify_tls=config.verify_tls,
        user_agent_suffix=None,
        max_retries=3,
        backoff_base=0.1,
        backoff_cap=1.0,
        backoff_jitter=True,
        http2=False,
        proxies=None,
        ca_bundle=None,
    )
    
    return Projects(transport), org


def test_list_projects_integration(real_projects_client):
    """Example integration test for listing projects"""
    projects, org = real_projects_client
    
    project_list = list(projects.list(org))
    print(f"Found {len(project_list)} projects in organization '{org}'")
    
    assert isinstance(project_list, list)
    # Add your assertions here


def test_project_crud_integration(real_projects_client):
    """Example integration test for full CRUD operations
    
    WARNING: This creates and deletes real resources in HCP Terraform!
    """
    projects, org = real_projects_client
    
    test_name = "example-test-project"
    project_id = None
    
    try:
        # CREATE
        created_project = projects.create(org, test_name)
        project_id = created_project.id
        assert created_project.name == test_name
        
        # READ
        read_project = projects.read(project_id)
        assert read_project.id == project_id
        
        # UPDATE
        updated_name = f"{test_name}-updated"
        updated_project = projects.update(project_id, updated_name)
        assert updated_project.name == updated_name
        
    finally:
        # CLEANUP - Always delete test resources
        if project_id:
            try:
                projects.delete(project_id)
                print(f"✅ Cleaned up project: {project_id}")
            except Exception as e:
                print(f"❌ Cleanup failed: {e}")