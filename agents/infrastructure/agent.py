from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
import structlog
import json

from ..shared.base_agent import BaseAgent, AgentConfig, BaseAgentState
from ..shared.llm_factory import LLMFactory
from ..config.settings import get_config
from .tools import InfrastructureTools, AWSConfig, TerraformConfig

logger = structlog.get_logger(__name__)

class InfrastructureAgent(BaseAgent):
    def __init__(self, config: AgentConfig, aws_config: AWSConfig, terraform_config: TerraformConfig):
        super().__init__(config)
        self.infrastructure_tools = InfrastructureTools(aws_config, terraform_config)
        global_config = get_config()
        self.model = LLMFactory.create_llm(global_config.llm)
    
    def create_tools(self) -> List[Any]:
        @tool
        def terraform_init() -> str:
            """
            Initialize Terraform working directory and download providers.
            
            Returns:
                JSON string with initialization results and output
            """
            result = self.infrastructure_tools.terraform_init()
            return json.dumps(result, default=str)
        
        @tool
        def terraform_plan(var_file: str = None, target: str = None) -> str:
            """
            Create Terraform execution plan showing what changes will be made.
            
            Args:
                var_file: Path to Terraform variables file (optional)
                target: Specific resource to target (optional)
            
            Returns:
                JSON string with plan results and change summary
            """
            result = self.infrastructure_tools.terraform_plan(var_file, target)
            return json.dumps(result, default=str)
        
        @tool
        def terraform_apply(var_file: str = None, target: str = None) -> str:
            """
            Apply Terraform configuration to create/update infrastructure.
            
            Args:
                var_file: Path to Terraform variables file (optional)
                target: Specific resource to target (optional)
            
            Returns:
                JSON string with apply results and output
            """
            result = self.infrastructure_tools.terraform_apply(var_file, target)
            return json.dumps(result, default=str)
        
        @tool
        def terraform_destroy(var_file: str = None, target: str = None) -> str:
            """
            Destroy Terraform-managed infrastructure.
            
            Args:
                var_file: Path to Terraform variables file (optional)
                target: Specific resource to target (optional)
            
            Returns:
                JSON string with destroy results and output
            """
            result = self.infrastructure_tools.terraform_destroy(var_file, target)
            return json.dumps(result, default=str)
        
        @tool
        def list_ec2_instances(filters: str = None) -> str:
            """
            List AWS EC2 instances with optional filtering.
            
            Args:
                filters: JSON string of EC2 filters (e.g., '{"instance-state-name": ["running"]}')
            
            Returns:
                JSON string with EC2 instance details
            """
            try:
                filter_dict = json.loads(filters) if filters else None
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "error": "Invalid JSON filters"
                })
            
            result = self.infrastructure_tools.list_ec2_instances(filter_dict)
            return json.dumps(result, default=str)
        
        @tool
        def list_s3_buckets() -> str:
            """
            List all S3 buckets in the AWS account.
            
            Returns:
                JSON string with S3 bucket details
            """
            result = self.infrastructure_tools.list_s3_buckets()
            return json.dumps(result, default=str)
        
        @tool
        def list_cloudformation_stacks(status_filter: str = None) -> str:
            """
            List AWS CloudFormation stacks with optional status filtering.
            
            Args:
                status_filter: JSON array of status filters (e.g., '["CREATE_COMPLETE", "UPDATE_COMPLETE"]')
            
            Returns:
                JSON string with CloudFormation stack details
            """
            try:
                status_list = json.loads(status_filter) if status_filter else None
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "error": "Invalid JSON status filter"
                })
            
            result = self.infrastructure_tools.list_cloudformation_stacks(status_list)
            return json.dumps(result, default=str)
        
        return [
            terraform_init,
            terraform_plan,
            terraform_apply,
            terraform_destroy,
            list_ec2_instances,
            list_s3_buckets,
            list_cloudformation_stacks
        ]
    
    def build_graph(self) -> Any:
        tools = self.create_tools()
        
        system_prompt = """You are an infrastructure management specialist agent. Your responsibilities include:

1. **Terraform Operations**: Manage infrastructure as code with Terraform
2. **AWS Resource Management**: Monitor and interact with AWS services
3. **Infrastructure Planning**: Plan and validate infrastructure changes
4. **Resource Monitoring**: Track resource status and utilization

Key capabilities:
- Execute Terraform lifecycle operations (init, plan, apply, destroy)
- Query AWS resources (EC2, S3, CloudFormation)
- Validate infrastructure configurations
- Provide cost and security recommendations
- Implement infrastructure best practices

Terraform Workflow:
1. Always run `terraform init` before other operations
2. Use `terraform plan` to preview changes before applying
3. Execute `terraform apply` with caution - verify plans first
4. Use targeted operations for specific resources when needed
5. Document all infrastructure changes

AWS Resource Management:
- Query EC2 instances by state, type, or tags
- Monitor S3 buckets and their configurations
- Track CloudFormation stack status and changes
- Apply appropriate filters for efficient resource discovery

Security Best Practices:
- Validate all inputs and commands
- Use least-privilege access principles
- Audit all infrastructure changes
- Never expose sensitive credentials
- Follow AWS security guidelines

Safety Guidelines:
- Always preview changes with terraform plan first
- Confirm destructive operations before execution
- Use targeted deployments for critical changes
- Maintain infrastructure state backups
- Implement proper change management procedures

When executing operations:
- Provide clear explanations of what will be changed
- Highlight potential risks or impacts
- Suggest rollback procedures for major changes
- Monitor for errors and provide troubleshooting guidance
- Document successful deployments and configurations"""

        agent = create_react_agent(
            model=self.model,
            tools=tools,
            prompt=system_prompt
        )
        
        graph_builder = StateGraph(BaseAgentState)
        graph_builder.add_node("agent", agent)
        graph_builder.set_entry_point("agent")
        graph_builder.add_edge("agent", END)
        
        return graph_builder.compile()
    
    def run(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the infrastructure management agent with user input."""
        try:
            graph = self.build_graph()
            initial_state = self.get_initial_state()
            
            if context:
                initial_state["context"].update(context)
            
            inputs = {
                "messages": [HumanMessage(content=user_input)],
                "metadata": initial_state["metadata"],
                "context": initial_state["context"],
                "error_count": 0,
                "max_retries": self.config.max_retries
            }
            
            self.logger.info("Starting infrastructure agent execution", input=user_input)
            
            result = graph.invoke(inputs)
            
            return {
                "status": "success",
                "response": result["messages"][-1].content if result["messages"] else "No response",
                "metadata": result.get("metadata", {}),
                "context": result.get("context", {})
            }
            
        except Exception as e:
            self.logger.error("Infrastructure agent execution failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "response": "I encountered an error while processing your request."
            }