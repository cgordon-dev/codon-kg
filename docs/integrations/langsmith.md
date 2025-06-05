# 🔍 LangSmith Integration - Agent Tracing & Monitoring

**The simplest way** to track agent actions and reasoning in your Codon Knowledge Graph system using LangSmith.

## 🎯 What is LangSmith?

LangSmith is LangChain's official tracing and monitoring platform that provides:
- **Complete visibility** into agent reasoning chains
- **Performance monitoring** for LLM calls and tools
- **Debugging capabilities** for complex agent workflows
- **Analytics** on agent behavior and success rates

## 🚀 Quick Setup (3 Steps)

### 1. **Get LangSmith API Key**
1. Visit [smith.langchain.com](https://smith.langchain.com)
2. Sign up/login and create a project
3. Copy your API key

### 2. **Enable in Environment**
Edit your `.env` file:
```bash
# LangSmith Tracing
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=your-langsmith-api-key-here
LANGSMITH_PROJECT=codon-kg-agents
```

### 3. **Start Your System**
```bash
make start  # For Docker
# OR
python app.py  # For local development
```

That's it! 🎉 All agent actions are now being tracked.

## 📊 What Gets Tracked

### **Automatic Tracing**
- ✅ **All LLM calls** with prompts and responses
- ✅ **Tool executions** (Neo4j queries, Prometheus metrics, etc.)
- ✅ **Agent reasoning chains** and decision points
- ✅ **Error handling** and retry attempts
- ✅ **Performance metrics** (latency, tokens used)
- ✅ **Session tracking** per user interaction

### **Enhanced Metadata**
Each trace includes:
```json
{
  "agent": "neo4j",
  "query": "Show database schema",
  "session": "neo4j-agent-1234",
  "system": "codon-kg-agents",
  "context_keys": ["user_id", "project"]
}
```

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Required
LANGSMITH_ENABLED=true                        # Enable/disable tracing
LANGSMITH_API_KEY=your-api-key               # Your LangSmith API key

# Optional (with defaults)
LANGSMITH_PROJECT=codon-kg-agents            # Project name
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING=true                       # Detailed tracing
LANGSMITH_SESSION=                           # Custom session name
```

### **YAML Configuration**
```yaml
langsmith:
  enabled: true
  api_key: "your-langsmith-api-key"
  project: "codon-kg-agents"
  endpoint: "https://api.smith.langchain.com"
  tracing: true
  session_name: null  # Auto-generated if not provided
```

## 📈 Viewing Traces

### **LangSmith Dashboard**
1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Navigate to your `codon-kg-agents` project
3. View real-time traces as agents execute

### **Trace Information**
Each agent run creates a trace showing:
- **Input query** and context
- **LLM reasoning** step-by-step
- **Tool calls** with parameters and results
- **Final response** and metadata
- **Performance metrics** (time, tokens, cost)

### **Session Grouping**
Traces are grouped by session:
- `neo4j-agent-1234` - Neo4j database queries
- `prometheus-agent-5678` - Monitoring queries
- `infrastructure-agent-9012` - AWS/Terraform operations

## 🛠️ Advanced Usage

### **Custom Sessions**
Set custom session names for specific workflows:
```bash
LANGSMITH_SESSION=user-analysis-workflow
```

### **Programmatic Access**
```python
from shared.langsmith_tracing import get_tracer

tracer = get_tracer()
if tracer and tracer.is_enabled():
    tracer.set_session("custom-workflow")
    # Run your agent
    tracer.clear_session()
```

### **Adding Custom Tags**
```python
from shared.langsmith_tracing import create_langsmith_tags

tags = create_langsmith_tags(
    agent_name="neo4j",
    query_type="schema_analysis",
    additional_tags={"user_id": "123", "department": "engineering"}
)
```

## 📋 Agent-Specific Tracking

### **Neo4j Agent**
Tracks:
- Cypher query construction and execution
- Schema exploration reasoning
- Graph traversal decisions
- MCP tool usage vs. direct database calls

### **Prometheus Agent** 
Tracks:
- PromQL query generation
- Metric interpretation reasoning
- Alert analysis logic
- Time series data processing

### **Infrastructure Agent**
Tracks:
- AWS API calls and responses
- Terraform planning decisions
- Resource management reasoning
- Security and compliance checks

## 🔍 Debugging with LangSmith

### **Common Use Cases**

**1. Agent Not Responding Correctly**
- View the trace to see exact LLM prompts
- Check tool call parameters and responses
- Identify where reasoning went wrong

**2. Performance Issues**
- See which tools are taking longest
- Identify expensive LLM calls
- Monitor token usage patterns

**3. Error Investigation**
- Full error context with stack traces
- See what led to the error
- Understand retry behavior

### **Example Trace Analysis**
```
Session: neo4j-agent-1234
├── 🤖 Agent Start: "Show me all Person nodes"
├── 🧠 LLM Planning: Determine query approach
├── 🔧 Tool Call: neo4j_execute_cypher
│   ├── Input: "MATCH (p:Person) RETURN p LIMIT 10"
│   └── Output: [{"name": "John"}, {"name": "Jane"}]
├── 🧠 LLM Response: Format results for user
└── ✅ Final Response: "Found 2 Person nodes..."
```

## 🐳 Docker Integration

LangSmith works seamlessly with Docker:

### **In Docker Compose**
LangSmith environment variables are automatically passed to containers:
```yaml
environment:
  LANGSMITH_ENABLED: ${LANGSMITH_ENABLED:-false}
  LANGSMITH_API_KEY: ${LANGSMITH_API_KEY}
  # ... other variables
```

### **Development vs Production**
- **Development**: Individual session tracking per developer
- **Production**: Centralized monitoring with session grouping

## 💡 Best Practices

### **Session Naming**
- Use descriptive session names: `user-onboarding-flow`
- Include user/request IDs for tracking: `user-123-analysis`
- Group related operations: `batch-processing-2024-01`

### **Project Organization**
- Use separate projects for different environments
- `codon-kg-dev` for development
- `codon-kg-prod` for production
- `codon-kg-test` for testing

### **Cost Management**
- Monitor token usage in LangSmith dashboard
- Set up alerts for unusual usage patterns
- Use sampling for high-volume production workloads

## 🔒 Security & Privacy

### **Data Handling**
- LangSmith stores prompts and responses for analysis
- Sensitive data should be masked in prompts
- Use environment variables for API keys (never commit them)

### **Access Control**
- Share LangSmith project access with team members
- Use organization-level access controls
- Monitor who has access to trace data

## 🎯 Production Considerations

### **Performance Impact**
- Minimal latency overhead (< 10ms per trace)
- Async trace submission doesn't block agents
- Can disable in production if needed: `LANGSMITH_ENABLED=false`

### **Monitoring Setup**
1. **Set up alerts** for failed traces
2. **Monitor performance** metrics regularly
3. **Review traces** for optimization opportunities
4. **Set up dashboards** for key metrics

## 🚨 Troubleshooting

### **Traces Not Appearing**
1. Check API key is correct
2. Verify `LANGSMITH_ENABLED=true`
3. Check network connectivity to LangSmith
4. Look for connection errors in logs

### **Missing Trace Data**
1. Ensure all environment variables are set
2. Check LangChain version compatibility
3. Verify project name matches in dashboard

### **Performance Issues**
1. Disable tracing temporarily: `LANGSMITH_ENABLED=false`
2. Check trace buffer settings
3. Monitor network latency to LangSmith

## 📚 Additional Resources

- **LangSmith Documentation**: [docs.smith.langchain.com](https://docs.smith.langchain.com)
- **LangChain Tracing Guide**: [docs.langchain.com/tracing](https://docs.langchain.com/tracing)
- **Agent Monitoring Best Practices**: [blog.langchain.dev](https://blog.langchain.dev)

---

With LangSmith integrated, you now have **complete visibility** into your agent's reasoning and actions! 🎉

View your traces at: [smith.langchain.com](https://smith.langchain.com)