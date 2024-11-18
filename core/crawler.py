import requests
import logging
import re
import time
import random
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from threading import Lock
from config import BASE_URL, USER_AGENTS
from utils.helpers import clean_filename
import os
from urllib.parse import urlencode
from urllib.parse import quote
from threading import Thread

class Crawler:
    def __init__(self, gui=None):
        self.base_url = BASE_URL
        self.gui = gui
        self.log_lock = Lock()
        self.ua_index = 0

    def get_headers(self) -> Dict[str, str]:
        """获取随机UA"""
        self.ua_index = (self.ua_index + 1) % len(USER_AGENTS)
        return {
            'User-Agent': USER_AGENTS[self.ua_index],
            'Referer': self.base_url
        }

    def log(self, message: str) -> None:
        """线程安全的日志输出"""
        with self.log_lock:
            if self.gui:
                self.gui.log(message)
            logging.info(message)

    def get_novel_info(self, book_id: str) -> Dict:
        """获取小说详细信息"""
        url = f'{self.base_url}/book/{book_id}/'
        try:
            self.log(f"\n获取小说详情: {url}")
            # 增加超时时间，添加重试逻辑
            for retry in range(3):
                try:
                    response = requests.get(
                        url, 
                        headers=self.get_headers(), 
                        timeout=30
                    )
                    response.encoding = 'utf-8'
                    break
                except requests.Timeout:
                    if retry == 2:  # 最后一次重试
                        raise
                    self.log(f"获取超时，第{retry+1}次重试...")
                    time.sleep(2)  # 重试前等待
                    continue
                
            soup = BeautifulSoup(response.text, 'lxml')

            info = {}
            
            # 获取小说标题
            title_elem = soup.find('h1')
            if title_elem:
                info['title'] = title_elem.text.strip()

            # 获取作者等信息
            small_info = soup.find('div', class_='small')
            if small_info:
                spans = small_info.find_all('span')
                for span in spans:
                    text = span.text.strip()
                    if '作者：' in text:
                        info['author'] = text.replace('作者：', '')
                    elif '状态：' in text:
                        # 处理状态信息
                        status = text.replace('状态：', '').strip()
                        # 统一状态显示
                        if '完' in status or '结' in status:
                            info['status'] = '已经完本'
                        else:
                            info['status'] = '连载中'
                    elif '分类：' in text:
                        info['category'] = text.replace('分类：', '')
                    elif '字数：' in text:
                        info['word_count'] = text.replace('字数：', '')
                    elif '更新：' in text:
                        info['update_time'] = text.replace('更新：', '')

            # 获取简介
            intro = soup.find('div', class_='intro')
            if intro:
                info['intro'] = intro.text.strip()

            # 获取最新章节
            latest_chapter = soup.find('div', class_='newest')
            if latest_chapter and latest_chapter.find('a'):
                info['latest_chapter'] = latest_chapter.find('a').text.strip()

            if info:
                self.log(
                    f"\n获取小说详情成功:"
                    f"\n{'='*50}"
                    f"\n书名: {info.get('title', '')}"
                    f"\n作者: {info.get('author', '')}"
                    f"\n状态: {info.get('status', '')}"
                    f"\n分类: {info.get('category', '')}"
                    f"\n字数: {info.get('word_count', '')}"
                    f"\n更新: {info.get('update_time', '')}"
                    f"\n最新: {info.get('latest_chapter', '')}"
                    f"\n简介: {info.get('intro', '')[:100]}..."
                    f"\n{'='*50}"
                )
            else:
                self.log("\n未获取到小说详情")

            return info

        except Exception as e:
            self.log(f"\n获取小说信息失败: {str(e)}")
            return {}

    def get_chapter_list(self, book_id: str) -> List[Dict]:
        """获取小说章节列表"""
        url = f'{self.base_url}/book/{book_id}/'
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            chapter_container = soup.find('div', class_='listmain')
            if not chapter_container:
                self.log("找不到章节列表容器")
                return []

            chapters = []
            for dd in chapter_container.find_all('dd'):
                a_tag = dd.find('a')
                if a_tag and not 'javascript:' in a_tag.get('href', ''):  # 过滤掉展开按钮
                    chapters.append({
                        'title': a_tag.text.strip(),
                        'url': a_tag['href']
                    })

            return chapters

        except Exception as e:
            self.log(f"获取章节列表失败: {str(e)}")
            return []

    def get_chapter_content(self, url: str) -> Optional[str]:
        """获取章节内容"""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            content_div = soup.find('div', id='chaptercontent')
            if not content_div:
                return None

            # 移除不需要的元素
            for elem in content_div.find_all(['p', 'div'], class_='readinline'):
                elem.decompose()

            # 理内容
            content = content_div.get_text('\n', strip=True)
            content = re.sub(r'(www|http:|https:).+?com', '', content)
            content = re.sub(r'笔趣阁.*?最新章节！', '', content)
            content = re.sub(r'手机用户请访问.*?阅读！', '', content)
            content = re.sub(r'请收藏本站.*', '', content)
            content = re.sub(r'『点此报错』', '', content)
            content = re.sub(r'『加入书签』', '', content)
            content = re.sub(r'\s*<br\s*/?>\s*', '\n', content)
            content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)

            return content if content.strip() else None

        except Exception as e:
            self.log(f"获取章节内容失败: {str(e)}")
            return None

    def download_chapter(self, chapter: Dict, save_path: str) -> bool:
        """下载单个章节"""
        if not chapter.get('title') or not chapter.get('url'):
            return False

        try:
            time.sleep(random.uniform(0.5, 1))
            url = f'{self.base_url}{chapter["url"]}'
            content = self.get_chapter_content(url)
            
            if not content:
                return False

            chapter_text = (
                f"{chapter['title']}\n"
                f"{'='*40}\n\n"
                f"{content}\n\n"
                f"{'='*40}\n"
            )

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(chapter_text)

            return True

        except Exception as e:
            self.log(f"下载章节失败: {str(e)}")
            return False

    def search_by_id(self, book_id: str) -> Optional[Dict]:
        """通过书号搜索小说"""
        try:
            self.log(f"正在通过书号搜索: {book_id}")
            novel_info = self.get_novel_info(book_id)
            
            if not novel_info:
                self.log("未找到相关小说")
                return None

            # 构建搜索结果
            result = {
                'title': novel_info.get('title', ''),
                'author': novel_info.get('author', '未知'),
                'book_id': book_id,
                'latest_chapter': novel_info.get('intro', '')[:50] + '...',
                'url': f'/book/{book_id}/'
            }
            
            self.log(f"找到小说：{result['title']}")
            return result

        except Exception as e:
            self.log(f"书号搜索失败: {str(e)}")
            return None

    def search_by_name(self, keyword: str, page: int = 1, page_size: int = 10) -> Dict:
        """通过书名搜索小说，分页返回结果"""
        try:
            self.log(f"开始搜索小说: {keyword} (第{page}页)")
            
            # 1. 先访问搜索页面获取cookie等信息
            search_page_url = f"{self.base_url}/s?q={quote(keyword)}"
            self.log(f"1. 访问搜索页面: {search_page_url}")
            
            session = requests.Session()
            session.headers.update(self.get_headers())
            
            page_response = session.get(search_page_url, timeout=30)
            page_response.encoding = 'utf-8'
            
            # 2. 发送AJAX请求获取搜索结果
            ajax_url = f"{self.base_url}/user/search.html"
            ajax_headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': search_page_url,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Origin': self.base_url
            }
            session.headers.update(ajax_headers)
            
            params = {'q': keyword}
            self.log(f"2. 发送AJAX请求: {ajax_url}")
            self.log(f"请求参数: {params}")
            
            ajax_response = session.get(
                ajax_url,
                params=params,
                timeout=30
            )
            
            try:
                # 尝试解析JSON响应
                results = ajax_response.json()
                if isinstance(results, list):
                    # 计算分页信息
                    total = len(results)
                    total_pages = (total + page_size - 1) // page_size
                    start_idx = (page - 1) * page_size
                    end_idx = min(start_idx + page_size, total)
                    
                    # 获取当前页的数据
                    page_results = results[start_idx:end_idx]
                    
                    novels = []
                    for book in page_results:
                        try:
                            # 构造基本信息，不获取详情
                            novel = {
                                'title': book['articlename'],  # 书名
                                'author': book['author'],      # 作者
                                'intro': book['intro'],        # 简介
                                'url': self.base_url + book['url_list'],  # 完整URL
                                'cover': book['url_img'],      # 封面图片
                                'book_id': book['url_list'].split('/')[-2],  # 书籍ID
                                'source': self.base_url,       # 来源网站
                                'status': '连载中',            # 默认状态
                                'latest_chapter': '',          # 最新章节
                                'category': '',                # 分类
                            }
                            
                            novels.append(novel)
                            self.log(f"找到小说: {novel['title']} - {novel['author']}")
                        except KeyError as e:
                            self.log(f"解析书籍信息时出错: {str(e)}")
                            continue
                    
                    self.log(f"第{page}页: 显示{len(novels)}/{total}本相关小说")
                    
                    # 返回分页信息和结果
                    return {
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': total_pages,
                        'results': novels
                    }
                else:
                    self.log(f"AJAX响应不是列表格式: {results}")
                    return self._empty_result(page, page_size)
                    
            except Exception as e:
                self.log(f"JSON解析失败: {str(e)}")
                return self._empty_result(page, page_size)

        except Exception as e:
            self.log(f"搜索过程发生错误: {str(e)}")
            return self._empty_result(page, page_size)

    def _empty_result(self, page: int, page_size: int) -> Dict:
        """返回空的搜索结果"""
        return {
            'total': 0,
            'page': page,
            'page_size': page_size,
            'total_pages': 0,
            'results': []
        }

    def get_novel_details(self, book_id: str) -> Dict:
        """异步获取小说详细信息"""
        try:
            info = self.get_novel_info(book_id)
            if info:
                return {
                    'status': info.get('status', '连载中'),
                    'latest_chapter': info.get('latest_chapter', ''),
                    'category': info.get('category', ''),
                    'word_count': info.get('word_count', ''),
                    'update_time': info.get('update_time', '')
                }
        except Exception as e:
            self.log(f"获取小说详情失败: {str(e)}")
        return {}

    def search_novel(self, keyword: str, page: int = 1) -> Dict:
        """统一的搜索接口"""
        try:
            # 如果是纯数字，优先尝试书号搜索
            if keyword.isdigit():
                self.log(f"\n开始使用书号搜索: {keyword}")
                result = self.search_by_id(keyword)
                if result:
                    self.log(
                        f"\n书号搜索成功:"
                        f"\n书名: {result['title']}"
                        f"\n作者: {result['author']}"
                        f"\n书号: {keyword}"
                        f"\n最新: {result.get('latest_chapter', '')}"
                    )
                    return {
                        'total': 1,
                        'page': 1,
                        'page_size': 10,
                        'total_pages': 1,
                        'results': [result]
                    }
                self.log("\n书号搜索失败，尝试书名搜索...")

            # 书号搜索失败或不是书号，尝试书名搜索
            self.log(f"\n开始使用书名搜索: {keyword}")
            results = self.search_by_name(keyword, page)
            
            if results['total'] > 0:
                self.log(f"\n书名搜索成功，共找到 {results['total']} 本相关小说")
            else:
                self.log("\n未找到任何相关小说")
            
            return results
            
        except Exception as e:
            self.log(f"\n搜索小说时出错: {str(e)}")
            return self._empty_result(page, 10)

    def parse_search_html(self, html_content: str) -> List[Dict]:
        """解析搜索页面的HTML内容"""
        try:
            self.log("开始解析搜索页面HTML")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找搜索结果容器
            type_show = soup.find('div', class_='type_show')
            if not type_show:
                self.log("未找到搜索结果容器 div.type_show")
                return []
            
            # 检查是否是加载中状态
            loading_div = type_show.find('div', class_='hots')
            if loading_div and '加载中' in loading_div.text:
                self.log("搜索结果正在加载中")
                return []
            
            # 查找所有小说盒子
            book_list = type_show.find_all('div', class_='bookbox')
            if not book_list:
                self.log("未找到任何小说信息")
                return []
            
            self.log(f"找到 {len(book_list)} 个小说")
            
            results = []
            for book in book_list:
                try:
                    book_info = book.find('div', class_='bookinfo')
                    if not book_info:
                        continue
                    
                    title_elem = book_info.find('h4', class_='bookname').find('a')
                    author_elem = book_info.find('div', class_='author')
                    intro_elem = book_info.find('div', class_='uptime')
                    img_elem = book.find('div', class_='bookimg').find('img')
                    
                    if all([title_elem, author_elem, intro_elem, img_elem]):
                        result = {
                            'title': title_elem.text.strip(),
                            'author': author_elem.text.replace('作者：', '').strip(),
                            'intro': intro_elem.text.strip(),
                            'url': title_elem.get('href', ''),
                            'cover': img_elem.get('src', ''),
                            'book_id': title_elem.get('href', '').split('/')[-2] if title_elem.get('href') else ''
                        }
                        results.append(result)
                        self.log(f"找到小说: {result['title']} - {result['author']}")
                
                except Exception as e:
                    self.log(f"解析书籍信息时出错: {str(e)}")
                    continue
                
            return results
            
        except Exception as e:
            self.log(f"解析HTML时出错: {str(e)}")
            return []

    def parse_search_results(self, soup):
        results = []
        book_list = soup.find_all('div', class_='bookbox')
        
        for book in book_list:
            try:
                book_info = {}
                book_info['title'] = book.find('h4', class_='bookname').get_text(strip=True)
                book_info['author'] = book.find('div', class_='author').get_text(strip=True).replace('作者：', '')
                book_info['url'] = book.find('a')['href']
                results.append(book_info)
            except (AttributeError, KeyError) as e:
                self.log(f'解析搜索结果时出错: {str(e)}')
                continue
            
        return results

    def make_request(self, url, method='get', retry_times=3, **kwargs):
        """带重试的请求函数"""
        headers = kwargs.pop('headers', {})
        # 添加必要的请求头
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1'
        })
        kwargs['headers'] = headers
        
        for i in range(retry_times):
            try:
                if method.lower() == 'get':
                    response = requests.get(url, **kwargs)
                else:
                    response = requests.post(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if i == retry_times - 1:  # 最后一次重试
                    raise
                self.log(f'请求失败，正在进行第{i+1}次重试: {str(e)}')
                time.sleep(2)  # 重试前等待

    def search_book(self, book_name):
        self.logger.info(f'正在通过书名搜索: {book_name}')
        
        params = {'q': book_name}
        encoded_params = urlencode(params, encoding='utf-8')
        search_url = f"{self.base_url}/user/search.html?{encoded_params}"
        
        try:
            response = self.make_request(search_url)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = self.parse_search_results(soup)
            
            if not results:
                self.logger.info('未找到任何匹配的小说')
                return None
                
            return results
            
        except Exception as e:
            self.logger.error(f'搜索过程发生错误: {str(e)}')
            return None

    # ... (其他方法保持不变)