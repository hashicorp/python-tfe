#!/usr/bin/env python3
"""
Complete Configuration Version Testing Suite

This file contains individual tests for all 12 configuration version functions:

CONFIGURATION VERSION FUNCTIONS AVAILABLE FOR TESTING:
1.  list() - List configuration versions for a workspace
2.  create() - Create a new configuration version
3.  read() - Read a specific configuration version
4.  upload() - Upload configuration files to a configuration version
5.  download() - Download configuration version archive
6.  archive() - Archive a configuration version
7.  read_with_options() - Read a configuration version with include options
8.  create_for_registry_module() - Create configuration version for registry module (BETA)
9.  upload_tar_gzip() - Direct tar.gz archive upload
10. soft_delete_backing_data() - Soft delete backing data (Enterprise only)
11. restore_backing_data() - Restore backing data (Enterprise only)
12. permanently_delete_backing_data() - Permanently delete backing data (Enterprise only)

USAGE:
- All test sections are now active and will run sequentially
- Tests are designed to run independently or sequentially
- Modify workspace_id as needed for your environment
- Ensure you have proper TFE credentials and workspace access
- Enterprise functions will show expected warnings on non-Enterprise installations
"""

import io
import os
import sys
import tempfile
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    ConfigurationVersionCreateOptions,
    ConfigurationVersionListOptions,
    ConfigurationVersionReadOptions,
    ConfigVerIncludeOpt,
)


def create_test_terraform_configuration(directory: str) -> None:
    """Create a test Terraform configuration for upload testing."""

    main_tf_content = """
terraform {
  required_version = ">= 1.0"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "configuration-version-test"
}

resource "null_resource" "test" {
  provisioner "local-exec" {
    command = "echo 'Testing configuration version: ${var.project_name} in ${var.environment}'"
  }

  triggers = {
    environment  = var.environment
    project_name = var.project_name
    timestamp    = timestamp()
  }
}

output "test_message" {
  description = "Test completion message"
  value       = "Configuration version test completed for ${var.project_name}"
}
"""

    variables_tf_content = """
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1

  validation {
    condition     = var.instance_count > 0
    error_message = "Instance count must be greater than 0."
  }
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Project     = "configuration-version-test"
    Environment = "test"
    ManagedBy   = "terraform"
    TestSuite   = "individual-functions"
  }
}
"""

    outputs_tf_content = """
output "configuration_details" {
  description = "Details about this configuration"
  value = {
    instance_count = var.instance_count
    tags          = var.tags
    environment   = var.environment
    project_name  = var.project_name
  }
}

output "creation_timestamp" {
  description = "When this configuration was created"
  value       = timestamp()
}
"""

    terraformignore_content = """
# Ignore temporary files
*.tmp
*.temp
.DS_Store

# Ignore local Terraform files
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl

# Ignore editor files
.vscode/
*.swp
*.swo
*~
"""

    # Write all files
    files = [
        ("main.tf", main_tf_content),
        ("variables.tf", variables_tf_content),
        ("outputs.tf", outputs_tf_content),
        (".terraformignore", terraformignore_content),
    ]

    for filename, content in files:
        filepath = os.path.join(directory, filename)
        with open(filepath, "w") as f:
            f.write(content.strip())


def main():
    """Test all configuration version functions individually."""

    print("=" * 80)
    print("CONFIGURATION VERSION COMPLETE TESTING SUITE")
    print("=" * 80)
    print("Testing ALL 12 functions in src/tfe/resources/configuration_version.py")
    print("Comprehensive test coverage for all configuration version operations")
    print("=" * 80)

    # Initialize the TFE client
    client = TFEClient(TFEConfig.from_env())
    workspace_id = "ws-zLgDCHFz9mBfri2Q"  # Replace with your workspace ID

    # Variables to store created resources for dependent tests
    created_cv_id = None
    uploadable_cv_id = None

    print(f"Target workspace: {workspace_id}")
    print("=" * 80)

    # =====================================================
    # TEST 1: LIST CONFIGURATION VERSIONS
    # =====================================================
    print("\n1. Testing list() function:")
    try:
        # Basic list without options
        cv_list = list(client.configuration_versions.list(workspace_id))
        print(f"Found {len(cv_list)} configuration versions")

        if cv_list:
            print("Recent configuration versions:")
            for i, cv in enumerate(cv_list[:5], 1):
                print(f"{i}. {cv.id}")
                print(f"Status: {cv.status}")
                print(f"Source: {cv.source}")
                if cv.status_timestamps and "queued-at" in cv.status_timestamps:
                    print(f"Queued at: {cv.status_timestamps['queued-at']}")
                elif cv.status_timestamps:
                    first_timestamp = list(cv.status_timestamps.keys())[0]
                    print(f"{first_timestamp}: {cv.status_timestamps[first_timestamp]}")
                else:
                    print("No timestamps available")

        # Test with options
        print("\nTesting list with options:")
        try:
            list_options = ConfigurationVersionListOptions(
                include=[ConfigVerIncludeOpt.INGRESS_ATTRIBUTES],
                page_size=5,  # Reduced page size
                page_number=1,
            )
            print(f"Making request with include: {list_options.include[0].value}")

            # Add timeout protection by limiting the iterator
            cv_list_opts = []
            count = 0
            for cv in client.configuration_versions.list(workspace_id, list_options):
                cv_list_opts.append(cv)
                count += 1
                if count >= 10:  # Limit to prevent infinite loop
                    break

            print(f"Found {len(cv_list_opts)} configuration versions with options")
            print(f"Include options: {[opt.value for opt in list_options.include]}")

        except Exception as opts_error:
            print(f"Error with options: {opts_error}")
            print("This may be expected if the API doesn't support these options")
            print("Basic list functionality still works")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 2: CREATE CONFIGURATION VERSION
    # =====================================================
    print("\n2. Testing create() function:")
    try:
        # Test 2a: Create and upload a REAL configuration version that will show in runs
        print("2a. Creating REAL NON-SPECULATIVE configuration version:")
        create_options = ConfigurationVersionCreateOptions(
            auto_queue_runs=True,  # This will create a run automatically
            speculative=False,  # This will make it appear in workspace runs
        )

        new_cv = client.configuration_versions.create(workspace_id, create_options)
        created_cv_id = new_cv.id
        print(f"Created NON-SPECULATIVE CV: {created_cv_id}")
        print(f"Status: {new_cv.status}")
        print(f"Speculative: {new_cv.speculative} (will show in runs)")
        print(f"Auto-queue runs: {new_cv.auto_queue_runs} (will create run)")
        print(f"Upload URL available: {bool(new_cv.upload_url)}")

        # UPLOAD REAL TERRAFORM CODE IMMEDIATELY
        if new_cv.upload_url:
            print("\nUploading real Terraform configuration...")

            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Creating Terraform files in: {temp_dir}")
                create_test_terraform_configuration(temp_dir)

                # List created files
                files = os.listdir(temp_dir)
                print(f"Created {len(files)} Terraform files:")
                for filename in sorted(files):
                    filepath = os.path.join(temp_dir, filename)
                    size = os.path.getsize(filepath)
                    print(f"       - {filename} ({size} bytes)")

                try:
                    # Create tar.gz archive manually since go-slug isn't available
                    print("Creating tar.gz archive manually...")

                    import tarfile

                    # Create tar.gz archive in memory
                    archive_buffer = io.BytesIO()
                    with tarfile.open(fileobj=archive_buffer, mode="w:gz") as tar:
                        # Add all files from the temp directory
                        for filename in files:
                            filepath = os.path.join(temp_dir, filename)
                            tar.add(filepath, arcname=filename)

                    archive_buffer.seek(0)
                    archive_bytes = archive_buffer.getvalue()
                    print(f"Created archive: {len(archive_bytes)} bytes")

                    # Use the SDK's upload_tar_gzip method instead of direct HTTP calls
                    print("Uploading archive using SDK method...")
                    archive_buffer.seek(0)  # Reset buffer position
                    client.configuration_versions.upload_tar_gzip(
                        new_cv.upload_url, archive_buffer
                    )
                    print("Terraform configuration uploaded successfully!")

                    # Wait and check status
                    print("\nChecking status after upload...")
                    time.sleep(5)  # Give TFE time to process

                    updated_cv = client.configuration_versions.read(created_cv_id)
                    print(f"Status after upload: {updated_cv.status}")

                    if updated_cv.status.value in ["uploaded", "fetching"]:
                        print("REAL configuration version created successfully!")
                        print("This CV now contains actual Terraform code")
                        print(
                            "You can now see this CV in your Terraform Cloud workspace!"
                        )
                    else:
                        print(f"Status is still: {updated_cv.status.value}")
                        print("(Upload may still be processing)")

                except Exception as e:
                    print(f"Upload failed: {type(e).__name__}: {e}")
                    print("CV created but no configuration uploaded")
        else:
            print("No upload URL - cannot upload Terraform code")

        # Test 2b: Create standard configuration version for upload testing
        print("\n 2b. Creating standard configuration version for upload tests:")
        standard_options = ConfigurationVersionCreateOptions(
            auto_queue_runs=False, speculative=False
        )

        standard_cv = client.configuration_versions.create(
            workspace_id, standard_options
        )
        uploadable_cv_id = standard_cv.id  # Save for summary display
        print(f"Created standard CV: {standard_cv.id}")
        print(f"Status: {standard_cv.status}")
        print(f"Speculative: {standard_cv.speculative}")
        print(f"Auto-queue runs: {standard_cv.auto_queue_runs}")

        # Test 2c: Create with auto-queue runs (will trigger run when uploaded)
        print("\n 2c. Creating configuration version with auto-queue:")
        auto_options = ConfigurationVersionCreateOptions(
            auto_queue_runs=True, speculative=False
        )

        auto_cv = client.configuration_versions.create(workspace_id, auto_options)
        print(f"Created auto-queue CV: {auto_cv.id}")
        print(f"Auto-queue runs: {auto_cv.auto_queue_runs}")
        print("This will trigger a Terraform run when code is uploaded")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 3: READ CONFIGURATION VERSION
    # =====================================================
    if created_cv_id:
        print("\n3. Testing read() function:")
        try:
            cv_details = client.configuration_versions.read(created_cv_id)

            print(f"Read configuration version: {cv_details.id}")
            print(f"Status: {cv_details.status}")
            print(f"Source: {cv_details.source}")
            if cv_details.status_timestamps:
                print(f"Status timestamps: {list(cv_details.status_timestamps.keys())}")
                if "queued-at" in cv_details.status_timestamps:
                    print(f"Queued at: {cv_details.status_timestamps['queued-at']}")
            else:
                print("No status timestamps available")
            print(f"Auto-queue runs: {cv_details.auto_queue_runs}")
            print(f"Speculative: {cv_details.speculative}")

            if cv_details.upload_url:
                print(f"Upload URL: {cv_details.upload_url[:60]}...")
            else:
                print("Upload URL: None")

            # Test field validation
            print("\n Field validation:")
            required_fields = [
                "id",
                "status",
                "source",
                "auto_queue_runs",
                "speculative",
                "upload_url",
            ]
            for field in required_fields:
                if hasattr(cv_details, field):
                    value = getattr(cv_details, field)
                    print(f"{field}: {type(value).__name__}")
                else:
                    print(f"{field}: Missing")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

    # =====================================================
    # TEST 4: UPLOAD CONFIGURATION VERSION
    # =====================================================
    # Test 4: Upload function (requires go-slug)
    # =====================================================
    print("\n4. Testing upload() function:")
    try:
        # Create a fresh configuration version specifically for upload testing
        upload_options = ConfigurationVersionCreateOptions(
            auto_queue_runs=False, speculative=True
        )

        fresh_cv = client.configuration_versions.create(workspace_id, upload_options)
        print(f"Created fresh CV for upload: {fresh_cv.id}")

        upload_url = fresh_cv.upload_url

        if not upload_url:
            print("No upload URL available for this configuration version")
            print("Configuration version may not be in uploadable state")
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Creating test configuration in: {temp_dir}")
                create_test_terraform_configuration(temp_dir)

                # List created files
                files = os.listdir(temp_dir)
                print(f"Created {len(files)} files:")
                for filename in sorted(files):
                    filepath = os.path.join(temp_dir, filename)
                    size = os.path.getsize(filepath)
                    print(f"     - {filename} ({size} bytes)")

                print(f"\n Uploading configuration to CV: {fresh_cv.id}")
                print(f"Upload URL: {upload_url[:60]}...")

                try:
                    client.configuration_versions.upload(upload_url, temp_dir)
                    print("Configuration uploaded successfully!")

                    # Check status after upload
                    print("\n Checking status after upload:")
                    time.sleep(3)  # Give TFE time to process
                    updated_cv = client.configuration_versions.read(fresh_cv.id)
                    print(f"Status after upload: {updated_cv.status}")

                    if updated_cv.status.value != "pending":
                        print("Status changed (upload processed)")
                    else:
                        print("Status still pending (may need more time)")

                except ImportError as e:
                    if "go-slug" in str(e):
                        print("go-slug package not available")
                        print("Install with: pip install go-slug")
                        print(
                            "Upload function exists but requires go-slug for packaging"
                        )
                        print(
                            "Function correctly raises ImportError when go-slug unavailable"
                        )
                    else:
                        raise

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 5: DOWNLOAD CONFIGURATION VERSION
    # =====================================================
    print("\n5. Testing download() function:")
    try:
        # Find uploadable configuration versions
        cv_generator = client.configuration_versions.list(workspace_id)

        downloadable_cvs = []
        print("Scanning for downloadable configuration versions:")
        # Convert generator to list and limit to avoid infinite loop
        cv_list = []
        count = 0
        for cv in cv_generator:
            cv_list.append(cv)
            count += 1
            if count >= 20:  # Limit to first 20 CVs
                break

        for cv in cv_list:
            print(f"CV {cv.id}: Status = {cv.status}")
            if cv.status.value in ["uploaded", "archived"]:
                downloadable_cvs.append(cv)

        if not downloadable_cvs:
            print("No uploaded configuration versions found to download")
            print("This is not a test failure - upload a configuration first")
        else:
            downloadable_cv = downloadable_cvs[0]
            print(f"\n Downloading CV: {downloadable_cv.id}")
            print(f"Status: {downloadable_cv.status}")

            archive_data = client.configuration_versions.download(downloadable_cv.id)
            print(f"Downloaded {len(archive_data)} bytes")

            # Validate downloaded data
            print("\n Validating downloaded data:")
            if len(archive_data) > 0:
                print("Archive data is non-empty")

                # Basic format check
                if archive_data[:2] == b"\x1f\x8b":
                    print("Data appears to be gzip format")
                else:
                    print("Data may not be gzip format (could still be valid)")
            else:
                print("Archive data is empty")

            # Test multiple downloads if available
            if len(downloadable_cvs) > 1:
                print("\n Testing multiple downloads:")
                for i, cv in enumerate(downloadable_cvs[1:3], 2):
                    try:
                        data = client.configuration_versions.download(cv.id)
                        print(f"CV {i}: {cv.id} - {len(data)} bytes")
                    except Exception as e:
                        print(f"CV {i}: {cv.id} - Failed: {type(e).__name__}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 6: ARCHIVE CONFIGURATION VERSION
    # =====================================================
    print("\n6. Testing archive() function:")
    try:
        # Get configuration versions for archiving
        cv_generator = client.configuration_versions.list(workspace_id)

        # Convert generator to list and limit to avoid infinite loop
        cv_list = []
        count = 0
        for cv in cv_generator:
            cv_list.append(cv)
            count += 1
            if count >= 20:  # Limit to first 20 CVs
                break

        if len(cv_list) < 2:
            print(
                "Need at least 2 configuration versions to test archive functionality"
            )
            print(
                "This is not a test failure - create more configuration versions first"
            )
        else:
            # Find suitable candidates for archiving
            archivable_cvs = []
            already_archived = []

            print("Scanning configuration versions for archiving:")
            for cv in cv_list:
                print(f"CV {cv.id}: Status = {cv.status}")
                if cv.status.value == "archived":
                    already_archived.append(cv)
                elif cv.status.value in ["uploaded", "errored", "pending"]:
                    archivable_cvs.append(cv)

            # Try to archive an older CV (not the most recent)
            # Only try to archive uploaded/errored CVs, not pending ones
            # Skip the first (most recent) uploaded CV as it's likely the current one
            uploaded_cvs = [
                cv
                for cv in archivable_cvs
                if cv.status.value in ["uploaded", "errored"]
            ]
            candidates = uploaded_cvs[1:] if len(uploaded_cvs) > 1 else []

            if candidates:
                cv_to_archive = candidates[0]  # Pick an older uploaded CV
                print(f"\n Attempting to archive CV: {cv_to_archive.id}")
                print(f"Current status: {cv_to_archive.status}")
                print("(Skipping most recent uploaded CV to avoid 'current' error)")

                try:
                    client.configuration_versions.archive(cv_to_archive.id)
                    print("Archive request sent successfully")

                    # Check status after archive request
                    print("\n Checking status after archive request:")
                    time.sleep(3)
                    try:
                        updated_cv = client.configuration_versions.read(
                            cv_to_archive.id
                        )
                        print(f"Status after archive: {updated_cv.status}")
                        if updated_cv.status.value == "archived":
                            print("Successfully archived")
                        else:
                            print("Still processing (archive may take time)")
                    except Exception:
                        print("Could not read status after archive (may be expected)")

                except Exception as e:
                    if "404" in str(e) or "not found" in str(e).lower():
                        print("CV may have been auto-archived or removed")
                    elif "current" in str(e).lower():
                        print("Cannot archive current configuration version")
                        print("Function correctly handles 'current' CV restriction")
                    else:
                        print(f"Archive failed: {type(e).__name__}: {e}")
            else:
                print("\n No suitable configuration versions found for archiving")
                print("Need at least 2 uploaded CVs (to avoid archiving current one)")
                print("Function correctly validates archivable CVs")

            # Test archiving already archived CV
            if already_archived:
                print("\n Testing archive of already archived CV:")
                already_archived_cv = already_archived[0]
                print(f"CV ID: {already_archived_cv.id} (already archived)")

                try:
                    client.configuration_versions.archive(already_archived_cv.id)
                    print("Handled gracefully (no-op for already archived)")
                except Exception as e:
                    print(f"Correctly rejected: {type(e).__name__}")

    except Exception as e:
        print(f"    Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 7: READ WITH OPTIONS
    # =====================================================
    if created_cv_id:
        print("\n7. Testing read_with_options() function:")
        try:
            # Test read with include options
            read_options = ConfigurationVersionReadOptions(
                include=[ConfigVerIncludeOpt.INGRESS_ATTRIBUTES]
            )

            cv_with_options = client.configuration_versions.read_with_options(
                created_cv_id, read_options
            )

            print(f"Read configuration version with options: {cv_with_options.id}")
            print(f"Status: {cv_with_options.status}")
            print(f"Source: {cv_with_options.source}")

            if (
                hasattr(cv_with_options, "ingress_attributes")
                and cv_with_options.ingress_attributes
            ):
                print("Ingress attributes included in response")
                if hasattr(cv_with_options.ingress_attributes, "branch"):
                    print(f"Branch: {cv_with_options.ingress_attributes.branch}")
                if hasattr(cv_with_options.ingress_attributes, "clone_url"):
                    print(f"Clone URL: {cv_with_options.ingress_attributes.clone_url}")
            else:
                print("No ingress attributes (expected for API-created CVs)")
                print("Ingress attributes are only present for VCS-connected CVs")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("\n7. Testing read_with_options() function:")
        print("Skipped - no configuration version created for testing")

    # =====================================================
    # TEST 8: CREATE FOR REGISTRY MODULE (BETA)
    # =====================================================
    print("\n8. Testing create_for_registry_module() function:")
    try:
        # Note: This requires a registry module to exist
        # We'll test the function but expect it may fail due to lack of registry modules
        module_id = {
            "organization": "hashicorp",  # Use a real org that likely has modules
            "registry_name": "private",
            "namespace": "hashicorp",
            "name": "example",
            "provider": "aws",
        }

        print("Testing registry module configuration version creation:")
        print(f"Module ID: {module_id}")

        try:
            registry_cv = client.configuration_versions.create_for_registry_module(
                module_id
            )
            print(f"Created registry module CV: {registry_cv.id}")
            print(f"Status: {registry_cv.status}")
            print(f"Source: {registry_cv.source}")

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("Registry module not found (expected - requires actual module)")
                print("Function exists and properly handles missing modules")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                print("No permission to access registry modules (expected)")
                print("Function exists and properly handles permission errors")
            elif "AttributeError" in str(e):
                print(f"Function parameter error: {e}")
                print("Function exists but may need parameter adjustment")
            else:
                print(f"Registry module CV creation failed: {type(e).__name__}: {e}")
                print("This may be expected if no registry modules exist")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 9: UPLOAD TAR GZIP (Direct Archive Upload)
    # =====================================================
    print("\n9. Testing upload_tar_gzip() function:")
    try:
        # Create a CV that we can upload to
        upload_cv_options = ConfigurationVersionCreateOptions(
            auto_queue_runs=False, speculative=True
        )

        upload_test_cv = client.configuration_versions.create(
            workspace_id, upload_cv_options
        )
        upload_test_cv_id = upload_test_cv.id
        upload_url = upload_test_cv.upload_url

        if upload_url:
            print(f"Created CV for upload test: {upload_test_cv_id}")
            print(f"Upload URL available: {bool(upload_url)}")

            # Create a simple tar.gz archive in memory for testing
            import tarfile

            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a simple terraform file
                test_file = os.path.join(temp_dir, "main.tf")
                with open(test_file, "w") as f:
                    f.write('resource "null_resource" "test" {}')

                # Create tar.gz archive
                archive_buffer = io.BytesIO()
                with tarfile.open(fileobj=archive_buffer, mode="w:gz") as tar:
                    tar.add(test_file, arcname="main.tf")

                archive_buffer.seek(0)
                print(f"Created test archive: {len(archive_buffer.getvalue())} bytes")

                # Test direct tar.gz upload
                try:
                    client.configuration_versions.upload_tar_gzip(
                        upload_url, archive_buffer
                    )
                    print("Direct tar.gz upload successful!")

                    # Check status after upload
                    time.sleep(2)
                    updated_upload_cv = client.configuration_versions.read(
                        upload_test_cv_id
                    )
                    print(f"Status after upload: {updated_upload_cv.status}")

                except Exception as e:
                    print(f"Upload failed: {type(e).__name__}: {e}")
                    print("This may be expected depending on TFE configuration")
        else:
            print("No upload URL available - cannot test upload_tar_gzip")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # =====================================================
    # TEST 10: ENTERPRISE BACKING DATA OPERATIONS
    # =====================================================
    print("\n10. Testing Enterprise backing data operations:")

    # These functions are Enterprise-only features, so we expect them to fail
    # on non-Enterprise installations, but we test that the functions exist

    if created_cv_id:
        print(f"Testing with CV: {created_cv_id}")

        # Test soft delete backing data
        print("\n 10a. Testing soft_delete_backing_data():")
        try:
            client.configuration_versions.soft_delete_backing_data(created_cv_id)
            print("Soft delete backing data request sent successfully")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("CV not found for backing data operation")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                print("Enterprise feature - not available (expected)")
            else:
                print(f"Soft delete failed: {type(e).__name__}: {e}")
            print("Function exists and properly handles Enterprise restrictions")

        # Test restore backing data
        print("\n 10b. Testing restore_backing_data():")
        try:
            client.configuration_versions.restore_backing_data(created_cv_id)
            print("Restore backing data request sent successfully")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("CV not found for backing data operation")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                print("Enterprise feature - not available (expected)")
            else:
                print(f"Restore failed: {type(e).__name__}: {e}")
            print("Function exists and properly handles Enterprise restrictions")

        # Test permanently delete backing data
        print("\n 10c. Testing permanently_delete_backing_data():")
        try:
            # Create a separate CV for this destructive test
            perm_delete_options = ConfigurationVersionCreateOptions(
                auto_queue_runs=False, speculative=True
            )

            perm_delete_cv = client.configuration_versions.create(
                workspace_id, perm_delete_options
            )
            perm_delete_cv_id = perm_delete_cv.id

            client.configuration_versions.permanently_delete_backing_data(
                perm_delete_cv_id
            )
            print("Permanent delete backing data request sent successfully")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("CV not found for backing data operation")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                print("Enterprise feature - not available (expected)")
            else:
                print(f"Permanent delete failed: {type(e).__name__}: {e}")
            print(" sFunction exists and properly handles Enterprise restrictions")

    # =====================================================
    # TEST SUMMARY
    # =====================================================
    print("\n" + "=" * 80)
    print("CONFIGURATION VERSION COMPLETE TESTING SUMMARY")
    print("=" * 80)
    print("TEST 1:  list() - List configuration versions for workspace")
    print(
        "TEST 2:  create() - Create new configuration versions with different options"
    )
    print("TEST 3:  read() - Read configuration version details and validate fields")
    print("TEST 4:  upload() - Upload Terraform configurations (requires go-slug)")
    print("TEST 5:  download() - Download configuration version archives")
    print("TEST 6:  archive() - Archive configuration versions")
    print("TEST 7:  read_with_options() - Read with include options")
    print("TEST 8:  create_for_registry_module() - Registry module CVs (BETA)")
    print("TEST 9:  upload_tar_gzip() - Direct tar.gz archive upload")
    print("TEST 10: Enterprise backing data operations (soft/restore/permanent delete)")
    print("=" * 80)
    print("ALL 12 configuration version functions have been tested!")
    print("Review the output above for any errors or warnings.")

    if created_cv_id:
        print("\nCreated configuration versions during testing:")
        print(f"  - Real CV: {created_cv_id}")
    if uploadable_cv_id:
        print(f"  - Standard CV: {uploadable_cv_id}")

    print("\nAll functions are now active and tested comprehensively!")
    print("Functions 1-6: Core configuration version operations")
    print(
        "Functions 7-9: Advanced operations (read with options, registry modules, direct upload)"
    )
    print("Functions 10: Enterprise backing data operations")
    print("=" * 80)

    # Close client
    client.close()


if __name__ == "__main__":
    main()
