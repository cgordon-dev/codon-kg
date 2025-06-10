# enrichment_mcp.py

from mcp_factory import create_mcp_server, ToolSpec
from enrichment_tools import (
  FetchPWCInput, FetchPWCOutput, fetch_pwc_benchmarks_handler,
  SemanticSearchInput, SemanticSearchOutput, semantic_search_handler
)

tool_specs = [
    ToolSpec(
      name="fetch_pwc_benchmarks",
      input_schema=FetchPWCInput,
      output_schema=FetchPWCOutput,
      handler=fetch_pwc_benchmarks_handler
    ),
    ToolSpec(
      name="semantic_search",
      input_schema=SemanticSearchInput,
      output_schema=SemanticSearchOutput,
      handler=semantic_search_handler
    ),
]

app = create_mcp_server(
  title="Codon Enrichment MCP",
  version="1.0.0",
  tool_specs=tool_specs,
  prefix="/mcp/enrichment"
)