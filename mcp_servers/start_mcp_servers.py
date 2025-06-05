#!/usr/bin/env python3
"""
MCP Servers Startup Script

Starts both Prometheus and Neo4j MCP servers on their respective ports.
Provides process management and graceful shutdown handling.
"""

import asyncio
import signal
import sys
import os
import subprocess
import logging
import time
from typing import List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-servers")

class MCPServerManager:
    """Manages multiple MCP server processes."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
        
        # Get script directory
        self.script_dir = Path(__file__).parent
        
        # Server configurations
        self.servers = [
            {
                "name": "prometheus-mcp",
                "script": self.script_dir / "prometheus_server.py",
                "port": 8000,
                "env_vars": {
                    "MCP_SERVER_PORT": "8000",
                    "MCP_SERVER_NAME": "prometheus-mcp-server"
                }
            },
            {
                "name": "neo4j-mcp", 
                "script": self.script_dir / "neo4j_server.py",
                "port": 8001,
                "env_vars": {
                    "MCP_SERVER_PORT": "8001", 
                    "MCP_SERVER_NAME": "neo4j-mcp-server"
                }
            }
        ]
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start_server(self, server_config: dict) -> Optional[subprocess.Popen]:
        """Start a single MCP server."""
        name = server_config["name"]
        script = server_config["script"]
        port = server_config["port"]
        
        if not script.exists():
            logger.error(f"Server script not found: {script}")
            return None
        
        # Prepare environment
        env = os.environ.copy()
        env.update(server_config.get("env_vars", {}))
        
        try:
            logger.info(f"Starting {name} server on port {port}...")
            
            # Start server process
            process = subprocess.Popen(
                [sys.executable, str(script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give server time to start
            time.sleep(1)
            
            # Check if process started successfully
            if process.poll() is None:
                logger.info(f"{name} server started successfully (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Failed to start {name} server:")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Exception starting {name} server: {e}")
            return None
    
    def start_all_servers(self):
        """Start all MCP servers."""
        logger.info("Starting MCP servers...")
        
        for server_config in self.servers:
            process = self.start_server(server_config)
            if process:
                self.processes.append(process)
            else:
                logger.error(f"Failed to start {server_config['name']} server")
        
        if not self.processes:
            logger.error("No servers started successfully")
            return False
        
        self.running = True
        logger.info(f"Successfully started {len(self.processes)} MCP servers")
        return True
    
    def check_servers(self):
        """Check status of running servers."""
        active_processes = []
        
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                active_processes.append(process)
            else:
                server_name = self.servers[i]["name"]
                logger.warning(f"Server {server_name} (PID: {process.pid}) has stopped")
                
                # Get exit output
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    if stdout:
                        logger.info(f"{server_name} STDOUT: {stdout}")
                    if stderr:
                        logger.error(f"{server_name} STDERR: {stderr}")
                except subprocess.TimeoutExpired:
                    pass
        
        self.processes = active_processes
        return len(self.processes) > 0
    
    def shutdown(self):
        """Shutdown all MCP servers gracefully."""
        if not self.running:
            return
        
        logger.info("Shutting down MCP servers...")
        self.running = False
        
        # Send SIGTERM to all processes
        for i, process in enumerate(self.processes):
            server_name = self.servers[i]["name"]
            
            if process.poll() is None:
                logger.info(f"Terminating {server_name} (PID: {process.pid})...")
                process.terminate()
        
        # Wait for graceful shutdown
        shutdown_timeout = 10
        start_time = time.time()
        
        while self.processes and (time.time() - start_time) < shutdown_timeout:
            remaining_processes = []
            
            for i, process in enumerate(self.processes):
                if process.poll() is None:
                    remaining_processes.append(process)
                else:
                    server_name = self.servers[i]["name"]
                    logger.info(f"{server_name} shut down gracefully")
            
            self.processes = remaining_processes
            
            if self.processes:
                time.sleep(0.5)
        
        # Force kill any remaining processes
        if self.processes:
            logger.warning("Force killing remaining processes...")
            for i, process in enumerate(self.processes):
                server_name = self.servers[i]["name"]
                if process.poll() is None:
                    logger.warning(f"Force killing {server_name} (PID: {process.pid})")
                    process.kill()
                    process.wait()
        
        logger.info("All MCP servers shut down")
    
    def run(self):
        """Run the MCP servers with monitoring."""
        self.setup_signal_handlers()
        
        if not self.start_all_servers():
            logger.error("Failed to start servers")
            return 1
        
        logger.info("MCP servers are running. Press Ctrl+C to stop.")
        
        try:
            # Monitor servers
            while self.running:
                time.sleep(5)  # Check every 5 seconds
                
                if not self.check_servers():
                    logger.error("All servers have stopped")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        
        self.shutdown()
        return 0

def main():
    """Main entry point."""
    # Check for required dependencies
    try:
        import mcp.server.stdio
        import mcp.types
    except ImportError:
        logger.error("MCP packages not found. Install with: pip install mcp")
        return 1
    
    # Check if environment variables are set
    required_env_vars = [
        "PROMETHEUS_URL",
        "NEO4J_URI", 
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Using default values. Consider setting these for production.")
    
    # Start server manager
    manager = MCPServerManager()
    return manager.run()

if __name__ == "__main__":
    sys.exit(main())