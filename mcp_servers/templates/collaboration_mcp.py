# collaboration_mcp.py

from mcp_factory import create_mcp_server, ToolSpec
from collaboration_tools import (
  MergeContextsInput, MergeContextsOutput, merge_contexts_handler
)

tool_specs = [
    ToolSpec(
      name="merge_contexts",
      input_schema=MergeContextsInput,
      output_schema=MergeContextsOutput,
      handler=merge_contexts_handler
    ),
]

app = create_mcp_server(
  title="Codon Collaboration MCP",
  version="1.0.0",
  tool_specs=tool_specs,
  prefix="/mcp/collaboration"
)