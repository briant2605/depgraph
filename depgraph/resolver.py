"""Resolves Python project dependencies from package metadata."""

from __future__ import annotations

import importlib.metadata as meta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Package:
    name: str
    version: str
    dependencies: list[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.name, self.version))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Package):
            return NotImplemented
        return self.name == other.name and self.version == other.version


def _parse_requirement_name(req: str) -> str:
    """Extract the package name from a requirement string."""
    for sep in (">", "<", "=", "!", "[", ";", " "):
        req = req.split(sep)[0]
    return req.strip()


def resolve_package(name: str, _visited: Optional[set[str]] = None) -> Package:
    """Resolve a package and its direct dependencies."""
    if _visited is None:
        _visited = set()

    try:
        dist = meta.distribution(name)
    except meta.PackageNotFoundError:
        return Package(name=name, version="unknown", dependencies=[])

    version = dist.metadata["Version"] or "unknown"
    requires = dist.requires or []

    deps: list[str] = []
    for req in requires:
        # Skip extras / environment markers for now
        if ";" in req:
            continue
        dep_name = _parse_requirement_name(req)
        if dep_name and dep_name.lower() not in _visited:
            deps.append(dep_name)

    return Package(name=name, version=version, dependencies=deps)


def build_dependency_tree(
    root: str,
    max_depth: int = 3,
    _visited: Optional[set[str]] = None,
    _depth: int = 0,
) -> dict[str, Package]:
    """Recursively build a dependency tree up to *max_depth* levels."""
    if _visited is None:
        _visited = set()

    if root.lower() in _visited or _depth > max_depth:
        return {}

    _visited.add(root.lower())
    pkg = resolve_package(root, _visited)
    tree: dict[str, Package] = {pkg.name: pkg}

    for dep in pkg.dependencies:
        subtree = build_dependency_tree(dep, max_depth, _visited, _depth + 1)
        tree.update(subtree)

    return tree
