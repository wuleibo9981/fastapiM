#!/bin/bash

# FastAPI多节点扩展项目部署脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 部署模式
DEPLOY_MODE=${1:-"docker"}
ENVIRONMENT=${2:-"development"}

log_info "开始部署 FastAPI 多节点扩展项目"
log_info "部署模式: $DEPLOY_MODE"
log_info "环境: $ENVIRONMENT"

case $DEPLOY_MODE in
    "docker")
        log_info "使用 Docker Compose 部署..."
        
        # 检查依赖
        check_command docker
        check_command docker-compose
        
        # 构建和启动服务
        log_info "构建 Docker 镜像..."
        docker-compose build
        
        log_info "启动服务..."
        docker-compose up -d
        
        # 等待服务启动
        log_info "等待服务启动..."
        sleep 30
        
        # 健康检查
        log_info "执行健康检查..."
        if curl -f http://localhost/health > /dev/null 2>&1; then
            log_info "✅ 应用部署成功！"
            log_info "访问地址: http://localhost"
            log_info "API文档: http://localhost/docs"
            log_info "Grafana监控: http://localhost:3000 (admin/admin)"
            log_info "Consul UI: http://localhost:8500"
        else
            log_error "❌ 应用健康检查失败"
            docker-compose logs app
            exit 1
        fi
        ;;
        
    "kubernetes")
        log_info "使用 Kubernetes 部署..."
        
        # 检查依赖
        check_command kubectl
        
        # 应用配置
        log_info "创建命名空间..."
        kubectl apply -f k8s/namespace.yaml
        
        log_info "应用配置..."
        kubectl apply -f k8s/configmap.yaml
        
        log_info "部署应用..."
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        kubectl apply -f k8s/hpa.yaml
        
        # 等待部署完成
        log_info "等待部署完成..."
        kubectl rollout status deployment/fastapi-app -n fastapi-app
        
        # 获取服务信息
        log_info "获取服务信息..."
        kubectl get services -n fastapi-app
        
        log_info "✅ Kubernetes 部署完成！"
        ;;
        
    "local")
        log_info "本地开发模式部署..."
        
        # 检查Python环境
        check_command python3
        check_command pip
        
        # 安装依赖
        log_info "安装 Python 依赖..."
        pip install -r requirements.txt
        
        # 设置环境变量
        export ENVIRONMENT=development
        export DATABASE_URL=sqlite:///./dev.db
        export REDIS_URL=redis://localhost:6379/0
        
        # 启动应用
        log_info "启动应用..."
        python -m app.main &
        APP_PID=$!
        
        # 等待启动
        sleep 5
        
        # 健康检查
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "✅ 本地应用启动成功！"
            log_info "访问地址: http://localhost:8000"
            log_info "API文档: http://localhost:8000/docs"
            log_info "PID: $APP_PID"
        else
            log_error "❌ 应用启动失败"
            kill $APP_PID 2>/dev/null || true
            exit 1
        fi
        ;;
        
    *)
        log_error "不支持的部署模式: $DEPLOY_MODE"
        log_info "支持的模式: docker, kubernetes, local"
        exit 1
        ;;
esac

log_info "部署完成！"
