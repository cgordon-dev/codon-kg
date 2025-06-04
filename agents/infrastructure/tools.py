import subprocess
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..shared.security import audit_log, require_security_check

logger = structlog.get_logger(__name__)

class AWSConfig(BaseModel):
    region: str = Field(default="us-east-1", description="AWS region")
    profile: Optional[str] = Field(default=None, description="AWS profile name")
    access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    session_token: Optional[str] = Field(default=None, description="AWS session token")

class TerraformConfig(BaseModel):
    working_directory: str = Field(..., description="Terraform working directory")
    state_backend: Optional[str] = Field(default=None, description="Terraform state backend")
    variables_file: Optional[str] = Field(default=None, description="Terraform variables file")
    auto_approve: bool = Field(default=False, description="Auto-approve Terraform operations")

class InfrastructureTools:
    def __init__(self, aws_config: AWSConfig, terraform_config: TerraformConfig):
        self.aws_config = aws_config
        self.terraform_config = terraform_config
        self._setup_aws_session()
        self._validate_terraform_directory()
    
    def _setup_aws_session(self):
        try:
            session_kwargs = {"region_name": self.aws_config.region}
            
            if self.aws_config.profile:
                session_kwargs["profile_name"] = self.aws_config.profile
            
            if self.aws_config.access_key_id and self.aws_config.secret_access_key:
                session_kwargs.update({
                    "aws_access_key_id": self.aws_config.access_key_id,
                    "aws_secret_access_key": self.aws_config.secret_access_key
                })
                if self.aws_config.session_token:
                    session_kwargs["aws_session_token"] = self.aws_config.session_token
            
            self.session = boto3.Session(**session_kwargs)
            
            # Test connection
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            logger.info("AWS session established", account=identity.get('Account'), user=identity.get('Arn'))
            
        except (NoCredentialsError, ClientError) as e:
            logger.error("Failed to establish AWS session", error=str(e))
            self.session = None
    
    def _validate_terraform_directory(self):
        tf_dir = Path(self.terraform_config.working_directory)
        if not tf_dir.exists():
            logger.warning("Terraform directory does not exist", directory=str(tf_dir))
        elif not any(tf_dir.glob("*.tf")):
            logger.warning("No Terraform files found in directory", directory=str(tf_dir))
    
    @audit_log("terraform_init")
    @require_security_check
    def terraform_init(self) -> Dict[str, Any]:
        try:
            cmd = ["terraform", "init"]
            result = self._run_terraform_command(cmd)
            
            return {
                "status": "success" if result["return_code"] == 0 else "error",
                "command": " ".join(cmd),
                "output": result["stdout"],
                "error": result["stderr"],
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            logger.error("Terraform init failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "command": "terraform init"
            }
    
    @audit_log("terraform_plan")
    @require_security_check
    def terraform_plan(self, var_file: Optional[str] = None, target: Optional[str] = None) -> Dict[str, Any]:
        try:
            cmd = ["terraform", "plan", "-detailed-exitcode"]
            
            if var_file or self.terraform_config.variables_file:
                var_path = var_file or self.terraform_config.variables_file
                cmd.extend(["-var-file", var_path])
            
            if target:
                cmd.extend(["-target", target])
            
            result = self._run_terraform_command(cmd)
            
            # Exit code 2 means changes are present
            has_changes = result["return_code"] == 2
            
            return {
                "status": "success",
                "command": " ".join(cmd),
                "has_changes": has_changes,
                "output": result["stdout"],
                "error": result["stderr"],
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            logger.error("Terraform plan failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "command": "terraform plan"
            }
    
    @audit_log("terraform_apply")
    @require_security_check
    def terraform_apply(self, var_file: Optional[str] = None, target: Optional[str] = None) -> Dict[str, Any]:
        try:
            cmd = ["terraform", "apply"]
            
            if self.terraform_config.auto_approve:
                cmd.append("-auto-approve")
            
            if var_file or self.terraform_config.variables_file:
                var_path = var_file or self.terraform_config.variables_file
                cmd.extend(["-var-file", var_path])
            
            if target:
                cmd.extend(["-target", target])
            
            result = self._run_terraform_command(cmd)
            
            return {
                "status": "success" if result["return_code"] == 0 else "error",
                "command": " ".join(cmd),
                "output": result["stdout"],
                "error": result["stderr"],
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            logger.error("Terraform apply failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "command": "terraform apply"
            }
    
    @audit_log("terraform_destroy")
    @require_security_check
    def terraform_destroy(self, var_file: Optional[str] = None, target: Optional[str] = None) -> Dict[str, Any]:
        try:
            cmd = ["terraform", "destroy"]
            
            if self.terraform_config.auto_approve:
                cmd.append("-auto-approve")
            
            if var_file or self.terraform_config.variables_file:
                var_path = var_file or self.terraform_config.variables_file
                cmd.extend(["-var-file", var_path])
            
            if target:
                cmd.extend(["-target", target])
            
            result = self._run_terraform_command(cmd)
            
            return {
                "status": "success" if result["return_code"] == 0 else "error",
                "command": " ".join(cmd),
                "output": result["stdout"],
                "error": result["stderr"],
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            logger.error("Terraform destroy failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "command": "terraform destroy"
            }
    
    def _run_terraform_command(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            env = os.environ.copy()
            if self.aws_config.access_key_id:
                env["AWS_ACCESS_KEY_ID"] = self.aws_config.access_key_id
            if self.aws_config.secret_access_key:
                env["AWS_SECRET_ACCESS_KEY"] = self.aws_config.secret_access_key
            if self.aws_config.session_token:
                env["AWS_SESSION_TOKEN"] = self.aws_config.session_token
            
            result = subprocess.run(
                cmd,
                cwd=self.terraform_config.working_directory,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
                env=env
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out after 30 minutes",
                "return_code": -1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    @audit_log("aws_ec2_list")
    def list_ec2_instances(self, filters: Dict[str, List[str]] = None) -> Dict[str, Any]:
        try:
            if not self.session:
                return {"status": "error", "error": "AWS session not available"}
            
            ec2 = self.session.client('ec2')
            
            kwargs = {}
            if filters:
                aws_filters = []
                for key, values in filters.items():
                    aws_filters.append({"Name": key, "Values": values})
                kwargs["Filters"] = aws_filters
            
            response = ec2.describe_instances(**kwargs)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        "instance_id": instance['InstanceId'],
                        "instance_type": instance['InstanceType'],
                        "state": instance['State']['Name'],
                        "private_ip": instance.get('PrivateIpAddress'),
                        "public_ip": instance.get('PublicIpAddress'),
                        "tags": {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            return {
                "status": "success",
                "instances": instances,
                "instance_count": len(instances)
            }
            
        except ClientError as e:
            logger.error("Failed to list EC2 instances", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    @audit_log("aws_s3_list")
    def list_s3_buckets(self) -> Dict[str, Any]:
        try:
            if not self.session:
                return {"status": "error", "error": "AWS session not available"}
            
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            buckets = []
            for bucket in response['Buckets']:
                buckets.append({
                    "name": bucket['Name'],
                    "creation_date": bucket['CreationDate'].isoformat()
                })
            
            return {
                "status": "success",
                "buckets": buckets,
                "bucket_count": len(buckets)
            }
            
        except ClientError as e:
            logger.error("Failed to list S3 buckets", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    @audit_log("aws_cloudformation_stacks")
    def list_cloudformation_stacks(self, status_filter: List[str] = None) -> Dict[str, Any]:
        try:
            if not self.session:
                return {"status": "error", "error": "AWS session not available"}
            
            cf = self.session.client('cloudformation')
            
            kwargs = {}
            if status_filter:
                kwargs["StackStatusFilter"] = status_filter
            
            response = cf.list_stacks(**kwargs)
            
            stacks = []
            for stack in response['StackSummaries']:
                stacks.append({
                    "stack_name": stack['StackName'],
                    "stack_status": stack['StackStatus'],
                    "creation_time": stack['CreationTime'].isoformat(),
                    "template_description": stack.get('TemplateDescription', '')
                })
            
            return {
                "status": "success",
                "stacks": stacks,
                "stack_count": len(stacks)
            }
            
        except ClientError as e:
            logger.error("Failed to list CloudFormation stacks", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }