#!/bin/bash

# Deploy with Disk Pressure Tolerance
echo "🚀 Deploying Insurance AI POC with Disk Pressure Tolerance"
echo "=========================================================="

# Delete existing namespace if it exists
kubectl delete namespace insurance-ai-poc --ignore-not-found=true
sleep 5

# Create namespace
echo "📦 Creating namespace..."
kubectl create namespace insurance-ai-poc

# Create API keys secret
echo "🔑 Creating API keys secret..."
kubectl create secret generic api-keys \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  --from-literal=LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY" \
  --from-literal=LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY" \
  --from-literal=LANGFUSE_HOST="$LANGFUSE_HOST" \
  -n insurance-ai-poc

# ConfigMap
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: insurance-ai-poc-config
  namespace: insurance-ai-poc
data:
  ENVIRONMENT: "development"
  LOG_LEVEL: "INFO"
  TECHNICAL_AGENT_URL: "http://insurance-ai-poc-technical-agent:8002"
  POLICY_SERVER_URL: "http://insurance-ai-poc-policy-server:8001"
  DOMAIN_AGENT_URL: "http://insurance-ai-poc-domain-agent:8003"
EOF

# Policy Server with disk pressure tolerance
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insurance-ai-poc-policy-server
  namespace: insurance-ai-poc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: insurance-ai-poc-policy-server
  template:
    metadata:
      labels:
        app: insurance-ai-poc-policy-server
    spec:
      tolerations:
      - key: "node.kubernetes.io/disk-pressure"
        operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: policy-server
        image: insurance-ai-poc:session-fix
        imagePullPolicy: Never
        ports:
        - containerPort: 8001
        command: ["python", "policy_server/main.py"]
        resources:
          requests:
            cpu: 25m
            memory: 32Mi
          limits:
            cpu: 50m
            memory: 64Mi
        envFrom:
        - configMapRef:
            name: insurance-ai-poc-config
---
apiVersion: v1
kind: Service
metadata:
  name: insurance-ai-poc-policy-server
  namespace: insurance-ai-poc
spec:
  selector:
    app: insurance-ai-poc-policy-server
  ports:
  - port: 8001
    targetPort: 8001
EOF

echo "⏳ Waiting for policy server to start..."
sleep 30

# Technical Agent
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insurance-ai-poc-technical-agent
  namespace: insurance-ai-poc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: insurance-ai-poc-technical-agent
  template:
    metadata:
      labels:
        app: insurance-ai-poc-technical-agent
    spec:
      tolerations:
      - key: "node.kubernetes.io/disk-pressure"
        operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: technical-agent
        image: insurance-ai-poc:session-fix
        imagePullPolicy: Never
        ports:
        - containerPort: 8002
        command: ["python", "technical_agent/main.py"]
        resources:
          requests:
            cpu: 25m
            memory: 32Mi
          limits:
            cpu: 50m
            memory: 64Mi
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: OPENROUTER_API_KEY
        envFrom:
        - configMapRef:
            name: insurance-ai-poc-config
---
apiVersion: v1
kind: Service
metadata:
  name: insurance-ai-poc-technical-agent
  namespace: insurance-ai-poc
spec:
  selector:
    app: insurance-ai-poc-technical-agent
  ports:
  - port: 8002
    targetPort: 8002
EOF

echo "⏳ Waiting for technical agent to start..."
sleep 30

# Domain Agent
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insurance-ai-poc-domain-agent
  namespace: insurance-ai-poc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: insurance-ai-poc-domain-agent
  template:
    metadata:
      labels:
        app: insurance-ai-poc-domain-agent
    spec:
      tolerations:
      - key: "node.kubernetes.io/disk-pressure"
        operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: domain-agent
        image: insurance-ai-poc:session-fix
        imagePullPolicy: Never
        ports:
        - containerPort: 8003
        command: ["python", "domain_agent/main.py"]
        resources:
          requests:
            cpu: 25m
            memory: 32Mi
          limits:
            cpu: 50m
            memory: 64Mi
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: OPENROUTER_API_KEY
        envFrom:
        - configMapRef:
            name: insurance-ai-poc-config
---
apiVersion: v1
kind: Service
metadata:
  name: insurance-ai-poc-domain-agent
  namespace: insurance-ai-poc
spec:
  selector:
    app: insurance-ai-poc-domain-agent
  ports:
  - port: 8003
    targetPort: 8003
EOF

echo "⏳ Waiting for domain agent to start..."
sleep 30

# Streamlit UI
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insurance-ai-poc-streamlit-ui
  namespace: insurance-ai-poc
spec:
  replicas: 1
  selector:
    matchLabels:
      app: insurance-ai-poc-streamlit-ui
  template:
    metadata:
      labels:
        app: insurance-ai-poc-streamlit-ui
    spec:
      tolerations:
      - key: "node.kubernetes.io/disk-pressure"
        operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: streamlit-ui
        image: insurance-ai-poc:session-fix
        imagePullPolicy: Never
        ports:
        - containerPort: 8501
        command: ["streamlit", "run", "main_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
        resources:
          requests:
            cpu: 25m
            memory: 32Mi
          limits:
            cpu: 50m
            memory: 64Mi
        envFrom:
        - configMapRef:
            name: insurance-ai-poc-config
---
apiVersion: v1
kind: Service
metadata:
  name: insurance-ai-poc-streamlit-ui
  namespace: insurance-ai-poc
spec:
  selector:
    app: insurance-ai-poc-streamlit-ui
  ports:
  - port: 8501
    targetPort: 8501
EOF

echo "⏳ Final wait for all services..."
sleep 30

echo "📊 Checking final pod status..."
kubectl get pods -n insurance-ai-poc

echo ""
echo "✅ Deployment complete with disk pressure tolerance!"
echo "" 