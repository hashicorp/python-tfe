"""Legacy Agent Pool model - DEPRECATED.

This file is kept for backward compatibility.
Please use src/tfe/models/agent.py for new agent and agent pool models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# Re-export from the new agent module


class AgentPool(BaseModel):
    """Legacy Agent Pool model - use agent.AgentPool instead."""

    id: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        import warnings

        warnings.warn(
            "AgentPool from agentpool.py is deprecated. Use agent.AgentPool instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init_subclass__(**kwargs)
