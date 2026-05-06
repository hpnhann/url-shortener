#!/bin/bash
# ── deploy-k8s.sh — Deploy URL Shortener lên Minikube ───────
# Chạy: bash scripts/deploy-k8s.sh

set -e

echo "🚀 Deploying URL Shortener to Kubernetes..."
echo ""

# ── Bước 1: Bật Ingress addon trong Minikube ────────────────
echo "📦 Enabling Ingress addon..."
minikube addons enable ingress
minikube addons enable metrics-server   # cần cho HPA

# ── Bước 2: Dùng Docker registry của Minikube ───────────────
# Thay vì pull từ Docker Hub, build thẳng vào Minikube
echo "🐳 Pointing Docker to Minikube registry..."
eval $(minikube docker-env)

# ── Bước 3: Build image vào Minikube ────────────────────────
echo "🔨 Building image inside Minikube..."
docker build -t url-shortener-app:local ./app

# ── Bước 4: Apply tất cả K8s config ─────────────────────────
echo "📋 Applying Kubernetes manifests..."
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap-secret.yaml
kubectl apply -f k8s/base/postgres.yaml
kubectl apply -f k8s/base/redis.yaml
kubectl apply -f k8s/base/app.yaml
kubectl apply -f k8s/base/ingress.yaml

# ── Bước 5: Đợi deployment sẵn sàng ─────────────────────────
echo ""
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=120s \
    deployment/postgres -n url-shortener
kubectl wait --for=condition=available --timeout=120s \
    deployment/redis -n url-shortener
kubectl wait --for=condition=available --timeout=120s \
    deployment/url-shortener-app -n url-shortener

# ── Bước 6: Thêm vào hosts file ─────────────────────────────
MINIKUBE_IP=$(minikube ip)
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Add this to your hosts file:"
echo "   Windows: C:\\Windows\\System32\\drivers\\etc\\hosts"
echo "   Linux/Mac: /etc/hosts"
echo ""
echo "   $MINIKUBE_IP  url-shortener.local"
echo ""
echo "🌐 Then open: http://url-shortener.local"
echo ""
echo "📊 Useful commands:"
echo "   kubectl get pods -n url-shortener"
echo "   kubectl get services -n url-shortener"
echo "   kubectl logs -f deployment/url-shortener-app -n url-shortener"
