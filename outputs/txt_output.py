import os
import glob
import logging
from typing import Dict
from outputs.base import BaseOutput
from utils.helpers import get_chapter_number

class TxtOutput(BaseOutput):
    """TXT格式输出处理器"""
    
    def convert(self) -> bool:
        """将多个章节文件合并为单个TXT文件"""
        try:
            # 获取所有章节文件并排序
            chapter_files = glob.glob(os.path.join(self.save_dir, '[0-9]*.txt'))
            chapter_files.sort(key=lambda x: get_chapter_number(x) or 0)
            
            if not chapter_files:
                logging.error("没有找到任何章节文件")
                return False
            
            # 合并后的文件路径
            output_path = os.path.join(self.save_dir, f'{self.book_info.get("title", "novel")}_完整版.txt')
            
            # 写入小说信息
            with open(output_path, 'w', encoding='utf-8') as outfile:
                # 写入书籍信息
                info_text = (
                    f"书名：{self.book_info.get('title', '')}\n"
                    f"作者：{self.book_info.get('author', '')}\n"
                    f"状态：{self.book_info.get('status', '')}\n"
                    f"\n简介：\n{self.book_info.get('intro', '')}\n"
                    f"\n{'='*50}\n\n"
                )
                outfile.write(info_text)
                
                # 合并所有章节
                for file_path in chapter_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read().strip()
                            outfile.write(f"{content}\n\n{'='*50}\n\n")
                    except Exception as e:
                        logging.error(f"处理章节文件 {file_path} 时出错: {str(e)}")
                        continue
            
            # 删除原始章节文件
            for file_path in chapter_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"删除章节文件 {file_path} 时出错: {str(e)}")
            
            return True
            
        except Exception as e:
            logging.error(f"生成完整TXT文件失败: {str(e)}")
            return False

    def merge_chapters(self, start_index: int = None, end_index: int = None) -> bool:
        """合并指定范围的章节"""
        try:
            # 获取所有章节文件并排序
            chapter_files = glob.glob(os.path.join(self.save_dir, '[0-9]*.txt'))
            chapter_files.sort(key=lambda x: get_chapter_number(x) or 0)
            
            if not chapter_files:
                logging.error("没有找到任何章节文件")
                return False
            
            # 如果指定了范围，过滤文件列表
            if start_index is not None and end_index is not None:
                chapter_files = [f for f in chapter_files 
                               if start_index <= (get_chapter_number(f) or 0) <= end_index]
            
            if not chapter_files:
                logging.error("指定范围内没有找到任何章节文件")
                return False
            
            # 生成输出文件名
            range_text = f"_{start_index}-{end_index}" if start_index and end_index else ""
            output_path = os.path.join(
                self.save_dir, 
                f'{self.book_info.get("title", "novel")}{range_text}.txt'
            )
            
            # 合并文件
            with open(output_path, 'w', encoding='utf-8') as outfile:
                # 写入书籍信息
                info_text = (
                    f"书名：{self.book_info.get('title', '')}\n"
                    f"作者：{self.book_info.get('author', '')}\n"
                    f"状态：{self.book_info.get('status', '')}\n"
                )
                if start_index and end_index:
                    info_text += f"章节范围：第{start_index}章 - 第{end_index}章\n"
                info_text += (
                    f"\n简介：\n{self.book_info.get('intro', '')}\n"
                    f"\n{'='*50}\n\n"
                )
                outfile.write(info_text)
                
                # 合并所有章节
                for file_path in chapter_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read().strip()
                            outfile.write(f"{content}\n\n{'='*50}\n\n")
                    except Exception as e:
                        logging.error(f"处理章节文件 {file_path} 时出错: {str(e)}")
                        continue
            
            return True
            
        except Exception as e:
            logging.error(f"合并章节失败: {str(e)}")
            return False 