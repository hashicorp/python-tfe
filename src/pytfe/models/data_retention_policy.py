# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel


class DataRetentionPolicy(BaseModel):
    """Deprecated: Use DataRetentionPolicyDeleteOlder instead."""

    id: str
    delete_older_than_n_days: int


class DataRetentionPolicyDeleteOlder(BaseModel):
    id: str
    delete_older_than_n_days: int


class DataRetentionPolicyDontDelete(BaseModel):
    id: str


class DataRetentionPolicyChoice(BaseModel):
    """Polymorphic data retention policy choice."""

    data_retention_policy: DataRetentionPolicy | None = None
    data_retention_policy_delete_older: DataRetentionPolicyDeleteOlder | None = None
    data_retention_policy_dont_delete: DataRetentionPolicyDontDelete | None = None

    def is_populated(self) -> bool:
        """Returns whether one of the choices is populated."""
        return (
            self.data_retention_policy is not None
            or self.data_retention_policy_delete_older is not None
            or self.data_retention_policy_dont_delete is not None
        )

    def convert_to_legacy_struct(self) -> DataRetentionPolicy | None:
        """Convert the DataRetentionPolicyChoice to the legacy DataRetentionPolicy struct."""
        if not self.is_populated():
            return None

        if self.data_retention_policy is not None:
            return self.data_retention_policy
        elif self.data_retention_policy_delete_older is not None:
            return DataRetentionPolicy(
                id=self.data_retention_policy_delete_older.id,
                delete_older_than_n_days=self.data_retention_policy_delete_older.delete_older_than_n_days,
            )
        return None


class DataRetentionPolicySetOptions(BaseModel):
    """Deprecated: Use DataRetentionPolicyDeleteOlderSetOptions instead."""

    delete_older_than_n_days: int


class DataRetentionPolicyDeleteOlderSetOptions(BaseModel):
    delete_older_than_n_days: int


class DataRetentionPolicyDontDeleteSetOptions(BaseModel):
    pass  # No additional fields needed
