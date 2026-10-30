# Dependency Graphs

Generated views of the import structure. They are pictures, not checks; the rules and why they exist are in [Architecture Enforcement](../enforcement.md), and the intended layering is in [architecture.md](../architecture.md#5-building-block-view).

| File | Content | Produced by |
|------|---------|-------------|
| `dependency_graph.html`, `dependency_report.html` | tach diagram and report of the declared module dependencies (committed) | `tools/tach_docs.sh` / `.bat` |
| `pydeps_graph.dot` | pydeps graph of the actual imports (committed) | `tools/pydeps_graph.sh` / `.bat` |
| `pydeps_graph.html` | page that renders the `.dot` file in a browser (committed) | static; no GraphViz needed |
| `pydeps_graph.svg` | rendered pydeps graph | `tools/pydeps_graph.sh` / `.bat`, needs [GraphViz](https://graphviz.org/download/) |
