"""
安全相关工具函数
"""
import secrets
import string
import hashlib
import hmac
from typing import Optional


def generate_random_string(length: int = 32, include_punctuation: bool = False) -> str:
    """生成随机字符串"""
    if include_punctuation:
        alphabet = string.ascii_letters + string.digits + string.punctuation
    else:
        alphabet = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key(prefix: str = "sk", length: int = 32) -> str:
    """生成API密钥"""
    random_part = generate_random_string(length)
    return f"{prefix}_{random_part}"


def hash_string(text: str, salt: Optional[str] = None) -> str:
    """使用SHA256对字符串进行哈希"""
    if salt:
        text = f"{text}{salt}"
    return hashlib.sha256(text.encode()).hexdigest()


def verify_hash(text: str, hashed: str, salt: Optional[str] = None) -> bool:
    """验证字符串哈希"""
    return hash_string(text, salt) == hashed


def generate_hmac_signature(message: str, secret: str) -> str:
    """生成HMAC签名"""
    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_hmac_signature(message: str, signature: str, secret: str) -> bool:
    """验证HMAC签名"""
    expected_signature = generate_hmac_signature(message, secret)
    return hmac.compare_digest(signature, expected_signature)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """掩码敏感数据"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def generate_secure_filename(original_filename: str) -> str:
    """生成安全的文件名"""
    import os
    import uuid
    
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)
    
    # 生成UUID作为文件名
    secure_name = str(uuid.uuid4())
    
    return f"{secure_name}{ext}"


class RateLimitTracker:
    """简单的内存限流跟踪器"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求"""
        import time
        
        current_time = int(time.time())
        window_start = current_time - window
        
        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [
                timestamp for timestamp in self.requests[key]
                if timestamp > window_start
            ]
        else:
            self.requests[key] = []
        
        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            return False
        
        # 记录当前请求
        self.requests[key].append(current_time)
        return True
