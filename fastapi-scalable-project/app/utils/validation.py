"""
验证相关工具函数
"""
import re
from typing import Optional, List
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str, country_code: str = "CN") -> bool:
    """验证手机号格式"""
    if country_code == "CN":
        # 中国手机号验证
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    elif country_code == "US":
        # 美国手机号验证
        pattern = r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$'
        return bool(re.match(pattern, phone.replace('-', '').replace(' ', '')))
    else:
        # 通用手机号验证（简单版本）
        pattern = r'^\+?[\d\s\-\(\)]{7,15}$'
        return bool(re.match(pattern, phone))


def validate_url(url: str) -> bool:
    """验证URL格式"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_password_strength(password: str) -> dict:
    """验证密码强度"""
    result = {
        'valid': True,
        'score': 0,
        'messages': []
    }
    
    # 长度检查
    if len(password) < 8:
        result['valid'] = False
        result['messages'].append('密码长度至少8位')
    else:
        result['score'] += 1
    
    # 包含小写字母
    if re.search(r'[a-z]', password):
        result['score'] += 1
    else:
        result['messages'].append('密码应包含小写字母')
    
    # 包含大写字母
    if re.search(r'[A-Z]', password):
        result['score'] += 1
    else:
        result['messages'].append('密码应包含大写字母')
    
    # 包含数字
    if re.search(r'\d', password):
        result['score'] += 1
    else:
        result['messages'].append('密码应包含数字')
    
    # 包含特殊字符
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['score'] += 1
    else:
        result['messages'].append('密码应包含特殊字符')
    
    # 根据得分判断强度
    if result['score'] < 3:
        result['strength'] = 'weak'
        result['valid'] = False
    elif result['score'] < 4:
        result['strength'] = 'medium'
    else:
        result['strength'] = 'strong'
    
    return result


def validate_username(username: str) -> dict:
    """验证用户名"""
    result = {
        'valid': True,
        'messages': []
    }
    
    # 长度检查
    if len(username) < 3:
        result['valid'] = False
        result['messages'].append('用户名长度至少3位')
    elif len(username) > 50:
        result['valid'] = False
        result['messages'].append('用户名长度不能超过50位')
    
    # 字符检查
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        result['valid'] = False
        result['messages'].append('用户名只能包含字母、数字和下划线')
    
    # 不能以数字开头
    if username[0].isdigit():
        result['valid'] = False
        result['messages'].append('用户名不能以数字开头')
    
    return result


def validate_json_schema(data: dict, required_fields: List[str]) -> dict:
    """验证JSON数据结构"""
    result = {
        'valid': True,
        'missing_fields': [],
        'messages': []
    }
    
    for field in required_fields:
        if field not in data:
            result['valid'] = False
            result['missing_fields'].append(field)
            result['messages'].append(f'缺少必需字段: {field}')
    
    return result


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """清理字符串"""
    # 去除首尾空白
    text = text.strip()
    
    # 移除危险字符
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """验证文件扩展名"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in [ext.lower() for ext in allowed_extensions]


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """验证文件大小"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_ip_address(ip: str) -> bool:
    """验证IP地址格式"""
    # IPv4验证
    ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ipv4_pattern, ip):
        return True
    
    # IPv6验证（简单版本）
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    if re.match(ipv6_pattern, ip):
        return True
    
    return False


def validate_credit_card(card_number: str) -> dict:
    """验证信用卡号（Luhn算法）"""
    result = {
        'valid': False,
        'card_type': 'unknown'
    }
    
    # 移除空格和连字符
    card_number = re.sub(r'[\s\-]', '', card_number)
    
    # 检查是否全为数字
    if not card_number.isdigit():
        return result
    
    # 识别卡类型
    if card_number.startswith('4'):
        result['card_type'] = 'visa'
    elif card_number.startswith('5') or card_number.startswith('2'):
        result['card_type'] = 'mastercard'
    elif card_number.startswith('3'):
        result['card_type'] = 'amex'
    
    # Luhn算法验证
    def luhn_check(card_num):
        total = 0
        reverse_digits = card_num[::-1]
        
        for i, char in enumerate(reverse_digits):
            digit = int(char)
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        
        return total % 10 == 0
    
    result['valid'] = luhn_check(card_number)
    return result
