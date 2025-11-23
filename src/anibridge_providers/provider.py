"""Common provider base protocol for AniBridge providers.

This defines the shared surface area between different provider kinds
(`LibraryProvider`, `ListProvider`, etc.). Individual provider protocols
extend this protocol for provider-specific operations.
"""

from dataclasses import dataclass
from typing import ClassVar, Protocol

__all__ = ["BaseProvider", "User"]


@dataclass(frozen=True, slots=True)
class User:
    """User information for a media list."""

    key: str
    title: str

    def __hash__(self) -> int:
        """Compute the hash based on the user's key."""
        return hash(self.key)


class BaseProvider(Protocol):
    """Minimal common provider protocol.

    Attributes:
        NAMESPACE (ClassVar[str]): Identifies the provider; should be unique.
    """

    NAMESPACE: ClassVar[str]

    def __init__(self, *, config: dict | None = None) -> None:
        """Initialize the provider with optional configuration.

        Args:
            config (dict | None): Any configuration options that were detected with the
                provider's namespace as a prefix.
        """

    async def initialize(self) -> None:
        """Asynchronous initialization hook.

        Put any async setup logic here (e.g., network requests).
        """
        ...

    def user(self) -> User | None:
        """Return the associated user object, if any.

        Returns:
            User | None: The associated user object, if any.
        """
        ...

    async def clear_cache(self) -> None:
        """Clear any provider-local caches."""
        ...

    async def close(self) -> None:
        """Close the provider and release resources."""
        ...
