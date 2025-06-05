import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from shared.security import audit_log, require_security_check

logger = structlog.get_logger(__name__)

class PrometheusConfig(BaseModel):
    base_url: str = Field(..., description="Prometheus server URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    auth_token: Optional[str] = Field(default=None, description="Authentication token")
    mcp_url: str = Field(default="http://localhost:8000/mcp", description="Prometheus MCP server URL")
    mcp_transport: str = Field(default="streamable_http", description="MCP transport protocol")

class MetricQuery(BaseModel):
    query: str = Field(..., description="PromQL query")
    start_time: Optional[datetime] = Field(default=None, description="Query start time")
    end_time: Optional[datetime] = Field(default=None, description="Query end time")
    step: str = Field(default="15s", description="Query resolution step")

class PrometheusTools:
    def __init__(self, config: PrometheusConfig):
        self.config = config
        self.session = requests.Session()
        if config.auth_token:
            self.session.headers.update({"Authorization": f"Bearer {config.auth_token}"})
    
    @audit_log("prometheus_query")
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def query_prometheus(self, metric_query: str, time_range: Optional[str] = None) -> Dict[str, Any]:
        try:
            params = {"query": metric_query}
            
            if time_range:
                end_time = datetime.now()
                if time_range == "1h":
                    start_time = end_time - timedelta(hours=1)
                elif time_range == "24h":
                    start_time = end_time - timedelta(hours=24)
                elif time_range == "7d":
                    start_time = end_time - timedelta(days=7)
                else:
                    start_time = end_time - timedelta(hours=1)
                
                params.update({
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "step": "15s"
                })
                endpoint = f"{self.config.base_url}/api/v1/query_range"
            else:
                endpoint = f"{self.config.base_url}/api/v1/query"
            
            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info("Prometheus query executed", query=metric_query, status=data.get("status"))
            
            return {
                "status": "success",
                "data": data,
                "query": metric_query,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error("Prometheus query failed", error=str(e), query=metric_query)
            return {
                "status": "error",
                "error": str(e),
                "query": metric_query,
                "timestamp": datetime.now().isoformat()
            }
    
    @audit_log("prometheus_health_check")
    def check_prometheus_health(self) -> Dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.config.base_url}/-/healthy",
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Prometheus health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @audit_log("prometheus_alerts")
    def get_active_alerts(self) -> Dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/v1/alerts",
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            response.raise_for_status()
            
            alerts_data = response.json()
            active_alerts = [
                alert for alert in alerts_data.get("data", {}).get("alerts", [])
                if alert.get("state") == "firing"
            ]
            
            return {
                "status": "success",
                "active_alerts": active_alerts,
                "total_alerts": len(active_alerts),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to retrieve alerts", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def detect_anomalies(self, metric: str, threshold: float = 2.0) -> Dict[str, Any]:
        try:
            query = f"rate({metric}[5m])"
            result = self.query_prometheus(query, "1h")
            
            if result["status"] != "success":
                return result
            
            values = []
            for series in result["data"]["data"]["result"]:
                for value_pair in series.get("values", []):
                    values.append(float(value_pair[1]))
            
            if not values:
                return {"status": "no_data", "message": "No data points found"}
            
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            anomalies = [
                val for val in values[-10:]
                if abs(val - mean_val) > threshold * std_dev
            ]
            
            return {
                "status": "success",
                "anomalies_detected": len(anomalies) > 0,
                "anomaly_count": len(anomalies),
                "threshold": threshold,
                "mean": mean_val,
                "std_dev": std_dev,
                "recent_anomalies": anomalies,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Anomaly detection failed", error=str(e), metric=metric)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }