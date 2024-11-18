import os
import glob
import re
from ebooklib import epub
from typing import Dict
from outputs.base import BaseOutput
from utils.helpers import get_chapter_number
import logging

class EpubOutput(BaseOutput):
    def convert(self) -> bool:
        try:
            # 创建epub书籍
            book = epub.EpubBook()

            # 设置书籍元数据
            book.set_identifier(f'novel_{self.book_info.get("title", "unknown")}')
            book.set_title(self.book_info.get('title', 'Unknown Title'))
            book.set_language('zh-CN')
            book.add_author(self.book_info.get('author', 'Unknown Author'))

            # 添加简介
            intro_content = self.book_info.get('intro', '')
            intro = epub.EpubHtml(title='简介', file_name='intro.xhtml', lang='zh-CN')
            intro.content = f'<html><body><h1>简介</h1><p>{intro_content}</p></body></html>'
            book.add_item(intro)

            # 获取所有章节文件并排序
            chapter_files = glob.glob(os.path.join(self.save_dir, '[0-9]*.txt'))
            chapter_files.sort(key=lambda x: get_chapter_number(x) or 0)

            # 创建章节列表
            chapters = []
            spine = ['nav', intro]
            toc = [epub.Link('intro.xhtml', '简介', 'intro')]

            # 处理每个章节
            for i, file_path in enumerate(chapter_files):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # 分离章节标题和内容
                title = content.split('\n')[0]
                text = content.split('='*40)[1].strip()

                # 创建章节
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'chapter_{i+1:04d}.xhtml',
                    lang='zh-CN'
                )

                formatted_text = text.replace("\n", "</p><p>")
                chapter.content = (
                    f'<html><body>'
                    f'<h1>{title}</h1>'
                    f'<p>{formatted_text}</p>'
                    f'</body></html>'
                )

                book.add_item(chapter)
                chapters.append(chapter)
                spine.append(chapter)
                toc.append(
                    epub.Link(f'chapter_{i+1:04d}.xhtml', title, f'chapter_{i+1:04d}')
                )

            # 添加导航信息
            book.toc = toc
            book.spine = spine
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # 添加默认CSS样式
            style = '''
                @namespace epub "http://www.idpf.org/2007/ops";
                body { font-family: SimSun, serif; }
                h1 { text-align: center; padding: 10px; }
                p { text-indent: 2em; line-height: 1.5; margin: 0.5em 0; }
            '''
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/nav.css",
                media_type="text/css",
                content=style
            )
            book.add_item(nav_css)

            # 生成epub文件
            epub_path = os.path.join(self.save_dir, f'{self.book_info.get("title", "novel")}.epub')
            epub.write_epub(epub_path, book, {})

            # 删除原始章节文件
            for file_path in chapter_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"删除章节文件 {file_path} 时出错: {str(e)}")

            return True

        except Exception as e:
            logging.error(f"生成epub文件失败: {str(e)}")
            return False 