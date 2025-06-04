#!/usr/bin/env python3
"""
Flask Web Interface for LangChain/LangGraph Agents

Provides a web-based UI for interacting with Prometheus, Neo4j, and Infrastructure agents.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import asyncio
import traceback
from typing import Dict, Any, Optional
import structlog

from main import AgentManager
from config.settings import get_config

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

logger = structlog.get_logger(__name__)

# Global agent manager instance
agent_manager: Optional[AgentManager] = None

def get_agent_manager() -> AgentManager:
    """Get or create the global agent manager instance."""
    global agent_manager
    if agent_manager is None:
        agent_manager = AgentManager()
    return agent_manager

@app.route('/')
def index():
    """Main page with agent selection and query interface."""
    try:
        manager = get_agent_manager()
        agents_info = manager.list_agents()
        health_status = manager.health_check()
        
        return render_template('index.html', 
                             agents=agents_info['agents'],
                             health_status=health_status)
    except Exception as e:
        logger.error("Failed to load index page", error=str(e))
        flash(f"Error loading page: {str(e)}", 'error')
        return render_template('index.html', agents={}, health_status={})

@app.route('/agent/<agent_name>')
def agent_page(agent_name: str):
    """Individual agent interaction page."""
    try:
        manager = get_agent_manager()
        agents_info = manager.list_agents()
        
        if agent_name not in agents_info['agents']:
            flash(f"Agent '{agent_name}' not found", 'error')
            return redirect(url_for('index'))
        
        agent_info = agents_info['agents'][agent_name]
        health_status = manager.health_check()
        agent_health = health_status.get('agents', {}).get(agent_name, {})
        
        return render_template('agent.html',
                             agent_name=agent_name,
                             agent_info=agent_info,
                             agent_health=agent_health)
    except Exception as e:
        logger.error("Failed to load agent page", agent=agent_name, error=str(e))
        flash(f"Error loading agent page: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for executing agent queries."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
        
        agent_name = data.get('agent')
        query = data.get('query')
        context = data.get('context', {})
        
        if not agent_name or not query:
            return jsonify({"status": "error", "error": "Agent and query are required"}), 400
        
        manager = get_agent_manager()
        result = manager.run_agent(agent_name, query, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("API query failed", error=str(e), traceback=traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/agents')
def api_agents():
    """API endpoint to list all agents."""
    try:
        manager = get_agent_manager()
        agents_info = manager.list_agents()
        return jsonify(agents_info)
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/health')
def api_health():
    """API endpoint for health check."""
    try:
        manager = get_agent_manager()
        health_status = manager.health_check()
        status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
        return jsonify(health_status), status_code
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/form/query', methods=['POST'])
def form_query():
    """Form-based query endpoint for HTML forms."""
    try:
        agent_name = request.form.get('agent')
        query = request.form.get('query')
        context_str = request.form.get('context', '{}')
        
        if not agent_name or not query:
            flash("Agent and query are required", 'error')
            return redirect(url_for('index'))
        
        # Parse context JSON
        try:
            context = json.loads(context_str) if context_str.strip() else {}
        except json.JSONDecodeError:
            flash("Invalid JSON in context field", 'error')
            return redirect(url_for('agent_page', agent_name=agent_name))
        
        manager = get_agent_manager()
        result = manager.run_agent(agent_name, query, context)
        
        # Redirect to agent page with result
        if result.get('status') == 'success':
            flash("Query executed successfully", 'success')
        else:
            flash(f"Query failed: {result.get('error', 'Unknown error')}", 'error')
        
        return render_template('agent.html',
                             agent_name=agent_name,
                             agent_info=manager.list_agents()['agents'][agent_name],
                             agent_health=manager.health_check().get('agents', {}).get(agent_name, {}),
                             query_result=result,
                             last_query=query,
                             last_context=context_str)
        
    except Exception as e:
        logger.error("Form query failed", error=str(e))
        flash(f"Error executing query: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Flask Web Interface for Agents")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Initialize agent manager with config
    if args.config:
        agent_manager = AgentManager(args.config)
    else:
        agent_manager = AgentManager()
    
    logger.info("Starting Flask web interface", host=args.host, port=args.port, debug=args.debug)
    
    app.run(host=args.host, port=args.port, debug=args.debug)