# depgraph

Visualizes Python project dependency trees as interactive SVG graphs.

---

## Installation

```bash
pip install depgraph
```

Or install from source:

```bash
git clone https://github.com/yourname/depgraph.git && cd depgraph && pip install .
```

---

## Usage

Analyze a project's dependencies and generate an interactive SVG graph:

```bash
depgraph generate --output deps.svg
```

Point it at a specific `requirements.txt` or `pyproject.toml`:

```bash
depgraph generate --input requirements.txt --output deps.svg
```

Use it as a library:

```python
from depgraph import DependencyGraph

graph = DependencyGraph.from_requirements("requirements.txt")
graph.render("deps.svg")
```

Open the resulting `deps.svg` in any browser to explore the interactive dependency tree — zoom, pan, and click nodes for package details.

---

## Options

| Flag | Description |
|------|-------------|
| `--input` | Path to `requirements.txt` or `pyproject.toml` (default: auto-detect) |
| `--output` | Output SVG file path (default: `deps.svg`) |
| `--depth` | Max dependency depth to traverse (default: unlimited) |

---

## License

MIT © 2024 yourname