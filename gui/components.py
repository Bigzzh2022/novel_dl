import tkinter as tk
from tkinter import ttk

class BookInfoFrame(ttk.LabelFrame):
    """书号和线程数输入框架"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="基本信息", padding="10", **kwargs)
        self.columnconfigure(1, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        # 书号输入
        ttk.Label(self, text="书号:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        self.book_id = ttk.Entry(self)
        self.book_id.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # 线程数选择
        thread_frame = ttk.Frame(self)
        thread_frame.grid(row=0, column=2, sticky=tk.E)
        ttk.Label(thread_frame, text="线程数:").grid(row=0, column=0, padx=(10,5))
        self.thread_num = ttk.Spinbox(thread_frame, from_=1, to=10, width=5)
        self.thread_num.set(3)
        self.thread_num.grid(row=0, column=1, padx=(0,5))

        # 查询按钮
        self.query_btn = ttk.Button(self, text="查询信息")
        self.query_btn.grid(row=0, column=3, padx=(5,0))

class ChapterRangeFrame(ttk.LabelFrame):
    """章节范围选择框架"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="章节范围", padding="10", **kwargs)
        self.columnconfigure(1, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        # 下载范围选择
        self.download_all = tk.BooleanVar(value=True)
        radio_frame = ttk.Frame(self)
        radio_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(radio_frame, text="下载全部章节",
                       variable=self.download_all, value=True).grid(row=0, column=0, padx=(0,20))
        ttk.Radiobutton(radio_frame, text="指定章节范围",
                       variable=self.download_all, value=False).grid(row=0, column=1)

        # 章节范围输入
        range_frame = ttk.Frame(self)
        range_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Label(range_frame, text="起始章节:").grid(row=0, column=0)
        self.start_chapter = ttk.Entry(range_frame, width=10, state='disabled')
        self.start_chapter.grid(row=0, column=1, padx=(5,20))
        self.start_chapter.insert(0, "1")

        ttk.Label(range_frame, text="结束章节:").grid(row=0, column=2)
        self.end_chapter = ttk.Entry(range_frame, width=10, state='disabled')
        self.end_chapter.grid(row=0, column=3, padx=5)
        self.end_chapter.insert(0, "0")

        # 章节信息显示
        self.chapter_info = ttk.Label(self, text="")
        self.chapter_info.grid(row=2, column=0, columnspan=2, pady=5)

class OutputFormatFrame(ttk.LabelFrame):
    """输出格式选择框架"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="输出格式", padding="10", **kwargs)
        self.columnconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        self.output_format = tk.StringVar(value="txt")
        formats_frame = ttk.Frame(self)
        formats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(formats_frame, text="TXT文本",
                       variable=self.output_format, value="txt").grid(row=0, column=0, padx=10)
        ttk.Radiobutton(formats_frame, text="EPUB电子书",
                       variable=self.output_format, value="epub").grid(row=0, column=1, padx=10)

class ControlButtonFrame(ttk.Frame):
    """控制按钮框架"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        self.download_btn = ttk.Button(self, text="开始下载", width=15)
        self.download_btn.grid(row=0, column=0, padx=5)

        self.retry_btn = ttk.Button(self, text="重试失败章节",
                                  state='disabled', width=15)
        self.retry_btn.grid(row=0, column=1, padx=5)

class ProgressFrame(ttk.LabelFrame):
    """进度显示框架"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="下载进度", padding="10", **kwargs)
        self.columnconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        self.progress = ttk.Progressbar(self, mode='determinate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        self.status = ttk.Label(self, text="")
        self.status.grid(row=1, column=0)

class LogFrame(ttk.LabelFrame):
    """日志显示框架"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="下载日志", padding="10", **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        self.log_text = tk.Text(self, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def clear(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END) 