from abc import ABC, abstractmethod
from typing import Dict

class BaseOutput(ABC):
    """输出格式的基类"""
    
    def __init__(self, save_dir: str, book_info: Dict):
        self.save_dir = save_dir
        self.book_info = book_info

    @abstractmethod
    def convert(self) -> bool:
        """转换文件格式"""
        pass 