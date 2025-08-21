"""
通知服务
支持邮件、短信、推送等多种通知方式
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """通知提供者抽象基类"""
    
    @abstractmethod
    async def send(self, recipient: str, subject: str, content: str, **kwargs) -> bool:
        """发送通知"""
        pass


class EmailProvider(NotificationProvider):
    """邮件通知提供者"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(self, recipient: str, subject: str, content: str, **kwargs) -> bool:
        """发送邮件"""
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # 添加邮件内容
            content_type = kwargs.get('content_type', 'plain')
            msg.attach(MIMEText(content, content_type))
            
            # 发送邮件
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_email, msg
            )
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False
    
    def _send_email(self, msg):
        """同步发送邮件"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)


class SMSProvider(NotificationProvider):
    """短信通知提供者"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
    
    async def send(self, recipient: str, subject: str, content: str, **kwargs) -> bool:
        """发送短信"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'to': recipient,
                    'message': content,
                    'api_key': self.api_key
                }
                
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"SMS sent successfully to {recipient}")
                        return True
                    else:
                        logger.error(f"Failed to send SMS to {recipient}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {e}")
            return False


class PushProvider(NotificationProvider):
    """推送通知提供者"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
    
    async def send(self, recipient: str, subject: str, content: str, **kwargs) -> bool:
        """发送推送通知"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'user_id': recipient,
                    'title': subject,
                    'body': content,
                    'api_key': self.api_key
                }
                
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Push notification sent successfully to {recipient}")
                        return True
                    else:
                        logger.error(f"Failed to send push notification to {recipient}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send push notification to {recipient}: {e}")
            return False


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.providers = {}
        self._setup_providers()
    
    def _setup_providers(self):
        """设置通知提供者"""
        # 邮件提供者配置
        email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password'
        }
        self.providers['email'] = EmailProvider(**email_config)
        
        # 短信提供者配置
        sms_config = {
            'api_url': 'https://api.sms-provider.com/send',
            'api_key': 'your-sms-api-key'
        }
        self.providers['sms'] = SMSProvider(**sms_config)
        
        # 推送提供者配置
        push_config = {
            'api_url': 'https://api.push-provider.com/send',
            'api_key': 'your-push-api-key'
        }
        self.providers['push'] = PushProvider(**push_config)
    
    async def send_notification(
        self,
        provider_type: str,
        recipient: str,
        subject: str,
        content: str,
        **kwargs
    ) -> bool:
        """发送单个通知"""
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Unknown notification provider: {provider_type}")
            return False
        
        return await provider.send(recipient, subject, content, **kwargs)
    
    async def send_bulk_notification(
        self,
        provider_type: str,
        recipients: List[str],
        subject: str,
        content: str,
        **kwargs
    ) -> Dict[str, bool]:
        """批量发送通知"""
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Unknown notification provider: {provider_type}")
            return {}
        
        results = {}
        tasks = []
        
        for recipient in recipients:
            task = provider.send(recipient, subject, content, **kwargs)
            tasks.append((recipient, task))
        
        # 并发执行所有发送任务
        for recipient, task in tasks:
            try:
                result = await task
                results[recipient] = result
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient}: {e}")
                results[recipient] = False
        
        return results
    
    async def send_multi_channel_notification(
        self,
        channels: List[str],
        recipient_map: Dict[str, str],
        subject: str,
        content: str,
        **kwargs
    ) -> Dict[str, bool]:
        """多渠道发送通知"""
        results = {}
        
        for channel in channels:
            recipient = recipient_map.get(channel)
            if recipient:
                result = await self.send_notification(
                    channel, recipient, subject, content, **kwargs
                )
                results[channel] = result
            else:
                logger.warning(f"No recipient found for channel: {channel}")
                results[channel] = False
        
        return results
    
    def add_provider(self, name: str, provider: NotificationProvider):
        """添加自定义通知提供者"""
        self.providers[name] = provider
    
    def remove_provider(self, name: str):
        """移除通知提供者"""
        if name in self.providers:
            del self.providers[name]


# 全局通知管理器实例
notification_manager = NotificationManager()


# 便捷函数
async def send_email(recipient: str, subject: str, content: str, **kwargs) -> bool:
    """发送邮件的便捷函数"""
    return await notification_manager.send_notification(
        'email', recipient, subject, content, **kwargs
    )


async def send_sms(recipient: str, subject: str, content: str, **kwargs) -> bool:
    """发送短信的便捷函数"""
    return await notification_manager.send_notification(
        'sms', recipient, subject, content, **kwargs
    )


async def send_push(recipient: str, subject: str, content: str, **kwargs) -> bool:
    """发送推送通知的便捷函数"""
    return await notification_manager.send_notification(
        'push', recipient, subject, content, **kwargs
    )
