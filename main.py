import sys
import os
from pathlib import Path
import traceback
import logging

# 将项目根目录添加到 Python 路径
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.helpers import setup_logging
from gui.main_window import MainWindow

def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
def main():
    # 设置日志
    setup_logging()
    
    # 设置全局异常处理
    sys.excepthook = handle_exception
    
    # 确保novels目录存在
    os.makedirs('novels', exist_ok=True)
    
    try:
        # 创建并运行主窗口
        window = MainWindow()
        window.run()
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main() 