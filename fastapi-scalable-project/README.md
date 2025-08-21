# FastAPI 多节点扩展项目框架

这是一个支持多节点扩展的FastAPI项目框架，采用微服务架构设计，支持水平扩展、负载均衡、服务发现等功能。

## 项目特性

- 🚀 **高性能**: 基于FastAPI和异步编程
- 🔄 **水平扩展**: 支持多节点部署和自动扩缩容
- 🎯 **负载均衡**: 内置负载均衡和健康检查
- 🔍 **服务发现**: 支持Consul/Etcd服务注册与发现
- 📊 **监控告警**: 集成Prometheus和Grafana监控
- 🗄️ **数据库**: 支持PostgreSQL/MySQL连接池
- ⚡ **缓存**: Redis分布式缓存
- 📝 **日志**: 结构化日志和链路追踪
- 🔒 **安全**: JWT认证和API限流
- 🐳 **容器化**: Docker和Kubernetes部署

## 项目结构

```
fastapi-scalable-project/
├── app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py            # 应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── dependencies.py    # 依赖注入
│   ├── middleware.py      # 中间件
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py        # 基础模型
│   │   └── user.py        # 用户模型
│   ├── schemas/           # Pydantic模型
│   │   ├── __init__.py
│   │   ├── common.py      # 通用模型
│   │   └── user.py        # 用户模型
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   ├── main.py        # 主路由
│   │   └── routes/        # 具体路由
│   │       ├── __init__.py
│   │       ├── auth.py    # 认证路由
│   │       ├── users.py   # 用户管理
│   │       └── health.py  # 健康检查
│   ├── services/          # 业务逻辑
│   │   ├── __init__.py
│   │   ├── discovery.py   # 服务发现
│   │   └── notification.py # 通知服务
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── security.py    # 安全工具
│       ├── datetime.py    # 时间工具
│       └── validation.py  # 验证工具
├── tests/                 # 测试文件
│   ├── __init__.py
│   └── test_api.py        # API测试
├── docker/                # Docker配置
│   └── nginx.conf         # Nginx配置
├── k8s/                   # Kubernetes配置
│   ├── namespace.yaml     # 命名空间
│   ├── deployment.yaml    # 部署配置
│   ├── service.yaml       # 服务配置
│   ├── configmap.yaml     # 配置映射
│   └── hpa.yaml          # 自动扩缩容
├── monitoring/            # 监控配置
│   └── prometheus.yml     # Prometheus配置
├── scripts/               # 部署脚本
│   └── deploy.sh         # 部署脚本
├── requirements.txt       # Python依赖
├── docker-compose.yml     # 开发环境
├── Dockerfile            # Docker镜像
├── .env.example          # 环境配置示例
└── README.md
```

## 快速开始

### 环境准备

1. **Python 3.12+**
2. **Docker & Docker Compose** (可选)
3. **Kubernetes** (可选)

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd fastapi-scalable-project
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，修改相应配置
```

5. **启动服务**
```bash
# 方式1: 直接运行
python -m app.main

# 方式2: 使用部署脚本
chmod +x scripts/deploy.sh
./scripts/deploy.sh local
```

6. **访问应用**
- 应用首页: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### Docker部署

1. **使用Docker Compose**
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

2. **使用部署脚本**
```bash
./scripts/deploy.sh docker
```

3. **访问服务**
- 应用首页: http://localhost
- API文档: http://localhost/docs
- Grafana监控: http://localhost:3000 (admin/admin)
- Consul UI: http://localhost:8500

### Kubernetes部署

1. **确保Kubernetes集群可用**
```bash
kubectl cluster-info
```

2. **部署应用**
```bash
# 方式1: 直接应用配置
kubectl apply -f k8s/

# 方式2: 使用部署脚本
./scripts/deploy.sh kubernetes
```

3. **检查部署状态**
```bash
kubectl get pods -n fastapi-app
kubectl get services -n fastapi-app
```

## 核心功能

### 用户认证与授权
- JWT令牌认证
- 用户注册/登录
- 权限控制
- 密码加密存储

### 数据库操作
- 异步数据库连接
- 连接池管理
- 数据模型定义
- 数据库迁移

### 缓存系统
- Redis分布式缓存
- 会话存储
- 限流控制

### 服务发现
- Consul集成
- 服务注册与发现
- 健康检查
- 负载均衡

### 监控告警
- Prometheus指标收集
- Grafana可视化
- 应用性能监控
- 自定义指标

### 安全特性
- API限流
- CORS配置
- 安全头设置
- 输入验证

## API接口

### 认证接口
```bash
# 用户注册
POST /api/v1/auth/register

# 用户登录
POST /api/v1/auth/login

# 获取用户信息
GET /api/v1/auth/me

# 修改密码
PUT /api/v1/auth/change-password
```

### 用户管理接口
```bash
# 获取用户列表（管理员）
GET /api/v1/users/

# 创建用户（管理员）
POST /api/v1/users/

# 更新用户信息（管理员）
PUT /api/v1/users/{user_id}

# 删除用户（管理员）
DELETE /api/v1/users/{user_id}

# 更新个人资料
PUT /api/v1/users/profile
```

### 健康检查接口
```bash
# 基础健康检查
GET /health

# 详细健康检查
GET /api/v1/health/detailed

# 存活探针
GET /api/v1/health/liveness

# 就绪探针
GET /api/v1/health/readiness
```

## 扩展部署

### 水平扩展

1. **Docker Compose扩展**
```bash
docker-compose up -d --scale app=3
```

2. **Kubernetes扩展**
```bash
kubectl scale deployment fastapi-app --replicas=5 -n fastapi-app
```

3. **自动扩缩容**
- 基于CPU使用率自动扩缩容
- 基于内存使用率自动扩缩容
- 自定义指标扩缩容

### 负载均衡

- **Nginx负载均衡**: 支持轮询、最少连接等策略
- **Kubernetes Service**: 自动负载均衡
- **Consul Connect**: 服务网格负载均衡

### 配置管理

1. **环境变量配置**
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export REDIS_URL="redis://host:6379/0"
```

2. **配置文件**
```bash
# 修改 .env 文件
vim .env
```

3. **Kubernetes ConfigMap**
```bash
kubectl apply -f k8s/configmap.yaml
```

## 监控告警

### Prometheus指标
- HTTP请求数量和延迟
- 数据库连接池状态
- Redis连接状态
- 应用错误率
- 系统资源使用率

### Grafana仪表板
- 应用性能概览
- 数据库监控
- 缓存监控
- 系统资源监控

### 告警规则
- 应用响应时间过长
- 错误率过高
- 数据库连接失败
- 内存使用率过高

## 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py

# 生成覆盖率报告
pytest --cov=app tests/
```

### 测试类型
- 单元测试
- 集成测试
- API测试
- 性能测试

## 开发指南

### 代码结构
- 遵循SOLID原则
- 使用依赖注入
- 异步编程最佳实践
- 类型提示

### 添加新功能
1. 在`models/`中定义数据模型
2. 在`schemas/`中定义Pydantic模型
3. 在`api/routes/`中添加路由
4. 在`services/`中实现业务逻辑
5. 编写测试用例

### 数据库迁移
```bash
# 生成迁移文件
alembic revision --autogenerate -m "Add new table"

# 执行迁移
alembic upgrade head
```

## 生产部署

### 安全配置
- 修改默认密钥
- 配置HTTPS
- 设置防火墙规则
- 定期更新依赖

### 性能优化
- 启用连接池
- 配置缓存策略
- 优化数据库查询
- 使用CDN

### 备份策略
- 数据库定期备份
- 配置文件备份
- 日志归档

## 故障排除

### 常见问题
1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 检查网络连通性

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证连接配置
   - 检查防火墙设置

3. **服务注册失败**
   - 检查Consul服务状态
   - 验证网络配置
   - 检查服务配置

### 日志查看
```bash
# Docker日志
docker-compose logs -f app

# Kubernetes日志
kubectl logs -f deployment/fastapi-app -n fastapi-app

# 本地日志
tail -f app.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: [您的姓名]
- 邮箱: [您的邮箱]
- 项目地址: [项目URL]
