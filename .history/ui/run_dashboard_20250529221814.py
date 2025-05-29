#!/usr/bin/env python3
"""
Insurance AI PoC Dashboard Runner
Configurable startup script for the Streamlit dashboard
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

def setup_environment(args):
    """Setup environment variables from command line arguments"""
    
    # Service URLs
    if args.claims_agent:
        os.environ["CLAIMS_AGENT_URL"] = args.claims_agent
    if args.data_agent:
        os.environ["DATA_AGENT_URL"] = args.data_agent
    if args.notification_agent:
        os.environ["NOTIFICATION_AGENT_URL"] = args.notification_agent
    
    # Dashboard configuration
    if args.host:
        os.environ["DASHBOARD_HOST"] = args.host
    if args.port:
        os.environ["DASHBOARD_PORT"] = str(args.port)
    
    # Feature flags
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
    if args.auto_refresh:
        os.environ["ENABLE_AUTO_REFRESH"] = "true"
    
    # Development mode
    if args.dev:
        os.environ["DEBUG_MODE"] = "true"
        os.environ["ENABLE_AUTO_REFRESH"] = "true"
        os.environ["FEATURE_QUICK_ACTIONS"] = "true"
        os.environ["FEATURE_LLM_THINKING"] = "true"


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "streamlit",
        "requests", 
        "pandas",
        "plotly"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements-streamlit.txt")
        return False
    
    return True


def run_streamlit(args):
    """Run the Streamlit dashboard"""
    dashboard_file = Path(__file__).parent / "streamlit_dashboard.py"
    
    # Build streamlit command
    cmd = [
        "streamlit", "run", str(dashboard_file),
        "--server.port", str(args.port),
        "--server.address", args.host
    ]
    
    # Add development flags
    if args.dev:
        cmd.extend([
            "--server.runOnSave", "true",
            "--server.fileWatcherType", "poll"
        ])
    
    # Run streamlit
    print(f"🚀 Starting Insurance AI PoC Dashboard...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"🔧 Claims Agent: {os.getenv('CLAIMS_AGENT_URL', 'http://claims-agent:8000')}")
    print(f"🔧 Data Agent: {os.getenv('DATA_AGENT_URL', 'http://data-agent:8002')}")
    print(f"🔧 Notification Agent: {os.getenv('NOTIFICATION_AGENT_URL', 'http://notification-agent:8003')}")
    print("---")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running dashboard: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Insurance AI PoC Dashboard Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python run_dashboard.py
  
  # Custom configuration
  python run_dashboard.py --port 8502 --host 0.0.0.0 \\
      --claims-agent http://192.168.1.100:8000 \\
      --data-agent http://192.168.1.101:8002
  
  # Development mode
  python run_dashboard.py --dev
  
  # With debugging
  python run_dashboard.py --debug --auto-refresh
        """
    )
    
    # Dashboard configuration
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Dashboard host address (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8501,
        help="Dashboard port (default: 8501)"
    )
    
    # Service URLs
    parser.add_argument(
        "--claims-agent",
        help="Claims Agent URL (default: http://claims-agent:8000)"
    )
    parser.add_argument(
        "--data-agent", 
        help="Data Agent URL (default: http://data-agent:8002)"
    )
    parser.add_argument(
        "--notification-agent",
        help="Notification Agent URL (default: http://notification-agent:8003)"
    )
    
    # Feature flags
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--auto-refresh",
        action="store_true", 
        help="Enable auto-refresh"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode (enables debug, auto-refresh, and file watching)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment(args)
    
    # Run dashboard
    run_streamlit(args)


if __name__ == "__main__":
    main() 