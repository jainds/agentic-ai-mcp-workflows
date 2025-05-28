#!/usr/bin/env python3
"""
Script to add /metrics endpoints to all agent files
"""

import os
import re

def add_metrics_endpoint(file_path):
    """Add metrics endpoint to an agent file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if metrics endpoint already exists
    if '@app.get("/metrics")' in content:
        print(f"Metrics endpoint already exists in {file_path}")
        return False
    
    # Find the @app.get("/skills") endpoint and add metrics after it
    skills_pattern = r'(\s+@app\.get\("/skills"\)\s+async def get_skills\(\):[^@]+return[^\n]+)'
    
    replacement = r'''\1
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        metrics_data = await agent_server.handle_metrics_request()
        from fastapi import Response
        return Response(content=metrics_data, media_type="text/plain")'''
    
    new_content = re.sub(skills_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Added metrics endpoint to {file_path}")
        return True
    else:
        print(f"Could not find skills endpoint pattern in {file_path}")
        return False

def main():
    # Agent files to update
    agent_files = [
        'agents/domain/claims_domain_agent.py',
        'agents/technical/claims_agent.py',
        'agents/technical/policy_agent.py',
        'agents/technical/customer_agent.py'
    ]
    
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            add_metrics_endpoint(agent_file)
        else:
            print(f"File not found: {agent_file}")

if __name__ == "__main__":
    main() 