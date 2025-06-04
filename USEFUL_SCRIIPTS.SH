# Technical agent testing 
curl -X POST http://localhost:8002/tasks/send -H "Content-Type: application/json" -d '{"message": {"content": {"text": "Get policies for customer CUST-001"}}}'

## Domain agent testing
curl -X POST http://localhost:8003/tasks/send -H "Content-Type: application/json" -d '{"message": {"content": {"text": "Customer ID CUST-001, show me my policies and coverage"}}}'

## Logs 
kubectl logs -n insurance-ai-agentic deployment/insurance-ai-poc-domain-agent --tail=20


## Port forwarding 

kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-technical-agent 8002:8002 &
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-domain-agent 8003:8003 &