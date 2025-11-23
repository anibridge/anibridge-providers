"""Utilities for dynamically importing provider classes."""

import importlib
from types import ModuleType
from typing import Any


def load_object(import_path: str) -> Any:
    """Load a Python object using ``module:qualname`` syntax.

    Args:
        import_path: String path in ``package.module:ClassName`` format. The
            attribute portion may include dotted names for nested objects.

    Returns:
        Any: The imported object referenced by ``import_path``.

    Raises:
        ValueError: If the import path is malformed or the attribute cannot be
            resolved.
        ImportError: If the module component cannot be imported.
    """
    if ":" not in import_path:
        raise ValueError("Import path must be in 'module:qualname' format")

    module_path, qualname = import_path.split(":", 1)
    if not module_path or not qualname:
        raise ValueError("Both module and attribute names are required")

    module = importlib.import_module(module_path)
    obj: Any = module

    for attr in qualname.split("."):
        if not hasattr(obj, attr):
            raise ValueError(
                f"Attribute '{attr}' not found while resolving '{import_path}'"
            )
        obj = getattr(obj, attr)

    return obj


def load_module(module_path: str) -> ModuleType:
    """Import and return a module by dotted path.

    Args:
        module_path: The dotted path of the module to import.

    Returns:
        ModuleType: The imported module.
    """
    if not module_path:
        raise ValueError("Module path cannot be empty")

    return importlib.import_module(module_path)
