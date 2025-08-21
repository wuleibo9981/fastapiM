"""
服务发现服务
支持Consul服务注册与发现
"""
import consul
import asyncio
import logging
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """服务发现管理器"""
    
    def __init__(self):
        self.consul_client = consul.Consul(
            host=settings.consul_host,
            port=settings.consul_port
        )
        self.service_id = settings.service_id
        self.service_name = settings.service_name
        self.is_registered = False
    
    async def register_service(self) -> bool:
        """注册服务到Consul"""
        try:
            # 服务注册信息
            service_info = {
                'name': self.service_name,
                'service_id': self.service_id,
                'address': settings.host,
                'port': settings.port,
                'tags': [
                    f'version-{settings.app_version}',
                    f'environment-{settings.environment}',
                    'fastapi',
                    'python'
                ],
                'check': {
                    'http': f'http://{settings.host}:{settings.port}/health',
                    'interval': f'{settings.health_check_interval}s',
                    'timeout': '5s',
                    'deregister_critical_service_after': '30s'
                },
                'meta': {
                    'version': settings.app_version,
                    'environment': settings.environment,
                    'framework': 'fastapi'
                }
            }
            
            # 注册服务
            self.consul_client.agent.service.register(**service_info)
            self.is_registered = True
            logger.info(f"Service {self.service_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            return False
    
    async def deregister_service(self) -> bool:
        """从Consul注销服务"""
        try:
            self.consul_client.agent.service.deregister(self.service_id)
            self.is_registered = False
            logger.info(f"Service {self.service_id} deregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
            return False
    
    async def discover_services(self, service_name: str) -> List[Dict]:
        """发现指定服务的实例"""
        try:
            _, services = self.consul_client.health.service(
                service_name, 
                passing=True  # 只返回健康的服务
            )
            
            service_instances = []
            for service in services:
                instance = {
                    'service_id': service['Service']['ID'],
                    'address': service['Service']['Address'],
                    'port': service['Service']['Port'],
                    'tags': service['Service']['Tags'],
                    'meta': service['Service']['Meta'],
                    'health': 'passing'
                }
                service_instances.append(instance)
            
            logger.info(f"Discovered {len(service_instances)} instances of {service_name}")
            return service_instances
            
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return []
    
    async def get_service_config(self, key: str) -> Optional[str]:
        """从Consul KV存储获取配置"""
        try:
            _, data = self.consul_client.kv.get(key)
            if data:
                return data['Value'].decode('utf-8')
            return None
            
        except Exception as e:
            logger.error(f"Failed to get config {key}: {e}")
            return None
    
    async def set_service_config(self, key: str, value: str) -> bool:
        """设置配置到Consul KV存储"""
        try:
            result = self.consul_client.kv.put(key, value)
            logger.info(f"Config {key} set successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    async def watch_service_changes(self, service_name: str, callback):
        """监听服务变化"""
        index = None
        while True:
            try:
                index, services = self.consul_client.health.service(
                    service_name,
                    index=index,
                    wait='10s'
                )
                
                # 调用回调函数处理服务变化
                if callback:
                    await callback(services)
                    
            except Exception as e:
                logger.error(f"Error watching service changes: {e}")
                await asyncio.sleep(5)  # 错误时等待5秒重试
    
    async def health_check(self) -> bool:
        """检查Consul连接健康状态"""
        try:
            # 尝试获取服务列表来测试连接
            self.consul_client.agent.services()
            return True
        except Exception as e:
            logger.error(f"Consul health check failed: {e}")
            return False


# 全局服务发现实例
service_discovery = ServiceDiscovery()


class LoadBalancer:
    """简单的负载均衡器"""
    
    def __init__(self):
        self.service_instances = {}
        self.current_index = {}
    
    def update_instances(self, service_name: str, instances: List[Dict]):
        """更新服务实例列表"""
        self.service_instances[service_name] = instances
        if service_name not in self.current_index:
            self.current_index[service_name] = 0
    
    def get_instance(self, service_name: str, strategy: str = "round_robin") -> Optional[Dict]:
        """获取服务实例"""
        instances = self.service_instances.get(service_name, [])
        if not instances:
            return None
        
        if strategy == "round_robin":
            # 轮询策略
            index = self.current_index[service_name]
            instance = instances[index]
            self.current_index[service_name] = (index + 1) % len(instances)
            return instance
        
        elif strategy == "random":
            # 随机策略
            import random
            return random.choice(instances)
        
        else:
            # 默认返回第一个
            return instances[0]


# 全局负载均衡器实例
load_balancer = LoadBalancer()
