"""Tests for depgraph.graph module."""

from unittest.mock import patch

import pytest

from depgraph.graph import DependencyGraph, Node, build_graph
from depgraph.resolver import Package


def _make_package(name: str, version: str = "1.0.0", deps=None) -> Package:
    pkg = Package(name=name, version=version)
    pkg.dependencies = deps or []
    return pkg


def _package_map(*packages: Package) -> dict:
    return {pkg.name: pkg for pkg in packages}


def _mock_resolve(pkg_map):
    """Return a side_effect function that looks up packages by name."""
    return lambda name: pkg_map.get(name)


class TestNode:
    def test_name_and_version_properties(self):
        pkg = _make_package("requests", "2.28.0")
        node = Node(package=pkg)
        assert node.name == "requests"
        assert node.version == "2.28.0"

    def test_repr_shows_children(self):
        parent = Node(package=_make_package("parent"))
        child = Node(package=_make_package("child"))
        parent.children.append(child)
        assert "child" in repr(parent)


class TestDependencyGraph:
    def _simple_graph(self):
        root_pkg = _make_package("root", deps=["dep"])
        dep_pkg = _make_package("dep")
        root_node = Node(package=root_pkg)
        dep_node = Node(package=dep_pkg)
        root_node.children.append(dep_node)
        nodes = {"root": root_node, "dep": dep_node}
        return DependencyGraph(root=root_node, nodes=nodes)

    def test_all_packages_returns_unique_packages(self):
        graph = self._simple_graph()
        names = {p.name for p in graph.all_packages()}
        assert names == {"root", "dep"}

    def test_edges_returns_parent_child_tuples(self):
        graph = self._simple_graph()
        assert ("root", "dep") in graph.edges()

    def test_edges_empty_for_leaf_only_graph(self):
        pkg = _make_package("solo")
        node = Node(package=pkg)
        graph = DependencyGraph(root=node, nodes={"solo": node})
        assert graph.edges() == []


class TestBuildGraph:
    def test_returns_none_for_unknown_package(self):
        with patch("depgraph.graph.resolve_package", return_value=None):
            result = build_graph("nonexistent")
        assert result is None

    def test_single_package_no_deps(self):
        pkg = _make_package("solo")
        with patch("depgraph.graph.resolve_package", return_value=pkg):
            graph = build_graph("solo")
        assert graph is not None
        assert graph.root.name == "solo"
        assert graph.root.children == []

    def test_transitive_dependencies_resolved(self):
        pkg_map = _package_map(
            _make_package("a", deps=["b"]),
            _make_package("b", deps=["c"]),
            _make_package("c"),
        )
        with patch("depgraph.graph.resolve_package", side_effect=_mock_resolve(pkg_map)):
            graph = build_graph("a")
        assert graph is not None
        assert {n for n in graph.nodes} == {"a", "b", "c"}

    def test_max_depth_limits_traversal(self):
        pkg_map = _package_map(
            _make_package("a", deps=["b"]),
            _make_package("b", deps=["c"]),
            _make_package("c"),
        )
        with patch("depgraph.graph.resolve_package", side_effect=_mock_resolve(pkg_map)):
            graph = build_graph("a", max_depth=1)
        assert "c" not in graph.nodes

    def test_circular_dependency_does_not_infinite_loop(self):
        pkg_map = _package_map(
            _make_package("x", deps=["y"]),
            _make_package("y", deps=["x"]),
        )
        with patch("depgraph.graph.resolve_package", side_effect=_mock_resolve(pkg_map)):
            graph = build_graph("x")
        assert graph is not None
        assert {"x", "y"} == set(graph.nodes.keys())
