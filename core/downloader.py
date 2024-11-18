import os
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from utils.helpers import clean_filename, ensure_dir
from core.crawler import Crawler
from outputs.epub_output import EpubOutput
from outputs.txt_output import TxtOutput
import time
import tkinter as tk

class Downloader:
    def __init__(self, crawler: Crawler):
        self.crawler = crawler
        self.download_count = 0
        self.total_chapters = 0
        self.download_lock = Lock()
        self.is_downloading = False

    def update_progress(self) -> None:
        """更新下载进度"""
        with self.download_lock:
            self.download_count += 1
            if self.crawler.gui:
                self.crawler.gui.update_progress(self.download_count, self.total_chapters)

    def download_chapters(self, book_id: str, chapters: List[Dict], save_dir: str,
                        start_index: int, thread_num: int = 3) -> List[Dict]:
        """下载多个章节"""
        failed_chapters = []
        
        with ThreadPoolExecutor(max_workers=thread_num) as executor:
            future_to_chapter = {}
            
            for i, chapter in enumerate(chapters):
                chapter_index = start_index + i
                save_path = os.path.join(
                    save_dir,
                    f"{chapter_index:04d}-{clean_filename(chapter['title'])}.txt"
                )
                
                self.crawler.log(f"正在下载: {chapter['title']}")
                future = executor.submit(
                    self.crawler.download_chapter,
                    chapter,
                    save_path
                )
                future_to_chapter[future] = chapter

            for future in as_completed(future_to_chapter):
                chapter = future_to_chapter[future]
                try:
                    success = future.result()
                    if not success:
                        failed_chapters.append(chapter)
                        self.crawler.log(f"下载失败: {chapter['title']}")
                    else:
                        self.crawler.log(f"下载成功: {chapter['title']}")
                    self.update_progress()
                except Exception as e:
                    self.crawler.log(f"下载章节 {chapter['title']} 时发生错误: {str(e)}")
                    failed_chapters.append(chapter)

                if not self.is_downloading:
                    executor.shutdown(wait=False)
                    break

        if failed_chapters:
            self.crawler.log(f"\n下载完成，共 {len(failed_chapters)} 个章节下载失败")
        else:
            self.crawler.log("\n所有章节下载成功！")

        return failed_chapters

    def retry_failed_chapters(self, book_id: str, failed_chapters: List[Dict], save_dir: str, thread_num: int = 1) -> List[Dict]:
        """单线程重试失败的章节"""
        still_failed = []
        self.crawler.log("\n开始重试失败章节...")
        
        # 按章节序号排序
        def get_chapter_number(chapter):
            # 从文件名中提取章节序号
            filename = os.path.basename(chapter.get('save_path', ''))
            try:
                # 提取文件名开头的数字部分
                number = int(filename.split('-')[0])
                return number
            except:
                return 0
        
        # 对失败章节按序号排序
        sorted_chapters = sorted(failed_chapters, key=get_chapter_number)
        
        for chapter in sorted_chapters:
            if not self.is_downloading:
                break
            
            try:
                self.crawler.log(f"重试下载: {chapter['title']}")
                success = self.crawler.download_chapter(chapter, chapter['save_path'])
                
                if not success:
                    still_failed.append(chapter)
                    self.crawler.log(f"重试失败: {chapter['title']}")
                else:
                    self.crawler.log(f"重试成功: {chapter['title']}")
                    
                self.update_progress()
                
            except Exception as e:
                self.crawler.log(f"重试章节时出错: {str(e)}")
                still_failed.append(chapter)
                
            time.sleep(1)  # 避免请求过快

        if still_failed:
            self.crawler.log(f"\n重试完成，仍有 {len(still_failed)} 个章节下载失败")
            # 保存仍然失败的章节信息
            self.save_failed_chapters(save_dir, still_failed)
        else:
            self.crawler.log("\n所有失败章节重试成功！")
            # 删除失败章节记录文件
            failed_file = os.path.join(save_dir, 'failed_chapters.txt')
            if os.path.exists(failed_file):
                os.remove(failed_file)
            
        return still_failed

    def start_download(self, book_id: str, start_chapter: int = 1, end_chapter: Optional[int] = None,
                      thread_num: int = 3, output_format: str = "txt") -> bool:
        """开始下载小说"""
        try:
            self.is_downloading = True
            self.download_count = 0

            # 获取小说信息
            novel_info = self.crawler.get_novel_info(book_id)
            if not novel_info:
                self.crawler.log("获取小说信息失败！")
                return False

            # 获取章节列表
            all_chapters = self.crawler.get_chapter_list(book_id)
            if not all_chapters:
                self.crawler.log("获取章节列表失败！")
                return False

            # 确定下载范围
            if end_chapter is None:
                end_chapter = len(all_chapters)
            end_chapter = min(end_chapter, len(all_chapters))
            
            if start_chapter > end_chapter:
                self.crawler.log("起始章节不能大于结束章节")
                return False

            # 获取需要下载的章节
            chapters = all_chapters[start_chapter-1:end_chapter]
            self.total_chapters = len(chapters)
            self.crawler.log(f"\n开始下载《{novel_info.get('title', '')}》")
            self.crawler.log(f"共 {self.total_chapters} 章，使用 {thread_num} 个线程下载\n")

            # 创建保存目录
            novel_title = clean_filename(novel_info['title'])
            save_dir = os.path.join('novels', novel_title)
            ensure_dir(save_dir)

            # 保存小说信息
            self.save_novel_info(save_dir, novel_info, start_chapter, end_chapter)

            # 为每个章节添加保存路径
            for i, chapter in enumerate(chapters):
                chapter_index = start_chapter + i
                chapter['save_path'] = os.path.join(
                    save_dir,
                    f"{chapter_index:04d}-{clean_filename(chapter['title'])}.txt"
                )

            # 下载章节
            failed_chapters = self.download_chapters(book_id, chapters, save_dir, start_chapter, thread_num)

            # 处理失败章节
            if failed_chapters:
                self.save_failed_chapters(save_dir, failed_chapters)
                self.crawler.log(f"\n失败章节已保存到: {os.path.join(save_dir, 'failed_chapters.txt')}")
                
                # 询问是否要重试
                if self.crawler.gui and self.crawler.gui.ask_retry():
                    # 单线程重试失败章节
                    failed_chapters = self.retry_failed_chapters(book_id, failed_chapters, save_dir)

            # 只有在没有失败章节或用户选择不重试的情况下才进行格式转换
            if not failed_chapters and self.is_downloading:
                # 转换格式
                if output_format != "txt":
                    self.crawler.log("\n正在转换为EPUB格式...")
                    converter = EpubOutput(save_dir, novel_info)
                    if converter.convert():
                        self.crawler.log("EPUB转换完成")
                    else:
                        self.crawler.log("EPUB转换失败")
                else:
                    self.crawler.log("\n正在合并TXT文件...")
                    converter = TxtOutput(save_dir, novel_info)
                    if converter.convert():
                        self.crawler.log("TXT合并完成")
                    else:
                        self.crawler.log("TXT合并失败")

                if self.is_downloading:
                    self.crawler.log(f"\n下载完成！文件保存在：{os.path.abspath(save_dir)}")
            else:
                self.crawler.log("\n由于存在下载失败的章节，跳过格式转换")

            return True

        except Exception as e:
            self.crawler.log(f"下载过程出错: {str(e)}")
            return False
        finally:
            self.is_downloading = False

    def save_novel_info(self, save_dir: str, novel_info: Dict, start_chapter: int, end_chapter: int) -> None:
        """保存小说信息"""
        info_text = (
            f"书名：{novel_info.get('title', '')}\n"
            f"作者：{novel_info.get('author', '')}\n"
            f"状态：{novel_info.get('status', '')}\n"
            f"简介：\n{novel_info.get('intro', '')}\n"
            f"下载章节：第{start_chapter}章 - 第{end_chapter}章\n"
        )
        info_path = os.path.join(save_dir, 'info.txt')
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(info_text)

    def save_failed_chapters(self, save_dir: str, failed_chapters: List[Dict]) -> None:
        """保存失败章节信息"""
        failed_path = os.path.join(save_dir, 'failed_chapters.txt')
        with open(failed_path, 'w', encoding='utf-8') as f:
            # 按章节序号排序后保存
            sorted_chapters = sorted(failed_chapters, 
                                   key=lambda x: int(os.path.basename(x['save_path']).split('-')[0]))
            for chapter in sorted_chapters:
                f.write(f"{chapter['title']}\t{chapter['url']}\t{chapter['save_path']}\n")

    def resume_download(self, book_id: str, current_progress: int, thread_num: int, output_format: str):
        """继续下载
        
        Args:
            book_id: 书号
            current_progress: 当前进度
            thread_num: 线程数
            output_format: 输出格式
        """
        # 获取章节列表
        chapters = self.crawler.get_chapter_list(book_id)
        if not chapters:
            return
        
        # 从当前进度继续下载
        remaining_chapters = chapters[current_progress:]
        self.start_download(book_id, current_progress + 1, len(chapters), 
                           thread_num, output_format, chapters=remaining_chapters)
  