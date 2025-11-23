"""Provider registry utilities for AniBridge plugins."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from importlib import metadata

from anibridge_providers.library import LibraryProvider
from anibridge_providers.list import ListProvider
from anibridge_providers.provider import BaseProvider

__all__ = [
    "ProviderDescriptor",
    "ProviderKind",
    "ProviderRegistry",
    "get_global_registry",
    "load_entry_points",
    "register_library_provider",
    "register_list_provider",
]

_LOG = logging.getLogger(__name__)


class ProviderKind(str, Enum):
    """Kinds of providers supported by AniBridge."""

    LIBRARY = "library"
    LIST = "list"


@dataclass(slots=True)
class ProviderDescriptor:
    """Metadata describing a provider class registered with the SDK."""

    namespace: str
    kind: ProviderKind
    provider_cls: type[BaseProvider]

    def __post_init__(self) -> None:
        """Normalize the namespace to a consistent lowercase form."""
        self.namespace = self.namespace.lower()


@dataclass(slots=True)
class ProviderRegistry:
    """Registry of available providers keyed by kind and namespace."""

    _providers: dict[tuple[ProviderKind, str], ProviderDescriptor] = field(
        default_factory=dict
    )

    def register(self, descriptor: ProviderDescriptor) -> ProviderDescriptor:
        """Register a provider descriptor, replacing any previous value.

        Args:
            descriptor (ProviderDescriptor): The provider descriptor to register.

        Returns:
            ProviderDescriptor: The registered provider descriptor.
        """
        key = (descriptor.kind, descriptor.namespace)
        self._providers[key] = descriptor
        return descriptor

    def get(self, kind: ProviderKind, namespace: str) -> ProviderDescriptor | None:
        """Retrieve a provider descriptor by kind and namespace.

        Args:
            kind (ProviderKind): The kind of provider.
            namespace (str): The namespace of the provider.

        Returns:
            ProviderDescriptor | None: The provider descriptor if found, else None.
        """
        return self._providers.get((kind, namespace.lower()))

    def require(self, kind: ProviderKind, namespace: str) -> ProviderDescriptor:
        """Retrieve a provider descriptor or raise a KeyError.

        Args:
            kind (ProviderKind): The kind of provider.
            namespace (str): The namespace of the provider.

        Returns:
            ProviderDescriptor: The provider descriptor.
        """
        descriptor = self.get(kind, namespace)
        if descriptor is None:
            raise KeyError(
                f"Provider '{namespace}' of kind '{kind.value}' is not registered"
            )
        return descriptor

    def available(self) -> list[ProviderDescriptor]:
        """Return all registered provider descriptors.

        Returns:
            list[ProviderDescriptor]: All registered provider descriptors.
        """
        return list(self._providers.values())


_GLOBAL_REGISTRY: ProviderRegistry | None = None


def get_global_registry() -> ProviderRegistry:
    """Return the process-wide provider registry.

    Returns:
        ProviderRegistry: The global provider registry.
    """
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ProviderRegistry()
    return _GLOBAL_REGISTRY


def _register_kind(
    kind: ProviderKind,
    namespace: str,
    provider_cls: type[BaseProvider],
) -> type[BaseProvider]:
    """Register a provider class for the given kind and namespace."""
    descriptor = ProviderDescriptor(
        namespace=namespace,
        kind=kind,
        provider_cls=provider_cls,
    )
    get_global_registry().register(descriptor)
    return provider_cls


def register_library_provider(
    namespace: str,
) -> Callable[[type[LibraryProvider]], type[LibraryProvider]]:
    """Decorator registering a LibraryProvider class for the given namespace.

    Example:
        @register_library_provider("my_namespace")
        class MyLibraryProvider(LibraryProvider):
            ...

    Args:
        namespace (str): The namespace of the library provider.

    Returns:
        Callable[[type[BaseProvider]], type[BaseProvider]]: The decorator function.
    """

    def decorator(cls: type[LibraryProvider]) -> type[LibraryProvider]:
        return _register_kind(ProviderKind.LIBRARY, namespace, cls)

    return decorator


def register_list_provider(
    namespace: str,
) -> Callable[[type[ListProvider]], type[ListProvider]]:
    """Decorator registering a ListProvider class for the given namespace.

    Example:
        @register_list_provider("my_namespace")
        class MyListProvider(ListProvider):
            ...

    Args:
        namespace (str): The namespace of the list provider.

    Returns:
        Callable[[type[ListProvider]], type[ListProvider]]: The decorator function.
    """

    def decorator(cls: type[ListProvider]) -> type[ListProvider]:
        return _register_kind(ProviderKind.LIST, namespace, cls)

    return decorator


ENTRY_POINT_GROUP = "anibridge.providers"


def load_entry_points(group: str = ENTRY_POINT_GROUP) -> None:
    """Load all entry points for provider registration.

    Args:
        group (str): The entry point group to load providers from.
    """
    eps = metadata.entry_points()
    selected = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])

    for entry_point in selected:
        try:
            obj = entry_point.load()
        except Exception:
            _LOG.exception(f"Failed to load provider entry point '{entry_point}'")
            continue

        if callable(obj):
            try:
                obj(get_global_registry())
            except TypeError:
                obj()
        elif isinstance(obj, type):
            # Support direct provider class entry points (namespace inference)
            namespace = getattr(obj, "NAMESPACE", entry_point.name)
            kind_value = getattr(obj, "PROVIDER_KIND", None)
            if not isinstance(kind_value, ProviderKind):
                _LOG.warning(f"Provider class '{obj}' missing PROVIDER_KIND; skipping")
                continue
            _register_kind(kind_value, namespace, obj)
        else:
            _LOG.warning(
                f"Entry point '{entry_point}' returned unsupported object {obj!r}",
                entry_point,
                obj,
            )
