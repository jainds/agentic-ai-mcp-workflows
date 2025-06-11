# 🚀 Deployment Guide: Auto-Versioning & Multi-Image Publishing

## 📋 **Overview**

This guide explains the enhanced CI/CD pipeline with automatic semantic versioning and multi-image publishing to GitHub Container Registry (GHCR).

## 🏗️ **Enhanced Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Push   │───▶│  Auto-Version   │───▶│  Multi-Image    │
│   (main/develop)│    │   Management    │    │     Build       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Git Tagging   │    │ Security Scan   │    │   GHCR Publish  │
│   (v1.2.3)      │    │    (Trivy)      │    │ (multi-platform)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ GitHub Release  │    │   Deploy K8s    │    │   Monitoring    │
│   Generation    │    │ (Staging/Prod)  │    │ & Notifications │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 **Automatic Versioning**

### **Semantic Versioning Rules**
The pipeline automatically determines version bumps based on commit messages:

- **🔥 MAJOR** (`1.0.0` → `2.0.0`): `break`, `breaking`, `major`
- **✨ MINOR** (`1.0.0` → `1.1.0`): `feat`, `feature`, `minor`  
- **🐛 PATCH** (`1.0.0` → `1.0.1`): All other commits

### **Example Commit Messages**
```bash
# Patch release (1.0.0 → 1.0.1)
git commit -m "fix: resolve LiteLLM connection issue"

# Minor release (1.0.0 → 1.1.0) 
git commit -m "feat: add new monitoring dashboard"

# Major release (1.0.0 → 2.0.0)
git commit -m "breaking: change API endpoint structure"
```

### **Manual Version Control**
Override automatic versioning via GitHub Actions:

```yaml
# Manual workflow dispatch
workflow_dispatch:
  inputs:
    version_bump:
      description: 'Version bump type'
      type: choice
      options: [patch, minor, major]
```

## 📦 **Multi-Image Publishing**

### **Published Images**
Two optimized Docker images are built and published:

1. **Main Image**: `ghcr.io/your-org/insurance-ai-poc-main:v1.2.3`
   - Legacy services compatibility
   - Policy server, technical agent, UI
   - Multi-stage build for optimization

2. **ADK Image**: `ghcr.io/your-org/insurance-ai-poc-adk:v1.2.3`
   - Google ADK + LiteLLM + OpenRouter 
   - Customer service, technical, orchestrator agents
   - Optimized for cloud deployment

### **Image Tags Strategy**
```
ghcr.io/your-org/insurance-ai-poc-main:
  ├── v1.2.3              # Semantic version
  ├── latest              # Latest stable (main branch)
  ├── main-abc123f        # Git commit SHA
  ├── 20250610-143022     # Build timestamp
  └── develop-20250610143022  # Pre-release
```

### **Platform Support**
- **linux/amd64** (Intel/AMD x64)
- **linux/arm64** (Apple Silicon, ARM servers)

## 🚀 **Deployment Workflow**

### **Automatic Triggers**
1. **Push to `main`**: Full production pipeline
2. **Push to `develop`**: Staging deployment with pre-release versions
3. **Pull Request**: Build and test only
4. **Manual Trigger**: Custom environment and version control

### **Pipeline Stages**

#### **1. Version Management** 🏷️
```bash
# Determines new version based on:
- Commit messages analysis
- Manual override input
- Branch context (main vs develop)
- Creates git tag and updates pyproject.toml
```

#### **2. Multi-Image Build** 🏗️
```bash
# Parallel matrix build:
- insurance-ai-poc-main (Dockerfile)
- insurance-ai-poc-adk (Dockerfile.adk)
# Features:
- Multi-stage optimization
- Multi-platform support (amd64, arm64)
- Build cache optimization
- Automatic metadata labeling
```

#### **3. Security Scanning** 🔒
```bash
# Trivy vulnerability scanning
- Critical/High vulnerability detection
- SARIF report upload to GitHub Security
- Automated security alerts
```

#### **4. Staging Deployment** 🧪
```bash
# Kubernetes deployment:
- Namespace: insurance-ai-staging
- Replicas: 1 (resource optimized)
- Health checks and monitoring
- E2E test execution
```

#### **5. Production Deployment** 🎯
```bash
# Production deployment (if staging passes):
- Namespace: insurance-ai-production  
- Replicas: 2 (with auto-scaling 2-10)
- Enhanced resource limits
- Rolling deployment strategy
```

#### **6. Release Creation** 📦
```bash
# GitHub Release:
- Automatic changelog generation
- Docker image references
- Deployment instructions
- Version metadata
```

## 🛠️ **Local Usage**

### **Version Management Script**
```bash
# Auto-detect version bump
python scripts/version.py

# Manual version bump
python scripts/version.py --bump minor --update-file

# Generate pre-release version
python scripts/version.py --branch feature/new-agents --prerelease

# JSON output for automation
python scripts/version.py --output-format json --changelog
```

### **Local Docker Builds**
```bash
# Build main image
docker build -f Dockerfile \
  --build-arg VERSION=1.2.3-dev \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse HEAD) \
  -t insurance-ai-poc-main:dev .

# Build ADK image  
docker build -f Dockerfile.adk \
  --build-arg VERSION=1.2.3-dev \
  -t insurance-ai-poc-adk:dev .
```

### **Local Testing**
```bash
# Test version script
python scripts/version.py --changelog

# Test images
docker run --rm insurance-ai-poc-main:dev python --version
docker run --rm insurance-ai-poc-adk:dev cat /app/version.json
```

## 🔧 **Configuration**

### **Required GitHub Secrets**
```bash
# Container Registry
GITHUB_TOKEN                 # Auto-provided

# Kubernetes  
KUBE_CONFIG_STAGING         # Base64-encoded kubeconfig
KUBE_CONFIG_PRODUCTION      # Base64-encoded kubeconfig

# API Keys
OPENROUTER_API_KEY          # OpenRouter API access
OPENAI_API_KEY              # OpenAI API access (backup)
LANGFUSE_SECRET_KEY         # LLM observability
LANGFUSE_PUBLIC_KEY         # LLM observability

# Notifications (optional)
SLACK_WEBHOOK_URL           # Team notifications
```

### **Kubernetes Configuration**
```yaml
# Update Helm values for new images
image:
  repository: ghcr.io/your-org/insurance-ai-poc
  tag: "1.2.3"
  mainImage: ghcr.io/your-org/insurance-ai-poc-main:1.2.3
  adkImage: ghcr.io/your-org/insurance-ai-poc-adk:1.2.3
```

## 🎯 **Usage Examples**

### **Production Release**
```bash
# 1. Create feature branch
git checkout -b feat/new-monitoring-dashboard

# 2. Make changes and commit with semantic message
git commit -m "feat: add comprehensive monitoring dashboard with Grafana integration"

# 3. Push and create PR
git push origin feat/new-monitoring-dashboard

# 4. After PR approval and merge to main:
# ✅ Auto-version bump: 1.0.0 → 1.1.0
# ✅ Git tag created: v1.1.0
# ✅ Images built and published:
#    - ghcr.io/your-org/insurance-ai-poc-main:1.1.0
#    - ghcr.io/your-org/insurance-ai-poc-adk:1.1.0
# ✅ Deployed to staging → E2E tests → Production
# ✅ GitHub Release created with changelog
```

### **Emergency Hotfix**
```bash
# 1. Create hotfix branch from main
git checkout -b hotfix/critical-security-fix

# 2. Apply fix and commit
git commit -m "fix: resolve critical authentication vulnerability"

# 3. Emergency deployment via workflow_dispatch:
#    - Force deploy: true
#    - Environment: production  
#    - Version bump: patch

# Result: 1.1.0 → 1.1.1 with immediate production deployment
```

### **Development Testing**
```bash
# 1. Work on develop branch
git checkout develop
git commit -m "feat: experimental agent coordination"

# 2. Push triggers staging deployment:
# ✅ Version: 1.1.1-develop.20250610143022  
# ✅ Images: insurance-ai-poc-*:1.1.1-develop.20250610143022
# ✅ Deployed to staging only
```

## 📊 **Monitoring & Observability**

### **Pipeline Metrics**
- Build duration and success rates
- Image size optimization
- Security vulnerability trends  
- Deployment success rates
- Test coverage reports

### **Container Metrics**
- Image pull statistics from GHCR
- Multi-platform usage analytics
- Version adoption rates
- Security scan results

### **Notifications**
- Slack integration for deployment status
- GitHub Security alerts for vulnerabilities
- Release notifications with changelogs
- Failed deployment alerts

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Version Script Fails**
```bash
# Check git configuration
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify pyproject.toml exists and has version field
grep 'version = ' pyproject.toml
```

#### **Docker Build Fails**
```bash
# Check build arguments
docker build --build-arg VERSION=test --no-cache .

# Verify multi-platform support
docker buildx create --use
docker buildx inspect --bootstrap
```

#### **Kubernetes Deployment Fails**
```bash
# Check secrets exist
kubectl get secrets -n insurance-ai-staging

# Verify image accessibility  
kubectl run test --image=ghcr.io/your-org/insurance-ai-poc-main:latest --rm -it

# Check resource availability
kubectl describe nodes
```

## 🎉 **Benefits of Enhanced CI/CD**

### **🔄 Automation**
- **Zero-touch versioning**: Semantic versioning based on commit messages
- **Multi-image publishing**: Separate optimized images for different use cases
- **Automatic changelog**: Generated from git commit history
- **Tag management**: Git tags created and managed automatically

### **🔒 Security**
- **Vulnerability scanning**: Trivy security scans on every build
- **Multi-platform support**: ARM64 and AMD64 for security diversity
- **Non-root containers**: Enhanced container security
- **Secret management**: Proper Kubernetes secret handling

### **📦 Distribution**
- **GitHub Container Registry**: Official GitHub integration
- **Multi-architecture**: Support for Intel and ARM processors  
- **Layer optimization**: Multi-stage builds for smaller images
- **Cache optimization**: Faster builds with layer caching

### **🚀 Deployment**
- **Blue-green deployments**: Zero-downtime deployments
- **Auto-scaling**: Production deployments with HPA
- **Health checks**: Comprehensive readiness and liveness probes
- **Rollback capability**: Easy version rollback via Helm

---

## 📚 **Next Steps**

1. **Configure GitHub Secrets**: Add required API keys and kubeconfig
2. **Test Pipeline**: Create a test commit and observe the pipeline
3. **Monitor Deployments**: Check GitHub Container Registry for published images
4. **Configure Notifications**: Set up Slack webhook for team alerts
5. **Review Security**: Monitor security scan results and alerts

For additional support, check the [GitHub Actions workflow logs](../../actions) and [Container Registry packages](../../packages). 