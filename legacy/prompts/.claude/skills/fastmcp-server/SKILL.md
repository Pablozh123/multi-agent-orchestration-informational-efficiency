---
name: fastmcp-server
description: FastMCP Server Entwicklung. Nutze beim Erstellen von MCP-Servern, Agent-Tools, MCP-Konfiguration.
---

# FastMCP Server Entwicklung

## Minimales Beispiel
```python
from fastmcp import FastMCP

mcp = FastMCP("ServerName")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Beschreibung für Claude — IMMER Docstring schreiben."""
    return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)
```

## Regeln
- IMMER async/await für I/O (DB, HTTP)
- IMMER Type Hints auf allen Parametern
- IMMER Docstrings (Claude nutzt sie als Tool-Beschreibung)
- Pydantic-Models für komplexe Inputs
- JSON-Output bevorzugen
- Error Messages actionable formulieren
- Jeden Server auf eigenem Port laufen lassen

## Testing
```python
from fastmcp import Client

async def test():
    async with Client("http://localhost:8001/mcp") as client:
        result = await client.call_tool("my_tool", {"param": "test"})
```
