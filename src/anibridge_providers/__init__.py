"""Anibridge provider package.

This package contains the interfaces for creating Anibridge providers. Actual concrete
implementations of providers should reside in separate repositories/packages.
"""

from anibridge_providers.library import LibraryProvider
from anibridge_providers.list import ListProvider
from anibridge_providers.provider import BaseProvider
from anibridge_providers.registry import (
    ProviderDescriptor,
    ProviderKind,
    get_global_registry,
    register_library_provider,
    register_list_provider,
)

__all__ = [
    "BaseProvider",
    "LibraryProvider",
    "ListProvider",
    "ProviderDescriptor",
    "ProviderKind",
    "get_global_registry",
    "register_library_provider",
    "register_list_provider",
]
