"""
时间相关工具函数
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import time


def get_current_timestamp() -> float:
    """获取当前时间戳"""
    return time.time()


def get_current_datetime() -> datetime:
    """获取当前UTC时间"""
    return datetime.utcnow()


def get_current_datetime_with_timezone() -> datetime:
    """获取带时区的当前时间"""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    return dt.strftime(format_string)


def parse_datetime(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析日期时间字符串"""
    return datetime.strptime(date_string, format_string)


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """时间戳转换为datetime对象"""
    return datetime.fromtimestamp(timestamp, timezone.utc)


def datetime_to_timestamp(dt: datetime) -> float:
    """datetime对象转换为时间戳"""
    return dt.timestamp()


def add_timezone(dt: datetime, tz: timezone = timezone.utc) -> datetime:
    """为naive datetime添加时区信息"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt


def is_expired(dt: datetime, expiry_minutes: int = 30) -> bool:
    """检查时间是否已过期"""
    if dt.tzinfo is None:
        dt = add_timezone(dt)
    
    expiry_time = dt + timedelta(minutes=expiry_minutes)
    current_time = get_current_datetime_with_timezone()
    
    return current_time > expiry_time


def time_until_expiry(dt: datetime, expiry_minutes: int = 30) -> Optional[timedelta]:
    """计算距离过期还有多长时间"""
    if dt.tzinfo is None:
        dt = add_timezone(dt)
    
    expiry_time = dt + timedelta(minutes=expiry_minutes)
    current_time = get_current_datetime_with_timezone()
    
    if current_time >= expiry_time:
        return None  # 已过期
    
    return expiry_time - current_time


def get_date_range(start_date: datetime, end_date: datetime) -> list:
    """获取日期范围内的所有日期"""
    dates = []
    current_date = start_date.date()
    end_date = end_date.date()
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates


def get_week_start_end(dt: datetime) -> tuple:
    """获取指定日期所在周的开始和结束日期"""
    # 获取周一作为一周的开始
    days_since_monday = dt.weekday()
    week_start = dt - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    return week_start.date(), week_end.date()


def get_month_start_end(dt: datetime) -> tuple:
    """获取指定日期所在月的开始和结束日期"""
    # 月初
    month_start = dt.replace(day=1)
    
    # 月末
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    
    month_end = next_month - timedelta(days=1)
    
    return month_start.date(), month_end.date()


def humanize_timedelta(td: timedelta) -> str:
    """人性化显示时间差"""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}秒"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}分钟"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}小时"
    else:
        days = total_seconds // 86400
        return f"{days}天"


def is_business_day(dt: datetime) -> bool:
    """检查是否为工作日（周一到周五）"""
    return dt.weekday() < 5


def get_next_business_day(dt: datetime) -> datetime:
    """获取下一个工作日"""
    next_day = dt + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day
