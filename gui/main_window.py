import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from typing import Optional
from core.crawler import Crawler
from core.downloader import Downloader
import os

class SearchDialog(tk.Toplevel):
    """搜索对话框"""
    def __init__(self, parent, crawler):
        super().__init__(parent)
        self.title("搜索小说")
        self.crawler = crawler
        self.selected_book_id = None
        
        # 设置窗口大小和位置
        window_width = 600
        window_height = 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 搜索框架
        search_frame = ttk.Frame(self, padding="10")
        search_frame.pack(fill=tk.X)
        
        # 搜索输入
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 搜索按钮
        search_btn = ttk.Button(search_frame, text="搜索", command=self._do_search)
        search_btn.pack(side=tk.RIGHT)
        
        # 搜索结果列表
        columns = ('title', 'author', 'latest_chapter', 'book_id')
        self.result_tree = ttk.Treeview(self, columns=columns, show='headings', padding="10")
        
        # 设置列标题
        self.result_tree.heading('title', text='书名')
        self.result_tree.heading('author', text='作者')
        self.result_tree.heading('latest_chapter', text='最新章节')
        self.result_tree.heading('book_id', text='书号')
        
        # 设置列宽
        self.result_tree.column('title', width=150)
        self.result_tree.column('author', width=100)
        self.result_tree.column('latest_chapter', width=200)
        self.result_tree.column('book_id', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包组件
        self.result_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(fill=tk.X)
        
        # 确定和取消按钮
        ttk.Button(btn_frame, text="确定", command=self._on_select).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        
        # 绑定双击事件
        self.result_tree.bind('<Double-1>', lambda e: self._on_select())
        
        # 绑定回车键
        search_entry.bind('<Return>', lambda e: self._do_search())

    def _do_search(self):
        """执行搜索"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索关键词")
            return

        # 执行搜索
        self.log("正在搜索小说...")
        results = self.crawler.search_novel(keyword)
        
        if not results:
            self.log("未找到相关小说")
            messagebox.showinfo("提示", "未找到相关小说")
            return

        # 显示搜索结果数量
        self.log(f"找到 {len(results)} 本相关小说")
        
        # 创建搜索结果窗口
        self._show_search_results(results)

    def _on_select(self):
        """选择说"""
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一本小说")
            return
            
        # 获取选中的书号
        item = self.result_tree.item(selection[0])
        self.selected_book_id = item['values'][3]
        self.destroy()

class MainWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说下载器 - 笔趣阁")
        self.window.geometry("600x700")
        self.window.minsize(600, 700)

        # 初始化变量
        self.download_all = tk.BooleanVar(value=True)
        self.output_format = tk.StringVar(value="txt")
        self.is_downloading = False
        self.download_thread: Optional[Thread] = None
        self.current_book_id: Optional[str] = None
        self.total_chapter_count = 0
        self.novel_info = None

        # 创建爬虫和下载器实例
        self.crawler = Crawler(self)
        self.downloader = Downloader(self.crawler)

        self._init_ui()

    def _init_ui(self):
        """初始化UI界面"""
        # 配置主框架
        frame = ttk.Frame(self.window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        self._create_input_frame(frame)
        self._create_progress_frame(frame)
        self._create_log_frame(frame)

    def _create_input_frame(self, parent):
        """创建输入设置区域"""
        input_frame = ttk.LabelFrame(parent, text="下载设置", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(1, weight=1)

        # 书号输入区域
        self._create_book_id_frame(input_frame)
        # 章节范围选择
        self._create_chapter_range_frame(input_frame)
        # 输出格式选择
        self._create_format_frame(input_frame)
        # 按钮区域
        self._create_button_frame(input_frame)

    def _create_book_id_frame(self, parent):
        """创建书号和搜索区域"""
        search_frame = ttk.LabelFrame(parent, text="搜索/书号", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        search_frame.columnconfigure(1, weight=1)

        # 第一行：书名搜索
        ttk.Label(search_frame, text="书名:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        search_btn = ttk.Button(search_frame, text="搜索", command=self._do_search)
        search_btn.grid(row=0, column=2, padx=5)

        # 第二行：书号输入
        ttk.Label(search_frame, text="书号:").grid(row=1, column=0, sticky=tk.W, padx=(0,5))
        self.book_id = ttk.Entry(search_frame)
        self.book_id.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)

        # 线程数和查询按钮放在第二行
        thread_frame = ttk.Frame(search_frame)
        thread_frame.grid(row=1, column=2, sticky=tk.E)
        
        ttk.Label(thread_frame, text="线程数:").grid(row=0, column=0, padx=(0,5))
        self.thread_num = ttk.Spinbox(thread_frame, from_=1, to=10, width=5)
        self.thread_num.set(3)
        self.thread_num.grid(row=0, column=1, padx=(0,5))

        self.query_btn = ttk.Button(thread_frame, text="查询信息", command=self.query_book_info)
        self.query_btn.grid(row=0, column=2, padx=(5,0))

        # 绑定回车键
        search_entry.bind('<Return>', lambda e: self._do_search())

    def _do_search(self):
        """执行搜索"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索关键词")
            return

        # 执行搜索
        self.log("正在搜索小说...")
        results = self.crawler.search_novel(keyword)
        
        if not results:
            self.log("未找到相关小说")
            messagebox.showinfo("提示", "未找到相关小说")
            return

        # 显示搜索结果数量
        self.log(f"找到 {len(results)} 本相关小说")
        
        # 创建搜索结果窗口
        self._show_search_results(results)

    def _show_search_results(self, results):
        """显示搜索结果"""
        dialog = tk.Toplevel(self.window)
        dialog.title("搜索结果")
        dialog.geometry("700x500")  # 减小窗口尺寸
        dialog.transient(self.window)
        dialog.grab_set()

        # 创建主框架
        main_frame = ttk.Frame(dialog, padding="5")  # 减小内边距
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建表格
        columns = ('title', 'author', 'book_id')  # 只保留书名、作者和书号
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        tree.heading('title', text='书名')
        tree.heading('author', text='作者')
        tree.heading('book_id', text='书号')
        
        # 设置列宽
        tree.column('title', width=350, anchor='w')  # 加宽书名列
        tree.column('author', width=200, anchor='w')
        tree.column('book_id', width=100, anchor='center')

        # 添加滚动条
        y_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=y_scrollbar.set)

        # 显示基本结果
        def update_tree(results_data):
            tree.delete(*tree.get_children())
            for result in results_data['results']:
                tree.insert('', tk.END, values=(
                    result['title'],
                    result['author'],
                    result['book_id']
                ))

        update_tree(results)

        # 双击选择
        def on_select(event=None):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                self.book_id.delete(0, tk.END)
                self.book_id.insert(0, item['values'][2])  # book_id
                dialog.destroy()
                self.query_book_info()

        tree.bind('<Double-1>', on_select)

        # 分页控件
        page_frame = ttk.Frame(dialog, padding="3")  # 减小内边距
        current_page = results.get('page', 1)
        total_pages = results.get('total_pages', 1)
        total_count = results.get('total', 0)
        
        # 分页信息和按钮布局在一行
        btn_frame = ttk.Frame(page_frame)
        btn_frame.pack(side=tk.RIGHT, padx=5)
        
        # 分页信息
        page_info = ttk.Label(
            page_frame, 
            text=f"共 {total_count} 条结果，第 {current_page}/{total_pages} 页"
        )
        page_info.pack(side=tk.LEFT, padx=5)
        
        def change_page(offset):
            nonlocal current_page
            new_page = current_page + offset
            if 1 <= new_page <= total_pages:
                current_page = new_page
                # 显示加载提示
                for item in tree.get_children():
                    tree.item(item, values=('加载中...', '', ''))
                dialog.update()
                
                # 加载新页面数据
                try:
                    new_results = self.crawler.search_novel(self.search_var.get(), new_page)
                    if new_results and new_results['results']:
                        update_tree(new_results)
                        update_page_controls(new_results)
                except Exception as e:
                    self.log(f"加载页面失败: {str(e)}")
                    messagebox.showerror("错误", "加载页面失败")

        def update_page_controls(results_data=None):
            nonlocal total_pages, total_count
            if results_data:
                total_pages = results_data.get('total_pages', total_pages)
                total_count = results_data.get('total', total_count)
            
            page_info.config(text=f"共 {total_count} 条结果，第 {current_page}/{total_pages} 页")
            prev_btn.config(state='normal' if current_page > 1 else 'disabled')
            next_btn.config(state='normal' if current_page < total_pages else 'disabled')

        # 分页按钮
        prev_btn = ttk.Button(
            btn_frame, 
            text="上一页", 
            command=lambda: change_page(-1),
            width=8,
            state='disabled' if current_page == 1 else 'normal'
        )
        next_btn = ttk.Button(
            btn_frame, 
            text="下一页", 
            command=lambda: change_page(1),
            width=8,
            state='disabled' if current_page == total_pages else 'normal'
        )

        # 操作按钮
        action_frame = ttk.Frame(dialog, padding="3")
        select_btn = ttk.Button(action_frame, text="选择", command=on_select, width=8)
        cancel_btn = ttk.Button(action_frame, text="取消", command=dialog.destroy, width=8)

        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0))
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        prev_btn.pack(side=tk.LEFT, padx=2)
        next_btn.pack(side=tk.LEFT, padx=2)
        
        page_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=3)
        
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=3)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        select_btn.pack(side=tk.RIGHT, padx=2)

    def _create_chapter_range_frame(self, parent):
        """创建章节范围选择区域"""
        chapter_frame = ttk.LabelFrame(parent, text="章节范围", padding="10")
        chapter_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        chapter_frame.columnconfigure(1, weight=1)

        # 单选按钮
        radio_frame = ttk.Frame(chapter_frame)
        radio_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        ttk.Radiobutton(radio_frame, text="下载全部章节",
                       variable=self.download_all, value=True,
                       command=self.toggle_chapter_range).pack(side=tk.LEFT, padx=(0,20))
        ttk.Radiobutton(radio_frame, text="指定章节范围",
                       variable=self.download_all, value=False,
                       command=self.toggle_chapter_range).pack(side=tk.LEFT)

        # 章节范围输入
        range_frame = ttk.Frame(chapter_frame)
        range_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Label(range_frame, text="起始章节:").grid(row=0, column=0)
        self.start_chapter = ttk.Entry(range_frame, width=10, state='disabled')
        self.start_chapter.grid(row=0, column=1, padx=(5,20))
        self.start_chapter.insert(0, "1")

        ttk.Label(range_frame, text="结束章节:").grid(row=0, column=2)
        self.end_chapter = ttk.Entry(range_frame, width=10, state='disabled')
        self.end_chapter.grid(row=0, column=3, padx=5)
        self.end_chapter.insert(0, "0")

        self.chapter_info = ttk.Label(chapter_frame, text="")
        self.chapter_info.grid(row=2, column=0, columnspan=2, pady=5)

    def _create_format_frame(self, parent):
        """创建输出格式选择区域"""
        format_frame = ttk.LabelFrame(parent, text="输出格式", padding="10")
        format_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Radiobutton(format_frame, text="TXT文本",
                       variable=self.output_format, value="txt").pack(side=tk.LEFT, padx=20)
        ttk.Radiobutton(format_frame, text="EPUB电子书",
                       variable=self.output_format, value="epub").pack(side=tk.LEFT)

    def _create_button_frame(self, parent):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent, padding="10")
        button_frame.grid(row=3, column=0, columnspan=2, pady=5)

        self.download_btn = ttk.Button(button_frame, text="开始下载", 
                                     command=self.start_download, width=15)
        self.download_btn.pack(side=tk.LEFT, padx=5)

        self.retry_btn = ttk.Button(button_frame, text="重试失败章节",
                                  command=self.retry_failed, state='disabled', width=15)
        self.retry_btn.pack(side=tk.LEFT, padx=5)

    def _create_progress_frame(self, parent):
        """创建进度显示区域"""
        progress_frame = ttk.LabelFrame(parent, text="下载进度", padding="10")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        self.status = ttk.Label(progress_frame, text="")
        self.status.grid(row=1, column=0)

    def _create_log_frame(self, parent):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="下载日志", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def query_book_info(self):
        """查询小说信息"""
        book_id = self.book_id.get().strip()
        if not book_id.isdigit():
            messagebox.showerror("错误", "请输入正确的书号（纯数字）")
            return

        self.log_text.delete(1.0, tk.END)
        self.log("正在获取小说信息...")

        def do_query():
            try:
                # 先获取基本信息
                self.novel_info = {
                    'title': '',
                    'author': '',
                    'status': '获取中...',
                    'latest_chapter': '',
                    'total_chapters': 0
                }
                
                # 更新基本显示
                self.window.after(0, self.update_book_info)
                
                # 获取章节列表
                chapters = self.crawler.get_chapter_list(book_id)
                if not chapters:
                    self.window.after(0, lambda: self.log("获取章节列表失"))
                    return
                    
                self.total_chapter_count = len(chapters)
                
                # 异步获取详细信息
                try:
                    details = self.crawler.get_novel_details(book_id)
                    if details:
                        self.novel_info.update(details)
                except Exception as e:
                    self.window.after(0, lambda: self.log(f"获取详情失败: {str(e)}"))
                
                # 再次更新显示
                self.window.after(0, self.update_book_info)

            except Exception as e:
                self.window.after(0, lambda: self.log(f"查询失败: {str(e)}"))
                self.window.after(0, lambda: messagebox.showerror("错误", "获取小说信息失败"))

        Thread(target=do_query, daemon=True).start()

    def update_book_info(self):
        """更新小说信息显示"""
        if self.novel_info:
            info_text = (
                f"书名：{self.novel_info.get('title', '')}\n"
                f"作者：{self.novel_info.get('author', '')}\n"
                f"状态：{self.novel_info.get('status', '')}\n"
                f"总章节数：{self.total_chapter_count}"
            )
            self.log(info_text)
            self.chapter_info.config(text=f"总章节数：{self.total_chapter_count}")

            if self.end_chapter.get() == "0":
                self.end_chapter.delete(0, tk.END)
                self.end_chapter.insert(0, str(self.total_chapter_count))

    def toggle_chapter_range(self):
        """切换章节范围选择状态"""
        state = 'disabled' if self.download_all.get() else 'normal'
        self.start_chapter.config(state=state)
        self.end_chapter.config(state=state)

    def start_download(self):
        """开始下载"""
        if self.is_downloading:
            if messagebox.askyesno("提示", "正在下载中，是否停止当前下载？"):
                self.is_downloading = False
                self.downloader.is_downloading = False
                self.log("正在停止下载...")
                return
            return

        book_id = self.book_id.get().strip()
        if not book_id.isdigit():
            messagebox.showerror("错误", "请输入正确的书号（纯数字）")
            return

        try:
            thread_num = int(self.thread_num.get())
            if thread_num < 1 or thread_num > 10:
                raise ValueError()
        except:
            messagebox.showerror("错误", "线程数必须是1-10之间的整数")
            return

        if not self.novel_info:
            if not messagebox.askyesno("提示", "尚未查询小说信息，是否先查询？"):
                return
            self.query_book_info()
            return

        # 获取下载范围
        if not self.download_all.get():
            try:
                start_chapter = int(self.start_chapter.get())
                end_chapter = int(self.end_chapter.get())
            except ValueError:
                messagebox.showerror("错误", "请输入正确的章节范围")
                return
        else:
            start_chapter = 1
            end_chapter = self.total_chapter_count

        # 清空日志和进度条
        self.log_text.delete(1.0, tk.END)
        self.progress["value"] = 0
        self.status["text"] = ""
        self.retry_btn["state"] = 'disabled'

        # 保存当前书号
        self.current_book_id = book_id

        # 启动下载
        self.is_downloading = True
        self.downloader.is_downloading = True
        self.download_thread = Thread(
            target=self.downloader.start_download,
            args=(book_id, start_chapter, end_chapter, thread_num, self.output_format.get()),
            daemon=True
        )
        self.download_thread.start()

    def retry_failed(self):
        """重试失败的章节"""
        if not self.current_book_id or not self.novel_info:
            messagebox.showerror("错误", "请先下载小说")
            return

        if self.is_downloading:
            messagebox.showwarning("提示", "请等待当前下载完成")
            return

        # 获取失败章节文件路径
        novel_title = self.novel_info.get('title', '')
        novel_title = self.crawler.clean_filename(novel_title)
        failed_file = os.path.join('.', 'novels', novel_title, 'failed_chapters.txt')
        
        if not os.path.exists(failed_file):
            messagebox.showinfo("提示", "没有发现失败章节记录")
            return

        try:
            # 读取失败章节信息
            with open(failed_file, 'r', encoding='utf-8') as f:
                failed_chapters = []
                for line in f:
                    title, url = line.strip().split('\t')
                    failed_chapters.append({'title': title, 'url': url})

            if not failed_chapters:
                messagebox.showinfo("提示", "没有需要重试的章节")
                return

            # 清空日志和进度条
            self.log_text.delete(1.0, tk.END)
            self.progress["value"] = 0
            self.status["text"] = ""
            self.retry_btn["state"] = 'disabled'

            # 启动重试下载
            self.is_downloading = True
            self.downloader.is_downloading = True
            thread_num = int(self.thread_num.get())
            
            self.download_thread = Thread(
                target=self.downloader.retry_failed_chapters,
                args=(
                    self.current_book_id,
                    failed_chapters,
                    thread_num,
                    self.output_format.get()
                ),
                daemon=True
            )
            self.download_thread.start()

        except Exception as e:
            messagebox.showerror("错误", f"读取失败章节信息出错: {str(e)}")

    def update_progress(self, current: int, total: int):
        """更新进度显示"""
        progress = (current / total) * 100
        self.progress["value"] = progress
        self.status["text"] = f"进度: {current}/{total} ({progress:.1f}%)"

    def log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def ask_retry(self) -> bool:
        """询问是否要重试失败的章节"""
        return messagebox.askyesno(
            "下载失败",
            "有章节下载失败，是否使用单线程重试下载失败的章节？\n\n" +
            "单线程下载可能会更稳定，但速度较慢。",
            icon='question'
        )

    def run(self):
        """运行主窗口"""
        self.window.mainloop() 