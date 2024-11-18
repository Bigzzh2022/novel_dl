import os
import random

# 网站基础URL
BASE_URL = 'https://www.3bqg.cc'

# 搜索相关配置
SEARCH_PATH = '/s'
SEARCH_RESULT_FILENAME = 'search_result.html'
SEARCH_API = '/user/search.html'
SEARCH_RESULT_JSON = 'search_result.json'
SEARCH_RESULT_HTML = 'search_result.html'

# User-Agent 列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/91.0.864.59',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/92.0.902.78',
]

# 请求头配置
def get_random_ua():
    return random.choice(USER_AGENTS)

HEADERS = {
    'User-Agent': get_random_ua(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0'
}

# 调试配置
DEBUG = True  # 是否保存调试信息
DEBUG_DIR = 'debug'  # 调试文件保存目录

# 日志配置
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.getcwd(), 'novel_downloader.log'),
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True
        }
    }
} 