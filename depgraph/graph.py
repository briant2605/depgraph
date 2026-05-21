"""Build a dependency graph from resolved packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from depgraph.resolver import Package, resolve_package


@dataclass
class Node:
    """Represents a package node in the dependency graph."""

    package: Package
    children: List["Node"] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.package.name

    @property
    def version(self) -> str:
        return self.package.version

    def __repr__(self) -> str:
        return f"Node({self.name}=={self.version}, children={[c.name for c in self.children]})"


@dataclass
class DependencyGraph:
    """Directed acyclic graph of package dependencies."""

    root: Node
    nodes: Dict[str, Node] = field(default_factory=dict)

    def all_packages(self) -> List[Package]:
        """Return all unique packages in the graph."""
        return [node.package for node in self.nodes.values()]

    def edges(self) -> List[tuple]:
        """Return all (parent_name, child_name) edges in the graph."""
        result = []
        for node in self.nodes.values():
            for child in node.children:
                result.append((node.name, child.name))
        return result


def build_graph(
    root_package_name: str,
    max_depth: Optional[int] = None,
) -> Optional[DependencyGraph]:
    """Build a dependency graph starting from *root_package_name*.

    Args:
        root_package_name: The top-level package to start from.
        max_depth: Optional maximum recursion depth (None = unlimited).

    Returns:
        A :class:`DependencyGraph` or ``None`` if the root package cannot
        be resolved.
    """
    visited: Set[str] = set()
    nodes: Dict[str, Node] = {}

    def _build(pkg_name: str, depth: int) -> Optional[Node]:
        if pkg_name in visited:
            return nodes.get(pkg_name)

        package = resolve_package(pkg_name)
        if package is None:
            return None

        visited.add(pkg_name)
        node = Node(package=package)
        nodes[pkg_name] = node

        if max_depth is None or depth < max_depth:
            for dep_name in package.dependencies:
                child = _build(dep_name, depth + 1)
                if child is not None:
                    node.children.append(child)

        return node

    root_node = _build(root_package_name, depth=0)
    if root_node is None:
        return None

    return DependencyGraph(root=root_node, nodes=nodes)
