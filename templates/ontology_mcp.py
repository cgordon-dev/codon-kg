# ontology_mcp.py

from mcp_factory import create_mcp_server, ToolSpec
from ontology_tools import (
  FetchOntologyInput, FetchOntologyOutput, fetch_ontology_handler,
  RDFtoJSONLDInput, RDFtoJSONLDOutput, rdf_to_jsonld_handler
)

tool_specs = [
    ToolSpec(
      name="fetch_ontology",
      input_schema=FetchOntologyInput,
      output_schema=FetchOntologyOutput,
      handler=fetch_ontology_handler
    ),
    ToolSpec(
      name="rdf_to_jsonld",
      input_schema=RDFtoJSONLDInput,
      output_schema=RDFtoJSONLDOutput,
      handler=rdf_to_jsonld_handler
    ),
]

app = create_mcp_server(
  title="Codon Ontology Ingest MCP",
  version="1.0.0",
  tool_specs=tool_specs,
  prefix="/mcp/ontology"
)