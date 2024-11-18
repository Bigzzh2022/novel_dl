import re
import os
import logging
import logging.config
import sys
from typing import Optional
from config import LOG_CONFIG

def clean_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    cleaned = re.sub(r'[\\/:*?"<>|]', '', filename)
    cleaned = cleaned.strip()
    return cleaned if cleaned else 'chapter'

def setup_logging():
    """设置日志配置"""
    try:
        # 确保日志目录存在
        log_dir = os.path.dirname(LOG_CONFIG['handlers']['file']['filename'])
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        # 配置日志
        logging.config.dictConfig(LOG_CONFIG)
        logging.info('日志系统初始化成功')
    except Exception as e:
        print(f"设置日志时出错: {str(e)}")
        sys.exit(1)

def ensure_dir(path: str) -> None:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)

def get_chapter_number(filename: str) -> Optional[int]:
    """从文件名中提取章节号"""
    match = re.search(r'(\d+)', os.path.basename(filename))
    return int(match.group(1)) if match else None 