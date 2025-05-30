#!/usr/bin/env python3
"""
Stability Monitoring Script for Insurance AI PoC Streamlit UI
Tracks health, restarts, and stability metrics over time
"""

import subprocess
import requests
import time
import json
import signal
import sys
from datetime import datetime, timedelta
from collections import defaultdict


class StabilityMonitor:
    """Monitor UI stability and track metrics"""
    
    def __init__(self):
        self.base_url = "http://localhost:8501"
        self.namespace = "cursor-insurance-ai-poc"
        self.running = True
        self.metrics = {
            "start_time": datetime.now(),
            "health_checks": {"success": 0, "failure": 0},
            "pod_restarts": defaultdict(int),
            "uptime_periods": [],
            "current_uptime_start": datetime.now()
        }
        
    def check_ui_health(self) -> bool:
        """Check UI health and record metrics"""
        try:
            response = requests.get(f"{self.base_url}/_stcore/health", timeout=10)
            if response.status_code == 200 and response.text.strip() == "ok":
                self.metrics["health_checks"]["success"] += 1
                return True
            else:
                self.metrics["health_checks"]["failure"] += 1
                return False
        except Exception:
            self.metrics["health_checks"]["failure"] += 1
            return False
    
    def check_pod_status(self) -> dict:
        """Check pod status and track restarts"""
        try:
            cmd = ["kubectl", "get", "pods", "-n", self.namespace, "-l", "app=streamlit-ui", "--no-headers"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                pods_info = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            pod_name = parts[0]
                            ready = parts[1]
                            status = parts[2]
                            restarts = int(parts[3])
                            
                            # Track restart count
                            if pod_name not in self.metrics["pod_restarts"]:
                                self.metrics["pod_restarts"][pod_name] = restarts
                            elif restarts > self.metrics["pod_restarts"][pod_name]:
                                print(f"🔄 Pod restart detected: {pod_name} (restart #{restarts})")
                                self.metrics["pod_restarts"][pod_name] = restarts
                                # Record downtime
                                if self.metrics["current_uptime_start"]:
                                    uptime = datetime.now() - self.metrics["current_uptime_start"]
                                    self.metrics["uptime_periods"].append(uptime.total_seconds())
                                    self.metrics["current_uptime_start"] = datetime.now()
                            
                            pods_info.append({
                                "name": pod_name,
                                "ready": ready,
                                "status": status,
                                "restarts": restarts
                            })
                
                return {"pods": pods_info, "healthy": len([p for p in pods_info if "Running" in p["status"]])}
        except Exception as e:
            print(f"❌ Failed to check pods: {e}")
        
        return {"pods": [], "healthy": 0}
    
    def calculate_stability_score(self) -> float:
        """Calculate stability score (0-100)"""
        total_checks = self.metrics["health_checks"]["success"] + self.metrics["health_checks"]["failure"]
        if total_checks == 0:
            return 100.0
        
        success_rate = (self.metrics["health_checks"]["success"] / total_checks) * 100
        
        # Penalty for restarts
        total_restarts = sum(self.metrics["pod_restarts"].values())
        restart_penalty = min(total_restarts * 5, 50)  # Max 50% penalty
        
        return max(success_rate - restart_penalty, 0.0)
    
    def get_average_uptime(self) -> float:
        """Get average uptime between restarts in seconds"""
        if not self.metrics["uptime_periods"]:
            # Current uptime if no restarts
            return (datetime.now() - self.metrics["current_uptime_start"]).total_seconds()
        
        return sum(self.metrics["uptime_periods"]) / len(self.metrics["uptime_periods"])
    
    def print_stability_report(self):
        """Print comprehensive stability report"""
        pods_status = self.check_pod_status()
        ui_healthy = self.check_ui_health()
        stability_score = self.calculate_stability_score()
        avg_uptime = self.get_average_uptime()
        
        print(f"\n📊 Stability Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Overall Health
        health_icon = "✅" if ui_healthy else "❌"
        print(f"{health_icon} UI Health: {'HEALTHY' if ui_healthy else 'UNHEALTHY'}")
        
        # Stability Score
        if stability_score >= 95:
            score_icon = "🟢"
        elif stability_score >= 80:
            score_icon = "🟡"
        else:
            score_icon = "🔴"
        print(f"{score_icon} Stability Score: {stability_score:.1f}%")
        
        # Uptime Stats
        hours, remainder = divmod(avg_uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"⏱️  Average Uptime: {int(hours)}h {int(minutes)}m {int(seconds)}s")
        
        # Pod Status
        print(f"🚀 Pods Status: {pods_status['healthy']}/{len(pods_status['pods'])} healthy")
        for pod in pods_status['pods']:
            status_icon = "✅" if "Running" in pod['status'] else "❌"
            print(f"   {status_icon} {pod['name']}: {pod['status']} ({pod['ready']}) - {pod['restarts']} restarts")
        
        # Health Check Stats
        total_checks = self.metrics["health_checks"]["success"] + self.metrics["health_checks"]["failure"]
        if total_checks > 0:
            success_rate = (self.metrics["health_checks"]["success"] / total_checks) * 100
            print(f"🩺 Health Checks: {self.metrics['health_checks']['success']}/{total_checks} successful ({success_rate:.1f}%)")
        
        # Total Runtime
        runtime = datetime.now() - self.metrics["start_time"]
        runtime_hours, remainder = divmod(runtime.total_seconds(), 3600)
        runtime_minutes, runtime_seconds = divmod(remainder, 60)
        print(f"📅 Monitor Runtime: {int(runtime_hours)}h {int(runtime_minutes)}m {int(runtime_seconds)}s")
        
        # Recommendations
        if stability_score < 80:
            print(f"\n⚠️  Stability Issues Detected:")
            if self.metrics["health_checks"]["failure"] > self.metrics["health_checks"]["success"]:
                print(f"   • High health check failure rate")
            if sum(self.metrics["pod_restarts"].values()) > 3:
                print(f"   • Frequent pod restarts detected")
            print(f"   • Consider checking logs: kubectl logs -l app=streamlit-ui -n {self.namespace}")
        else:
            print(f"\n✅ System is stable and healthy!")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received shutdown signal, generating final report...")
        self.running = False
        self.print_stability_report()
        sys.exit(0)
    
    def monitor_loop(self, check_interval: int = 30):
        """Main monitoring loop"""
        print("🔍 Starting UI Stability Monitor")
        print(f"📡 Check interval: {check_interval} seconds")
        print("Press Ctrl+C to stop and generate report\n")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        while self.running:
            try:
                self.print_stability_report()
                print(f"\n⏰ Next check in {check_interval} seconds...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(5)


def main():
    """Main function"""
    monitor = StabilityMonitor()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            monitor.print_stability_report()
            return
        elif sys.argv[1] == "--test":
            print("🧪 Running 5-minute stability test...")
            monitor.monitor_loop(check_interval=10)
            return
    
    # Default: continuous monitoring
    monitor.monitor_loop()


if __name__ == "__main__":
    main() 