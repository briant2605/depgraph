"""depgraph — Visualizes Python project dependency trees as interactive SVG graphs."""

from depgraph.resolver import Package, build_dependency_tree, resolve_package

__all__ = ["Package", "resolve_package", "build_dependency_tree"]
__version__ = "0.1.0"
