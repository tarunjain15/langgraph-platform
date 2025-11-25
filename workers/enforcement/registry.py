"""
Witness Registry (R13.4)

Registry of witness verification functions for constraint enforcement.
Witnesses verify constraints before action execution.
"""

from typing import Callable, Dict, Any, List


class WitnessRegistry:
    """Registry of witness verification functions"""

    _witnesses: Dict[str, Callable] = {}

    @staticmethod
    def register(witness_id: str, witness_fn: Callable):
        """
        Register witness function.

        Args:
            witness_id: Constraint witness identifier (from worker definition)
            witness_fn: async function(action) -> List[str] (warnings)

        Example:
            async def verify_file_size(action):
                if action.get("type") == "write":
                    size = len(action.get("content", ""))
                    if size > 1_000_000:
                        return ["File size exceeds 1MB limit"]
                return []

            WitnessRegistry.register("verify_file_size_within_limit", verify_file_size)
        """
        WitnessRegistry._witnesses[witness_id] = witness_fn

    @staticmethod
    def is_registered(witness_id: str) -> bool:
        """Check if witness function registered"""
        return witness_id in WitnessRegistry._witnesses

    @staticmethod
    async def run(witness_id: str, action: Dict[str, Any]) -> List[str]:
        """
        Run witness verification.

        Args:
            witness_id: Witness to run
            action: Action to verify

        Returns:
            List of warning messages (empty if constraint passes)

        Raises:
            KeyError: If witness not registered
        """
        if witness_id not in WitnessRegistry._witnesses:
            raise KeyError(f"Witness not registered: {witness_id}")

        witness_fn = WitnessRegistry._witnesses[witness_id]
        return await witness_fn(action)

    @staticmethod
    def list_witnesses() -> List[str]:
        """Get list of registered witness IDs"""
        return list(WitnessRegistry._witnesses.keys())

    @staticmethod
    def clear():
        """Clear all registered witnesses (for testing)"""
        WitnessRegistry._witnesses.clear()


# ============================================================================
# Built-in Witness Functions
# ============================================================================

async def verify_file_size_within_limit(action: Dict[str, Any]) -> List[str]:
    """
    Witness: Verify file size doesn't exceed limit.

    Constraint: FILE_SIZE_LIMIT
    - Write operations must not exceed 1MB
    - Prevents memory exhaustion
    """
    warnings = []

    if action.get("type") == "write":
        content = action.get("content", "")
        size_bytes = len(content.encode())
        max_size = 1_000_000  # 1MB

        if size_bytes > max_size:
            warnings.append(
                f"File size {size_bytes} bytes exceeds limit {max_size} bytes"
            )

    return warnings


async def verify_search_count_within_hourly_limit(action: Dict[str, Any]) -> List[str]:
    """
    Witness: Verify web search count within hourly limit.

    Constraint: SEARCH_RATE_LIMIT
    - Maximum 100 searches per hour per journey
    - Prevents abuse of external APIs

    Note: Currently a placeholder. Real implementation would:
    1. Track search count per user_journey_id in Redis/database
    2. Increment counter on each search action
    3. Reset counter after 1 hour
    4. Return warning if limit exceeded
    """
    warnings = []

    if action.get("type") == "web_search":
        # TODO R13.5: Implement actual rate limiting with Redis
        # For now, always pass
        pass

    return warnings


async def verify_workspace_isolation(action: Dict[str, Any]) -> List[str]:
    """
    Witness: Verify action respects workspace isolation.

    Constraint: JOURNEY_ISOLATION
    - Read/write operations must stay within workspace boundary
    - Prevents access to other journeys' data

    Note: Container isolation handles this at runtime, but we verify
    at planning time (void()) to catch violations before execution.
    """
    warnings = []

    if action.get("type") in ["read", "write", "delete"]:
        target = action.get("target", "")

        # Check for path traversal attempts
        if "../" in target or target.startswith("/"):
            warnings.append(
                f"Path traversal detected: {target} (must stay within workspace)"
            )

    return warnings


async def verify_no_network_access(action: Dict[str, Any]) -> List[str]:
    """
    Witness: Verify action doesn't access network.

    Constraint: NO_NETWORK_ACCESS
    - For sandboxed workers that should not access internet
    - Network isolation enforced at container level, but verified here too
    """
    warnings = []

    network_actions = ["web_search", "http_request", "api_call"]

    if action.get("type") in network_actions:
        warnings.append(
            f"Network access denied: {action.get('type')} (worker is sandboxed)"
        )

    return warnings


# Register built-in witnesses
WitnessRegistry.register("verify_file_size_within_limit", verify_file_size_within_limit)
WitnessRegistry.register("verify_search_count_within_hourly_limit", verify_search_count_within_hourly_limit)
WitnessRegistry.register("verify_workspace_isolation", verify_workspace_isolation)
WitnessRegistry.register("verify_no_network_access", verify_no_network_access)
