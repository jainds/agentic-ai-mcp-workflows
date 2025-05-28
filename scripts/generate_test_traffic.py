#!/usr/bin/env python3
"""
Generate test traffic for insurance AI system to populate observability dashboards
"""
import requests
import time
import random
import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

class InsuranceTestTrafficGenerator:
    """Generate realistic test traffic for insurance AI system"""
    
    def __init__(self):
        self.base_urls = {
            'support': 'http://localhost:30005',
            'claims': 'http://localhost:30007',
            'ui': 'http://localhost:30009'
        }
        
        self.test_scenarios = {
            'claim_status_inquiries': [
                "What is the status of claim 12345?",
                "Can you check claim 67890 for me?", 
                "I need an update on my claim C-2024-001",
                "Where is my claim in the process?",
                "Has my claim been approved yet?"
            ],
            'claim_filing': [
                "I need to file a new claim for auto damage",
                "My roof was damaged in the storm, I want to file a claim",
                "I had a fender bender yesterday, need to start a claim",
                "Water damage in my basement, please help me file a claim",
                "I need to report property damage from the recent weather"
            ],
            'general_support': [
                "What is my policy coverage?",
                "I need help updating my address",
                "Can you explain my deductible?",
                "How do I add a driver to my policy?",
                "What documents do I need for my claim?"
            ],
            'complex_inquiries': [
                "I have multiple claims and need status on all of them",
                "My claim was denied, can you help me understand why?",
                "I need to speak with someone about my settlement offer",
                "There's an error in my claim details that needs fixing",
                "I want to escalate my claim to a supervisor"
            ]
        }
    
    def make_request(self, service, endpoint, data, delay_range=(1, 3)):
        """Make a single request with random delay"""
        try:
            time.sleep(random.uniform(*delay_range))
            
            url = f"{self.base_urls[service]}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            print(f"🔄 {service.upper()}: {data.get('message', '')[:50]}...")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                print(f"   ✅ Success: {success}")
                return True
            else:
                print(f"   ❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    def generate_support_traffic(self, duration_minutes=10):
        """Generate customer support traffic"""
        print(f"\n🎧 Generating support traffic for {duration_minutes} minutes...")
        
        end_time = time.time() + (duration_minutes * 60)
        request_count = 0
        
        while time.time() < end_time:
            # Random scenario
            scenario = random.choice(list(self.test_scenarios.keys()))
            message = random.choice(self.test_scenarios[scenario])
            customer_id = random.randint(1001, 1050)
            
            data = {
                "message": message,
                "customer_id": customer_id
            }
            
            success = self.make_request('support', '/chat', data)
            request_count += 1
            
            # Random delay between requests
            time.sleep(random.uniform(2, 8))
        
        print(f"   📊 Generated {request_count} support requests")
        return request_count
    
    def generate_claims_traffic(self, duration_minutes=10):
        """Generate claims-specific traffic"""
        print(f"\n📋 Generating claims traffic for {duration_minutes} minutes...")
        
        end_time = time.time() + (duration_minutes * 60)
        request_count = 0
        
        while time.time() < end_time:
            # Mix of claim status and filing
            if random.random() < 0.7:  # 70% status inquiries
                message = random.choice(self.test_scenarios['claim_status_inquiries'])
                claim_id = random.randint(10000, 99999)
                data = {
                    "message": message,
                    "customer_id": random.randint(1001, 1050),
                    "claim_id": claim_id
                }
                endpoint = '/chat'
            else:  # 30% new claim filing
                message = random.choice(self.test_scenarios['claim_filing'])
                data = {
                    "message": message,
                    "customer_id": random.randint(1001, 1050),
                    "claim_details": {
                        "incident_type": random.choice(["auto", "property", "storm", "theft"]),
                        "incident_date": "2024-01-15",
                        "description": message
                    }
                }
                endpoint = '/file-claim'
            
            success = self.make_request('claims', endpoint, data)
            request_count += 1
            
            # Random delay
            time.sleep(random.uniform(1, 5))
        
        print(f"   📊 Generated {request_count} claims requests")
        return request_count
    
    def generate_mixed_load(self, duration_minutes=5):
        """Generate mixed load across all services"""
        print(f"\n🔀 Generating mixed load for {duration_minutes} minutes...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit parallel traffic generation
            futures = [
                executor.submit(self.generate_support_traffic, duration_minutes // 2),
                executor.submit(self.generate_claims_traffic, duration_minutes // 2),
                executor.submit(self.generate_error_scenarios, duration_minutes // 3)
            ]
            
            # Wait for completion
            total_requests = sum(f.result() for f in futures)
        
        print(f"   📊 Total mixed load: {total_requests} requests")
        return total_requests
    
    def generate_error_scenarios(self, duration_minutes=3):
        """Generate some error scenarios for testing alerts"""
        print(f"\n⚠️ Generating error scenarios for {duration_minutes} minutes...")
        
        end_time = time.time() + (duration_minutes * 60)
        request_count = 0
        
        while time.time() < end_time:
            # Generate requests that might cause errors
            scenarios = [
                # Invalid customer IDs
                {"message": "Check my claim", "customer_id": 99999},
                # Malformed requests
                {"message": "", "customer_id": "invalid"},
                # Non-existent claims
                {"message": "Status of claim 000000", "customer_id": 1001},
                # Very long messages (potential timeouts)
                {"message": "x" * 1000, "customer_id": 1001}
            ]
            
            data = random.choice(scenarios)
            service = random.choice(['support', 'claims'])
            endpoint = '/chat'
            
            self.make_request(service, endpoint, data, delay_range=(0.5, 1))
            request_count += 1
            
            time.sleep(random.uniform(3, 7))
        
        print(f"   📊 Generated {request_count} error scenarios")
        return request_count
    
    def run_continuous_load(self):
        """Run continuous background load"""
        print("\n🔄 Starting continuous background load...")
        
        while True:
            try:
                # Light continuous load
                scenario = random.choice(list(self.test_scenarios.keys()))
                message = random.choice(self.test_scenarios[scenario])
                data = {
                    "message": message,
                    "customer_id": random.randint(1001, 1020)
                }
                
                service = random.choice(['support', 'claims'])
                self.make_request(service, '/chat', data, delay_range=(10, 30))
                
                # Long delay between background requests
                time.sleep(random.uniform(30, 120))
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping continuous load...")
                break
            except Exception as e:
                print(f"⚠️ Background load error: {e}")
                time.sleep(60)

def main():
    """Main function to run traffic generation"""
    
    print("🚀 Insurance AI Traffic Generator")
    print("=" * 50)
    print("This will generate test traffic to populate your observability dashboards")
    print("Make sure your services are running at:")
    print("  - Support Agent: http://localhost:30005")
    print("  - Claims Agent: http://localhost:30007")
    print("")
    
    generator = InsuranceTestTrafficGenerator()
    
    try:
        # Generate initial burst of traffic
        print("Phase 1: Initial traffic burst...")
        generator.generate_support_traffic(2)
        generator.generate_claims_traffic(2)
        
        print("\nPhase 2: Mixed load testing...")
        generator.generate_mixed_load(3)
        
        print("\nPhase 3: Error scenario testing...")
        generator.generate_error_scenarios(1)
        
        print("\n✅ Traffic generation complete!")
        print("\n📈 Check your dashboards:")
        print("  - Prometheus: http://localhost:30090")
        print("  - Grafana: http://localhost:30030") 
        print("  - Jaeger: http://localhost:30016")
        print("  - Alertmanager: http://localhost:30093")
        
        print("\n🔄 Starting continuous background load (Ctrl+C to stop)...")
        generator.run_continuous_load()
        
    except KeyboardInterrupt:
        print("\n🛑 Traffic generation stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 