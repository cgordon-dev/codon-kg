# graph_mcp.py

from mcp_factory import create_mcp_server, ToolSpec
from tools import (
    CypherReadInput, CypherReadOutput, cypher_read_handler,
    CypherWriteInput, CypherWriteOutput, cypher_write_handler
)

tool_specs = [
    ToolSpec(
      name="execute_cypher_read",
      input_schema=CypherReadInput,
      output_schema=CypherReadOutput,
      handler=cypher_read_handler
    ),
    ToolSpec(
      name="execute_cypher_write",
      input_schema=CypherWriteInput,
      output_schema=CypherWriteOutput,
      handler=cypher_write_handler
    ),
]

app = create_mcp_server(
  title="Codon Neo4j Cypher MCP",
  version="1.0.0",
  tool_specs=tool_specs,
  prefix="/mcp/neo4j"
)