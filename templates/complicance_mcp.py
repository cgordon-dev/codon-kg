# compliance_mcp.py

from mcp_factory import create_mcp_server, ToolSpec
from compliance_tools import (
  ValidateComplianceInput, ValidateComplianceOutput, validate_compliance_handler,
  LogAuditInput, LogAuditOutput, log_audit_event_handler
)

tool_specs = [
    ToolSpec(
      name="validate_compliance",
      input_schema=ValidateComplianceInput,
      output_schema=ValidateComplianceOutput,
      handler=validate_compliance_handler
    ),
    ToolSpec(
      name="log_audit_event",
      input_schema=LogAuditInput,
      output_schema=LogAuditOutput,
      handler=log_audit_event_handler
    ),
]

app = create_mcp_server(
  title="Codon Compliance MCP",
  version="1.0.0",
  tool_specs=tool_specs,
  prefix="/mcp/compliance"
)