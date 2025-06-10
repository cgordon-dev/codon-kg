# mcp_factory.py
from fastapi import FastAPI
from model_context_protocol.server import MCPServer, ToolSpec, ToolContext

def create_mcp_server(
    *,
    title: str,
    version: str,
    tool_specs: list[ToolSpec],
    prefix: str = "/mcp"
) -> FastAPI:
    """
    Spins up a FastAPI app exposing an MCP JSON-RPC server
    with the given tools.
    
    :param title: human-readable server name
    :param version: server version string
    :param tool_specs: list of ToolSpec(name, input_schema, output_schema, handler)
    :param prefix: URL prefix for MCP endpoints
    :returns: a FastAPI app ready to uvicorn.run()
    """
    app = FastAPI(title=title, version=version)
    server = MCPServer()

    # Register each tool with the MCPServer
    for spec in tool_specs:
        server.register_tool(
            name=spec.name,
            input_schema=spec.input_schema,
            output_schema=spec.output_schema,
            handler=spec.handler,
        )

    # Mount the JSON-RPC endpoints under /{prefix}/...
    server.mount(app, prefix)

    return app