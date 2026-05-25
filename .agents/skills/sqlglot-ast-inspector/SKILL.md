---
name: sqlglot-ast-inspector
description: Use when Codex needs to check how `sqlglot` parses a query with the project `StarRocks` dialect by calling `sqlglot.parse_one(query, dialect=StarRocks)` and inspecting the AST for reuse in code.
---

# SQLGlot AST Inspector

Run the snippet from the repository root with the local `uv` environment.

```python
import sqlglot
from src.query_objects.dialect import StarRocks

query = "select id from table"

ast = sqlglot.parse_one(query, dialect=StarRocks)
```
