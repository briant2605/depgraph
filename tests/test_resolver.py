"""Tests for depgraph.resolver."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depgraph.resolver import (
    Package,
    _parse_requirement_name,
    build_dependency_tree,
    resolve_package,
)


# ---------------------------------------------------------------------------
# _parse_requirement_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "req, expected",
    [
        ("requests>=2.0", "requests"),
        ("flask[async]>=2.0", "flask"),
        ("numpy", "numpy"),
        ("scipy; python_version>='3.8'", "scipy"),
        ("click!=7.0,>=6.0", "click"),
    ],
)
def test_parse_requirement_name(req: str, expected: str) -> None:
    assert _parse_requirement_name(req) == expected


# ---------------------------------------------------------------------------
# resolve_package
# ---------------------------------------------------------------------------

def _make_dist(name: str, version: str, requires: list[str] | None = None) -> MagicMock:
    dist = MagicMock()
    dist.metadata = {"Version": version}
    dist.requires = requires
    return dist


def test_resolve_package_found() -> None:
    dist = _make_dist("requests", "2.28.0", ["urllib3>=1.21", "certifi"])
    with patch("depgraph.resolver.meta.distribution", return_value=dist):
        pkg = resolve_package("requests")

    assert pkg.name == "requests"
    assert pkg.version == "2.28.0"
    assert "urllib3" in pkg.dependencies
    assert "certifi" in pkg.dependencies


def test_resolve_package_not_found() -> None:
    import importlib.metadata as meta

    with patch(
        "depgraph.resolver.meta.distribution",
        side_effect=meta.PackageNotFoundError("ghost"),
    ):
        pkg = resolve_package("ghost")

    assert pkg.name == "ghost"
    assert pkg.version == "unknown"
    assert pkg.dependencies == []


def test_resolve_package_skips_env_markers() -> None:
    dist = _make_dist("mylib", "1.0", ["win32api; sys_platform=='win32'", "six"])
    with patch("depgraph.resolver.meta.distribution", return_value=dist):
        pkg = resolve_package("mylib")

    assert "six" in pkg.dependencies
    assert not any("win32api" in d for d in pkg.dependencies)


# ---------------------------------------------------------------------------
# build_dependency_tree
# ---------------------------------------------------------------------------

def test_build_dependency_tree_respects_max_depth() -> None:
    """Packages beyond max_depth should not appear in the tree."""

    def fake_distribution(name: str) -> MagicMock:
        mapping = {
            "a": ("1.0", ["b"]),
            "b": ("2.0", ["c"]),
            "c": ("3.0", ["d"]),
            "d": ("4.0", []),
        }
        version, deps = mapping.get(name, ("0", []))
        return _make_dist(name, version, deps)

    with patch("depgraph.resolver.meta.distribution", side_effect=fake_distribution):
        tree = build_dependency_tree("a", max_depth=1)

    assert "a" in tree
    assert "b" in tree
    assert "c" not in tree


def test_build_dependency_tree_no_cycles() -> None:
    """Circular dependencies must not cause infinite recursion."""

    def fake_distribution(name: str) -> MagicMock:
        mapping = {"x": ("1", ["y"]), "y": ("1", ["x"])}
        version, deps = mapping.get(name, ("0", []))
        return _make_dist(name, version, deps)

    with patch("depgraph.resolver.meta.distribution", side_effect=fake_distribution):
        tree = build_dependency_tree("x", max_depth=10)

    assert "x" in tree
    assert "y" in tree
