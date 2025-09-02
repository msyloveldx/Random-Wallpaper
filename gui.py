import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
from PIL import Image, ImageTk
import requests
import ctypes
import logging
from datetime import datetime
import json

# 导入远梦API
try:
    from yuanmeng_api import WallpaperAPI
    YUANMENG_API_AVAILABLE = True
except ImportError:
    YUANMENG_API_AVAILABLE = False
    print("远梦API模块未找到，相关功能将不可用")

# 导入动漫壁纸API
try:
    from anime_wallpaper_api import AnimeWallpaperAPI
    ANIME_API_AVAILABLE = True
except ImportError:
    ANIME_API_AVAILABLE = False
    print("动漫壁纸API模块未找到，相关功能将不可用")

# 导入动态壁纸API
try:
    from dynamic_wallpaper_api import DynamicWallpaperAPI
    DYNAMIC_API_AVAILABLE = True
except ImportError:
    DYNAMIC_API_AVAILABLE = False
    print("动态壁纸API模块未找到，相关功能将不可用")

# 导入原有的功能模块
try:
    from myAPI import (
        set_wallpaper, 
        download_and_set_wallpaper, 
        count_files_in_directory,
        get_image_format_from_url,
        get_random_image_api,
        clear_image
    )
except ImportError:
    # 如果导入失败，直接定义这些函数
    def set_wallpaper(image_path):
        try:
            abs_path = os.path.abspath(image_path)
            if os.name == 'nt':
                SPI_SETDESKWALLPAPER = 20
                SPIF_UPDATEINIFILE = 1
                SPIF_SENDCHANGE = 2
                result = ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
                )
                return result
        except Exception as e:
            print(f"Error setting wallpaper: {e}")
            return False

    def download_and_set_wallpaper(image_url, save_path):
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False
                
            if not os.path.exists('images'):
                os.makedirs('images')

            with open(save_path, 'wb') as f:
                f.write(response.content)

            if not os.path.exists(save_path):
                return False

            set_wallpaper(save_path)
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False

    def count_files_in_directory(directory_path):
        try:
            if not os.path.exists(directory_path):
                return 0
                
            file_count = 0
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isfile(item_path) and item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                    file_count += 1
            return file_count
        except Exception as e:
            print(f"Error counting files: {e}")
            return 0

    def get_image_format_from_url(image_url):
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            content_type = response.headers.get('Content-Type', '')
            mime_type = content_type.split(';')[0].strip().lower()
            
            mime_to_extension = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/gif': 'gif',
                'image/bmp': 'bmp',
                'image/webp': 'webp',
                'image/svg+xml': 'svg'
            }
            
            return mime_to_extension.get(mime_type, 'jpg')
        except Exception as e:
            print(f"Error getting image format: {e}")
            return 'jpg'

    def get_random_image_api(api_type):
        api_urls = {
            'api1': 'https://api.btstu.cn/sjbz/api.php',
            'api2': 'https://api.paugram.com/wallpaper/',
            'api3': 'https://cdn.seovx.com/d/?mom=302',
            'api4': 'https://cdn.seovx.com/?mom=302',
            'api5': 'https://cdn.seovx.com/ha/?mom=302',
            'api6': 'https://www.dmoe.cc/random.php',
        }
        
        try:
            if api_type not in list(api_urls.keys()):
                import random
                api_url = random.choice(list(api_urls.values()))
                return api_url
            elif api_type in list(api_urls.keys()):
                return api_urls[api_type]
        except Exception as e:
            print(f"Error getting random image API: {e}")
        return ''

    def clear_image(save_path):
        try:
            image = Image.open(save_path)
            from PIL import ImageEnhance
            contrast = ImageEnhance.Contrast(image)
            image = contrast.enhance(1.2)
            image.save(save_path, quality=95, dpi=(500, 500), optimize=True)
        except Exception as e:
            print(f"Error clearing image: {e}")


class ImageRandomGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("随机壁纸设置器")
        self.root.geometry("600x800")
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 创建主框架
        self.create_widgets()
        
        # 初始化变量
        self.is_downloading = False
        self.current_image_path = None
        
        # 更新图片计数
        self.update_image_count()

    def setup_styles(self):
        """设置GUI样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Info.TLabel', font=('Arial', 10))
        
        # 按钮样式
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', font=('Arial', 10, 'bold'))

    def create_widgets(self):
        """创建GUI组件"""
        # 主标题
        title_label = ttk.Label(self.root, text="🎨 随机壁纸设置器", style='Title.TLabel')
        title_label.pack(pady=10)

        # 创建标签页控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建第一个标签页 - 原有功能
        self.tab1 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab1, text="🖼️ 随机壁纸")
        
        # 创建第二个标签页 - 远梦API
        self.tab2 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab2, text="🌟 远梦API")
        
        # 创建第三个标签页 - 动漫壁纸API
        self.tab3 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab3, text="🎌 动漫壁纸")
        
        # 创建第四个标签页 - 动态壁纸API
        self.tab4 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab4, text="🎬 动态壁纸")
        
        # 创建第五个标签页 - 使用说明
        self.tab5 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab5, text="📖 使用说明")
        
        # 设置各个标签页内容
        self.setup_tab1_content()
        self.setup_tab2_content()
        self.setup_tab3_content()
        self.setup_tab4_content()
        self.setup_tab5_content()

    def setup_tab1_content(self):
        """设置第一个标签页内容 - 原有功能"""
        # API选择区域
        self.create_api_selection(self.tab1)
        
        # 分隔线
        ttk.Separator(self.tab1, orient='horizontal').pack(fill='x', pady=10)
        
        # 图片预览区域
        self.create_preview_area(self.tab1)
        
        # 分隔线
        ttk.Separator(self.tab1, orient='horizontal').pack(fill='x', pady=10)
        
        # 控制按钮区域
        self.create_control_buttons(self.tab1)
        
        # 状态栏
        self.create_status_bar(self.tab1)

    def setup_tab2_content(self):
        """设置第二个标签页内容 - 远梦API"""
        if not YUANMENG_API_AVAILABLE:
            # 如果远梦API不可用，显示错误信息
            error_frame = ttk.Frame(self.tab2)
            error_frame.pack(fill=tk.BOTH, expand=True)
            
            error_label = ttk.Label(error_frame, text="❌ 远梦API模块未找到\n请确保yuanmeng_api.py文件存在", 
                                   style='Header.TLabel', justify='center')
            error_label.pack(expand=True)
            return
        
        # 初始化远梦API
        self.yuanmeng_api = WallpaperAPI()
        
        # 创建远梦API界面
        self.create_yuanmeng_api_interface()

    def create_api_selection(self, parent):
        """创建API选择区域"""
        api_frame = ttk.LabelFrame(parent, text="API 选择", padding="10")
        api_frame.pack(fill='x', pady=5)

        # API选择下拉框
        ttk.Label(api_frame, text="选择图片API:", style='Header.TLabel').pack(anchor='w')
        
        self.api_options = [
            ('随机各类壁纸', 'api1'),
            ('随机动漫壁纸', 'api2'),
            ('随机二次元', 'api3'),
            ('随机美图', 'api4'),
            ('随机古风', 'api5'),
            ('樱花二次元', 'api6'),
            ('随机选择', 'random')
        ]
        
        self.api_var = tk.StringVar(value='随机动漫壁纸')
        api_combo = ttk.Combobox(api_frame, textvariable=self.api_var, 
                                values=[opt[0] for opt in self.api_options], 
                                state='readonly', width=20)
        api_combo.pack(pady=5)
        api_combo.bind('<<ComboboxSelected>>', self.on_api_change)
        
        # 自定义API输入
        ttk.Label(api_frame, text="或输入自定义API:", style='Header.TLabel').pack(anchor='w', pady=(10,0))
        
        custom_frame = ttk.Frame(api_frame)
        custom_frame.pack(fill='x', pady=5)
        
        self.custom_api_var = tk.StringVar()
        custom_entry = ttk.Entry(custom_frame, textvariable=self.custom_api_var, width=50)
        custom_entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        
        test_btn = ttk.Button(custom_frame, text="测试", command=self.test_custom_api)
        test_btn.pack(side='right')

    def create_preview_area(self, parent):
        """创建图片预览区域"""
        preview_frame = ttk.LabelFrame(parent, text="图片预览", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=5)

        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', height=200)
        self.preview_canvas.pack(fill='both', expand=True, pady=5)
        
        # 默认显示文字
        self.preview_canvas.create_text(300, 100, text="点击获取图片查看预览", 
                                      font=('Arial', 12), fill='gray')

    def create_control_buttons(self, parent):
        """创建控制按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)

        # 获取图片按钮
        self.get_image_btn = ttk.Button(button_frame, text="🖼️ 获取随机图片", 
                                       command=self.get_random_image, style='Action.TButton')
        self.get_image_btn.pack(side='left', padx=5)

        # 设置壁纸按钮
        self.set_wallpaper_btn = ttk.Button(button_frame, text="🖥️ 设置为壁纸", 
                                           command=self.set_as_wallpaper, style='Action.TButton')
        self.set_wallpaper_btn.pack(side='left', padx=5)
        self.set_wallpaper_btn.config(state='disabled')

        # 保存图片按钮
        self.save_image_btn = ttk.Button(button_frame, text="💾 保存图片", 
                                        command=self.save_image, style='Action.TButton')
        self.save_image_btn.pack(side='left', padx=5)
        self.save_image_btn.config(state='disabled')

        # 打开图片文件夹按钮
        open_folder_btn = ttk.Button(button_frame, text="📁 打开图片文件夹", 
                                    command=self.open_images_folder)
        open_folder_btn.pack(side='right', padx=5)

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=5)

        # 图片计数
        self.count_label = ttk.Label(status_frame, text="图片数量: 0", style='Info.TLabel')
        self.count_label.pack(side='left')

        # 状态信息
        self.status_label = ttk.Label(status_frame, text="就绪", style='Info.TLabel')
        self.status_label.pack(side='right')

    def create_yuanmeng_api_interface(self):
        """创建远梦API界面"""
        # 标题
        title_label = ttk.Label(self.tab2, text="🌟 远梦API - 随机PC壁纸", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # 分类选择区域
        category_frame = ttk.LabelFrame(self.tab2, text="壁纸分类选择", padding="10")
        category_frame.pack(fill='x', pady=5)
        
        # 分类选择下拉框
        ttk.Label(category_frame, text="选择壁纸分类:", style='Header.TLabel').pack(anchor='w')
        
        self.yuanmeng_category_var = tk.StringVar(value='')
        categories = [('随机壁纸', '')] + list(self.yuanmeng_api.get_categories().items())
        category_options = [f"{value} ({key})" if key else "随机壁纸" for key, value in categories]
        
        self.yuanmeng_category_combo = ttk.Combobox(category_frame, textvariable=self.yuanmeng_category_var,
                                                   values=category_options, state='readonly', width=30)
        self.yuanmeng_category_combo.pack(pady=5)
        self.yuanmeng_category_combo.set("随机壁纸")
        
        # 分隔线
        ttk.Separator(self.tab2, orient='horizontal').pack(fill='x', pady=10)
        
        # 图片预览区域
        preview_frame = ttk.LabelFrame(self.tab2, text="壁纸预览", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        # 预览画布
        self.yuanmeng_preview_canvas = tk.Canvas(preview_frame, bg='white', height=300)
        self.yuanmeng_preview_canvas.pack(fill='both', expand=True, pady=5)
        
        # 默认显示文字
        self.yuanmeng_preview_canvas.create_text(300, 150, text="点击获取壁纸查看预览", 
                                               font=('Arial', 12), fill='gray')
        
        # 分隔线
        ttk.Separator(self.tab2, orient='horizontal').pack(fill='x', pady=10)
        
        # 控制按钮区域
        button_frame = ttk.Frame(self.tab2)
        button_frame.pack(fill='x', pady=10)
        
        # 获取壁纸按钮
        self.yuanmeng_get_btn = ttk.Button(button_frame, text="🖼️ 获取随机壁纸", 
                                          command=self.get_yuanmeng_wallpaper, style='Action.TButton')
        self.yuanmeng_get_btn.pack(side='left', padx=5)
        
        # 设置壁纸按钮
        self.yuanmeng_set_btn = ttk.Button(button_frame, text="🖥️ 设置为壁纸", 
                                          command=self.set_yuanmeng_as_wallpaper, style='Action.TButton')
        self.yuanmeng_set_btn.pack(side='left', padx=5)
        self.yuanmeng_set_btn.config(state='disabled')
        
        # 保存壁纸按钮
        self.yuanmeng_save_btn = ttk.Button(button_frame, text="💾 保存壁纸", 
                                           command=self.save_yuanmeng_wallpaper, style='Action.TButton')
        self.yuanmeng_save_btn.pack(side='left', padx=5)
        self.yuanmeng_save_btn.config(state='disabled')
        
        # 打开图片文件夹按钮
        open_folder_btn = ttk.Button(button_frame, text="📁 打开图片文件夹", 
                                    command=self.open_images_folder)
        open_folder_btn.pack(side='right', padx=5)
        
        # 状态栏
        status_frame = ttk.Frame(self.tab2)
        status_frame.pack(fill='x', pady=5)
        
        # 图片计数
        self.yuanmeng_count_label = ttk.Label(status_frame, text="图片数量: 0", style='Info.TLabel')
        self.yuanmeng_count_label.pack(side='left')
        
        # 状态信息
        self.yuanmeng_status_label = ttk.Label(status_frame, text="就绪", style='Info.TLabel')
        self.yuanmeng_status_label.pack(side='right')
        
        # 更新图片计数
        self.update_yuanmeng_image_count()

    def on_api_change(self, event):
        """API选择改变事件"""
        self.update_status("API已更改")

    def test_custom_api(self):
        """测试自定义API"""
        api_url = self.custom_api_var.get().strip()
        if not api_url:
            messagebox.showwarning("警告", "请输入API地址")
            return

        def test_api():
            try:
                self.update_status("正在测试API...")
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    self.update_status("API测试成功")
                    messagebox.showinfo("成功", "API测试成功！")
                else:
                    self.update_status("API测试失败")
                    messagebox.showerror("错误", f"API测试失败，状态码: {response.status_code}")
            except Exception as e:
                self.update_status("API测试失败")
                messagebox.showerror("错误", f"API测试失败: {str(e)}")

        threading.Thread(target=test_api, daemon=True).start()

    def get_random_image(self):
        """获取随机图片"""
        if self.is_downloading:
            return

        def download_image():
            try:
                self.is_downloading = True
                self.get_image_btn.config(state='disabled')
                self.update_status("正在获取图片...")

                # 确定API地址
                if self.custom_api_var.get().strip():
                    image_url = self.custom_api_var.get().strip()
                else:
                    # 从选择的API名称中获取对应的API代码
                    selected_api_name = self.api_var.get()
                    api_type = None
                    
                    # 查找对应的API代码
                    for name, code in self.api_options:
                        if name == selected_api_name:
                            api_type = code
                            break
                    
                    if api_type is None:
                        # 如果没有找到匹配的，使用默认的api2
                        api_type = 'api2'
                    
                    image_url = get_random_image_api(api_type)

                if not image_url:
                    raise Exception("无法获取API地址")

                # 获取图片格式
                img_type = get_image_format_from_url(image_url)
                
                # 确保images目录存在
                if not os.path.exists('images'):
                    os.makedirs('images')

                # 生成保存路径
                img_num = count_files_in_directory('images')
                save_path = f"images/temp_preview.{img_type}"
                
                # 下载图片
                response = requests.get(image_url, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"下载失败，状态码: {response.status_code}")

                with open(save_path, 'wb') as f:
                    f.write(response.content)

                # 图片清晰化处理
                clear_image(save_path)

                # 更新预览
                self.current_image_path = save_path
                self.root.after(0, self.update_preview, save_path)
                self.root.after(0, self.update_status, "图片获取成功")
                self.root.after(0, self.enable_action_buttons)

            except Exception as e:
                self.root.after(0, self.update_status, f"获取失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"获取图片失败: {str(e)}")
            finally:
                self.is_downloading = False
                self.root.after(0, lambda: self.get_image_btn.config(state='normal'))

        threading.Thread(target=download_image, daemon=True).start()

    def update_preview(self, image_path):
        """更新图片预览"""
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 获取画布尺寸
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 200

            # 计算缩放比例
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 缩放图片
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # 清除画布并显示图片
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor='center')
            
            # 保持引用
            self.current_photo = photo
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(200, 100, text=f"预览失败: {str(e)}", 
                                          font=('Arial', 10), fill='red')

    def set_as_wallpaper(self):
        """设置为壁纸"""
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            messagebox.showwarning("警告", "请先获取图片")
            return

        def set_wallpaper_thread():
            try:
                self.update_status("正在保存并设置壁纸...")
                
                # 确保images目录存在
                if not os.path.exists('images'):
                    os.makedirs('images')
                
                # 生成保存路径
                img_num = count_files_in_directory('images')
                save_path = f"images/wallpaper_{img_num + 1}.jpg"
                
                # 复制临时文件到永久保存位置
                import shutil
                shutil.copy2(self.current_image_path, save_path)
                
                # 图片清晰化处理
                clear_image(save_path)
                
                # 设置为壁纸
                success = set_wallpaper(save_path)
                
                # 检查返回值
                if success:
                    self.root.after(0, self.update_status, "壁纸设置成功")
                    self.root.after(0, messagebox.showinfo, "成功", f"壁纸设置成功！\n已保存到: {save_path}")
                    self.root.after(0, self.update_image_count)
                else:
                    self.root.after(0, self.update_status, "壁纸设置失败")
                    self.root.after(0, messagebox.showerror, "错误", "壁纸设置失败")
                    
            except Exception as e:
                self.root.after(0, self.update_status, f"设置失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"设置壁纸失败: {str(e)}")

        threading.Thread(target=set_wallpaper_thread, daemon=True).start()

    def save_image(self):
        """保存图片"""
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            messagebox.showwarning("警告", "请先获取图片")
            return

        # 选择保存位置
        file_types = [
            ('JPEG文件', '*.jpg'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]
        
        save_path = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=".jpg",
            filetypes=file_types
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy2(self.current_image_path, save_path)
                self.update_status("图片保存成功")
                messagebox.showinfo("成功", f"图片已保存到: {save_path}")
                self.update_image_count()
            except Exception as e:
                self.update_status(f"保存失败: {str(e)}")
                messagebox.showerror("错误", f"保存图片失败: {str(e)}")

    def open_images_folder(self):
        """打开图片文件夹"""
        images_path = os.path.abspath('images')
        if not os.path.exists(images_path):
            os.makedirs(images_path)
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(images_path)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{images_path}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{images_path}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")

    def enable_action_buttons(self):
        """启用操作按钮"""
        self.set_wallpaper_btn.config(state='normal')
        self.save_image_btn.config(state='normal')

    def update_status(self, message):
        """更新状态信息"""
        self.status_label.config(text=message)

    def update_image_count(self):
        """更新图片计数"""
        count = count_files_in_directory('images')
        self.count_label.config(text=f"图片数量: {count}")

    # 远梦API相关方法
    def get_yuanmeng_wallpaper(self):
        """获取远梦API壁纸"""
        if hasattr(self, 'yuanmeng_is_downloading') and self.yuanmeng_is_downloading:
            return

        def download_wallpaper():
            try:
                self.yuanmeng_is_downloading = True
                self.yuanmeng_get_btn.config(state='disabled')
                self.update_yuanmeng_status("正在获取壁纸...")

                # 删除之前的临时文件
                if hasattr(self, 'yuanmeng_current_image_path') and os.path.exists(self.yuanmeng_current_image_path):
                    try:
                        os.remove(self.yuanmeng_current_image_path)
                    except:
                        pass

                # 获取选择的分类
                selected = self.yuanmeng_category_var.get()
                category = None
                if selected and selected != "随机壁纸":
                    # 从选项中提取分类代码
                    for key, value in self.yuanmeng_api.get_categories().items():
                        if f"{value} ({key})" == selected:
                            category = key
                            break

                # 获取壁纸信息
                result = self.yuanmeng_api.get_random_wallpaper(category, "json")
                
                if "error" in result:
                    raise Exception(result["error"])

                # 获取图片数据
                img_result = self.yuanmeng_api.get_random_wallpaper(category, "jpg")
                
                if "error" in img_result:
                    raise Exception(img_result["error"])

                # 确保images目录存在
                if not os.path.exists('images'):
                    os.makedirs('images')

                # 生成临时保存路径
                save_path = "images/temp_yuanmeng_preview.jpg"
                
                # 保存图片
                with open(save_path, 'wb') as f:
                    f.write(img_result["image_data"])

                # 更新预览
                self.yuanmeng_current_image_path = save_path
                self.yuanmeng_current_wallpaper_info = result
                
                self.root.after(0, self.update_yuanmeng_preview, save_path)
                self.root.after(0, self.update_yuanmeng_status, "壁纸获取成功")
                self.root.after(0, self.enable_yuanmeng_action_buttons)

            except Exception as e:
                self.root.after(0, self.update_yuanmeng_status, f"获取失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"获取壁纸失败: {str(e)}")
            finally:
                self.yuanmeng_is_downloading = False
                self.root.after(0, lambda: self.yuanmeng_get_btn.config(state='normal'))

        threading.Thread(target=download_wallpaper, daemon=True).start()

    def update_yuanmeng_preview(self, image_path):
        """更新远梦API图片预览"""
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 获取画布尺寸
            canvas_width = self.yuanmeng_preview_canvas.winfo_width()
            canvas_height = self.yuanmeng_preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 300

            # 计算缩放比例
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 缩放图片
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # 清除画布并显示图片
            self.yuanmeng_preview_canvas.delete("all")
            self.yuanmeng_preview_canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor='center')
            
            # 保持引用
            self.yuanmeng_current_photo = photo
            
        except Exception as e:
            self.yuanmeng_preview_canvas.delete("all")
            self.yuanmeng_preview_canvas.create_text(200, 150, text=f"预览失败: {str(e)}", 
                                                   font=('Arial', 10), fill='red')

    def set_yuanmeng_as_wallpaper(self):
        """设置远梦API壁纸为桌面壁纸"""
        if not hasattr(self, 'yuanmeng_current_image_path') or not os.path.exists(self.yuanmeng_current_image_path):
            messagebox.showwarning("警告", "请先获取壁纸")
            return

        def set_wallpaper_thread():
            try:
                self.update_yuanmeng_status("正在保存并设置壁纸...")
                
                # 确保images目录存在
                if not os.path.exists('images'):
                    os.makedirs('images')
                
                # 生成保存路径
                img_num = count_files_in_directory('images')
                save_path = f"images/yuanmeng_wallpaper_{img_num + 1}.jpg"
                
                # 复制临时文件到永久保存位置
                import shutil
                shutil.copy2(self.yuanmeng_current_image_path, save_path)
                
                # 图片清晰化处理
                clear_image(save_path)
                
                # 设置为壁纸
                success = set_wallpaper(save_path)
                
                # 检查返回值
                if success:
                    self.root.after(0, self.update_yuanmeng_status, "壁纸设置成功")
                    self.root.after(0, messagebox.showinfo, "成功", f"壁纸设置成功！\n已保存到: {save_path}")
                    self.root.after(0, self.update_yuanmeng_image_count)
                else:
                    self.root.after(0, self.update_yuanmeng_status, "壁纸设置失败")
                    self.root.after(0, messagebox.showerror, "错误", "壁纸设置失败")
                    
            except Exception as e:
                self.root.after(0, self.update_yuanmeng_status, f"设置失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"设置壁纸失败: {str(e)}")

        threading.Thread(target=set_wallpaper_thread, daemon=True).start()

    def save_yuanmeng_wallpaper(self):
        """保存远梦API壁纸"""
        if not hasattr(self, 'yuanmeng_current_image_path') or not os.path.exists(self.yuanmeng_current_image_path):
            messagebox.showwarning("警告", "请先获取壁纸")
            return

        # 选择保存位置
        file_types = [
            ('JPEG文件', '*.jpg'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]
        
        save_path = filedialog.asksaveasfilename(
            title="保存壁纸",
            defaultextension=".jpg",
            filetypes=file_types
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy2(self.yuanmeng_current_image_path, save_path)
                self.update_yuanmeng_status("壁纸保存成功")
                messagebox.showinfo("成功", f"壁纸已保存到: {save_path}")
                self.update_yuanmeng_image_count()
            except Exception as e:
                self.update_yuanmeng_status(f"保存失败: {str(e)}")
                messagebox.showerror("错误", f"保存壁纸失败: {str(e)}")
        else:
            # 如果用户取消保存，可以选择自动保存到images文件夹
            try:
                # 生成保存路径
                img_num = count_files_in_directory('images')
                auto_save_path = f"images/yuanmeng_wallpaper_{img_num + 1}.jpg"
                
                import shutil
                shutil.copy2(self.yuanmeng_current_image_path, auto_save_path)
                self.update_yuanmeng_status("壁纸已自动保存")
                messagebox.showinfo("成功", f"壁纸已自动保存到: {auto_save_path}")
                self.update_yuanmeng_image_count()
            except Exception as e:
                self.update_yuanmeng_status(f"自动保存失败: {str(e)}")
                messagebox.showerror("错误", f"自动保存壁纸失败: {str(e)}")

    def enable_yuanmeng_action_buttons(self):
        """启用远梦API操作按钮"""
        self.yuanmeng_set_btn.config(state='normal')
        self.yuanmeng_save_btn.config(state='normal')

    def update_yuanmeng_status(self, message):
        """更新远梦API状态信息"""
        self.yuanmeng_status_label.config(text=message)

    def update_yuanmeng_image_count(self):
        """更新远梦API图片计数"""
        count = count_files_in_directory('images')
        self.yuanmeng_count_label.config(text=f"图片数量: {count}")

    def setup_tab3_content(self):
        """设置第三个标签页内容 - 动漫壁纸API"""
        if not ANIME_API_AVAILABLE:
            # 如果动漫壁纸API不可用，显示错误信息
            error_frame = ttk.Frame(self.tab3)
            error_frame.pack(fill=tk.BOTH, expand=True)
            
            error_label = ttk.Label(error_frame, text="❌ 动漫壁纸API模块未找到\n请确保anime_wallpaper_api.py文件存在", 
                                   style='Header.TLabel', justify='center')
            error_label.pack(expand=True)
            return
        
        # 初始化动漫壁纸API
        self.anime_api = AnimeWallpaperAPI()
        
        # 创建动漫壁纸API界面
        self.create_anime_api_interface()

    def setup_tab4_content(self):
        """设置第四个标签页内容 - 动态壁纸API"""
        if not DYNAMIC_API_AVAILABLE:
            # 如果动态壁纸API不可用，显示错误信息
            error_frame = ttk.Frame(self.tab4)
            error_frame.pack(fill=tk.BOTH, expand=True)
            
            error_label = ttk.Label(error_frame, text="❌ 动态壁纸API模块未找到\n请确保dynamic_wallpaper_api.py文件存在", 
                                   style='Header.TLabel', justify='center')
            error_label.pack(expand=True)
            return
        
        # 初始化动态壁纸API
        self.dynamic_api = DynamicWallpaperAPI()
        
        # 创建动态壁纸API界面
        self.create_dynamic_api_interface()

    def create_anime_api_interface(self):
        """创建动漫壁纸API界面"""
        # 标题
        title_label = ttk.Label(self.tab3, text="🎌 动漫壁纸API - 随机动漫壁纸", style='Title.TLabel')
        title_label.pack(pady=10)

        
        # 图片预览区域
        preview_frame = ttk.LabelFrame(self.tab3, text="动漫壁纸预览", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        # 预览画布
        self.anime_preview_canvas = tk.Canvas(preview_frame, bg='white', height=300)
        self.anime_preview_canvas.pack(fill='both', expand=True, pady=5)
        
        # 默认显示文字
        self.anime_preview_canvas.create_text(300, 150, text="点击获取动漫壁纸查看预览", 
                                               font=('Arial', 12), fill='gray')
        
        # 分隔线
        ttk.Separator(self.tab3, orient='horizontal').pack(fill='x', pady=10)
        
        # 控制按钮区域
        button_frame = ttk.Frame(self.tab3)
        button_frame.pack(fill='x', pady=10)
        
        # 获取壁纸按钮
        self.anime_get_btn = ttk.Button(button_frame, text="🎌 获取动漫壁纸", 
                                       command=self.get_anime_wallpaper, style='Action.TButton')
        self.anime_get_btn.pack(side='left', padx=5)
        
        # 设置壁纸按钮
        self.anime_set_btn = ttk.Button(button_frame, text="🖥️ 设置为壁纸", 
                                       command=self.set_anime_as_wallpaper, style='Action.TButton')
        self.anime_set_btn.pack(side='left', padx=5)
        self.anime_set_btn.config(state='disabled')
        
        # 保存壁纸按钮
        self.anime_save_btn = ttk.Button(button_frame, text="💾 保存壁纸", 
                                        command=self.save_anime_wallpaper, style='Action.TButton')
        self.anime_save_btn.pack(side='left', padx=5)
        self.anime_save_btn.config(state='disabled')
        
        # 打开图片文件夹按钮
        open_folder_btn = ttk.Button(button_frame, text="📁 打开图片文件夹", 
                                    command=self.open_images_folder)
        open_folder_btn.pack(side='right', padx=5)
        
        # 状态栏
        status_frame = ttk.Frame(self.tab3)
        status_frame.pack(fill='x', pady=5)
        
        # 图片计数
        self.anime_count_label = ttk.Label(status_frame, text="图片数量: 0", style='Info.TLabel')
        self.anime_count_label.pack(side='left')
        
        # 状态信息
        self.anime_status_label = ttk.Label(status_frame, text="就绪", style='Info.TLabel')
        self.anime_status_label.pack(side='right')
        
        # 更新图片计数
        self.update_anime_image_count()

    def create_dynamic_api_interface(self):
        """创建动态壁纸API界面"""
        # 标题
        title_label = ttk.Label(self.tab4, text="🎬 动态壁纸API - 随机动态壁纸视频", style='Title.TLabel')
        title_label.pack(pady=10)
        
        
        # 视频预览区域
        preview_frame = ttk.LabelFrame(self.tab4, text="视频预览", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=5)
        
        # 预览画布
        self.dynamic_preview_canvas = tk.Canvas(preview_frame, bg='white', height=300)
        self.dynamic_preview_canvas.pack(fill='both', expand=True, pady=5)
        
        # 视频控制按钮框架
        video_control_frame = ttk.Frame(preview_frame)
        video_control_frame.pack(fill='x', pady=5)
        
        # 播放/暂停按钮
        self.video_play_btn = ttk.Button(video_control_frame, text="▶️ 播放", 
                                        command=self.toggle_video_playback, state='disabled')
        self.video_play_btn.pack(side='left', padx=5)
        
        # 停止按钮
        self.video_stop_btn = ttk.Button(video_control_frame, text="⏹️ 停止", 
                                        command=self.stop_video_playback, state='disabled')
        self.video_stop_btn.pack(side='left', padx=5)
        
        # 进度条
        self.video_progress = ttk.Progressbar(video_control_frame, mode='determinate')
        self.video_progress.pack(side='left', fill='x', expand=True, padx=10)
        
        # 默认显示文字
        self.dynamic_preview_canvas.create_text(300, 150, text="点击获取动态壁纸查看预览", 
                                               font=('Arial', 12), fill='gray')
        
        # 分隔线
        ttk.Separator(self.tab4, orient='horizontal').pack(fill='x', pady=10)
        
        # 控制按钮区域
        button_frame = ttk.Frame(self.tab4)
        button_frame.pack(fill='x', pady=10)
        
        # 获取视频按钮
        self.dynamic_get_btn = ttk.Button(button_frame, text="🎬 获取动态壁纸", 
                                         command=self.get_dynamic_wallpaper, style='Action.TButton')
        self.dynamic_get_btn.pack(side='left', padx=5)
        
        # 下载视频按钮
        self.dynamic_download_btn = ttk.Button(button_frame, text="💾 下载视频", 
                                              command=self.download_dynamic_wallpaper, style='Action.TButton')
        self.dynamic_download_btn.pack(side='left', padx=5)
        self.dynamic_download_btn.config(state='disabled')
        
        # 打开视频文件夹按钮
        open_video_folder_btn = ttk.Button(button_frame, text="📁 打开视频文件夹", 
                                          command=self.open_videos_folder)
        open_video_folder_btn.pack(side='right', padx=5)
        
        # 状态栏
        status_frame = ttk.Frame(self.tab4)
        status_frame.pack(fill='x', pady=5)
        
        # 视频计数
        self.dynamic_count_label = ttk.Label(status_frame, text="视频数量: 0", style='Info.TLabel')
        self.dynamic_count_label.pack(side='left')
        
        # 状态信息
        self.dynamic_status_label = ttk.Label(status_frame, text="就绪", style='Info.TLabel')
        self.dynamic_status_label.pack(side='right')
        
        # 更新视频计数
        self.update_dynamic_video_count()

    def setup_tab5_content(self):
        """设置第五个标签页内容 - 使用说明"""
        # 标题
        title_label = ttk.Label(self.tab5, text="📖 使用说明", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # 创建滚动文本框
        text_frame = ttk.Frame(self.tab5)
        text_frame.pack(fill='both', expand=True, pady=10)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        # 创建文本框
        self.help_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                                font=('Arial', 10), bg='white', fg='black')
        self.help_text.pack(side='left', fill='both', expand=True)
        
        # 配置滚动条
        scrollbar.config(command=self.help_text.yview)
        
        # 使用说明内容
        help_content = """🎨 随机壁纸设置器 - 使用说明

📋 功能概述
本软件提供了多种获取和设置壁纸的方式，包括随机壁纸、远梦API、动漫壁纸和动态壁纸。

🖼️ 第一个标签页 - 随机壁纸
• 功能：从多个API获取随机壁纸图片
• 使用方法：
  1. 选择API类型（随机各类壁纸、随机动漫壁纸等）
  2. 或输入自定义API地址
  3. 点击"获取随机图片"按钮
  4. 预览图片后可以设置为壁纸或保存到本地
• 支持格式：JPG、PNG、GIF、BMP、WEBP
• 保存位置：images/ 目录

🌟 第二个标签页 - 远梦API
• 功能：使用远梦API获取高质量PC壁纸
• 使用方法：
  1. 选择壁纸分类（风景、动漫、游戏等）
  2. 点击"获取随机壁纸"按钮
  3. 预览壁纸后可以设置为桌面壁纸或保存
• 特点：高质量、分类明确
• 保存位置：images/ 目录

🎌 第三个标签页 - 动漫壁纸
• 功能：专门获取动漫风格的壁纸
• API来源：https://img.8845.top/random.php
• 使用方法：
  1. 点击"获取动漫壁纸"按钮
  2. 预览动漫壁纸
  3. 可以设置为桌面壁纸或保存
• 特点：专门针对动漫爱好者
• 保存位置：images/ 目录

🎬 第四个标签页 - 动态壁纸
• 功能：获取动态视频壁纸
• API来源：https://i18.net/video.php
• 使用方法：
  1. 点击"获取动态壁纸"按钮
  2. 预览视频（支持播放/暂停/停止控制）
  3. 点击"下载视频"保存完整视频
• 视频控制：
  - ▶️ 播放：开始播放视频预览
  - ⏸️ 暂停：暂停视频播放
  - ⏹️ 停止：停止播放并回到第一帧
  - 进度条：显示当前播放进度
• 保存位置：videos/ 目录
• 推荐软件：
  - Wallpaper Engine (Steam收费)
  - Lively Wallpaper (免费)
  - 注意：动态壁纸会消耗更多系统资源

💡 通用操作说明
• 预览功能：所有标签页都支持图片/视频预览
• 设置为壁纸：点击"设置为壁纸"按钮即可
• 保存文件：点击"保存"按钮选择保存位置
• 打开文件夹：点击"打开文件夹"按钮查看已保存的文件
• 状态显示：底部状态栏显示当前操作状态和文件数量

⚠️ 注意事项
1. 需要网络连接才能获取壁纸
2. 动态壁纸需要安装OpenCV：pip install opencv-python
3. 动态壁纸会消耗更多系统资源，请根据电脑性能选择使用
4. 所有下载的文件都会保存在对应的目录中
5. 临时预览文件会在程序关闭时自动清理

🔧 故障排除
• 如果预览失败，请检查网络连接
• 如果动态壁纸预览失败，请安装OpenCV
• 如果API连接失败，请稍后重试或更换API
• 如果设置壁纸失败，请检查图片文件是否完整

📞 技术支持
如有问题，请检查：
1. Python环境是否正确安装
2. 所需依赖包是否已安装
3. 网络连接是否正常
4. 文件权限是否足够

版本信息：随机壁纸设置器 v2.0
更新时间：2025年"""
        
        # 插入使用说明内容
        self.help_text.insert('1.0', help_content)
        self.help_text.config(state='disabled')

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理第一标签页的临时文件
            if hasattr(self, 'current_image_path') and self.current_image_path is not None and os.path.exists(self.current_image_path):
                if 'temp_preview' in self.current_image_path:
                    os.remove(self.current_image_path)
            
            # 清理远梦API的临时文件
            if hasattr(self, 'yuanmeng_current_image_path') and self.yuanmeng_current_image_path is not None and os.path.exists(self.yuanmeng_current_image_path):
                if 'temp_yuanmeng_preview' in self.yuanmeng_current_image_path:
                    os.remove(self.yuanmeng_current_image_path)
            
            # 清理动漫壁纸API的临时文件
            if hasattr(self, 'anime_current_image_path') and self.anime_current_image_path is not None and os.path.exists(self.anime_current_image_path):
                if 'temp_anime_preview' in self.anime_current_image_path:
                    os.remove(self.anime_current_image_path)
            
            # 清理动态壁纸API的临时文件
            if hasattr(self, 'dynamic_current_preview_path') and self.dynamic_current_preview_path is not None:
                if os.path.exists(self.dynamic_current_preview_path) and 'temp_dynamic_preview' in self.dynamic_current_preview_path:
                    os.remove(self.dynamic_current_preview_path)
            
            # 清理临时视频文件
            temp_video_path = "videos/temp_dynamic_preview.mp4"
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            # 清理临时预览图文件
            temp_preview_path = "videos/temp_dynamic_preview.jpg"
            if os.path.exists(temp_preview_path):
                os.remove(temp_preview_path)
            
            # 清理视频帧数据
            if hasattr(self, 'dynamic_video_frames'):
                delattr(self, 'dynamic_video_frames')
            if hasattr(self, 'dynamic_video_info'):
                delattr(self, 'dynamic_video_info')
            if hasattr(self, 'dynamic_is_playing'):
                self.dynamic_is_playing = False
        except Exception as e:
            print(f"清理临时文件时出错: {e}")

    # 动漫壁纸API相关方法
    def get_anime_wallpaper(self):
        """获取动漫壁纸"""
        if hasattr(self, 'anime_is_downloading') and self.anime_is_downloading:
            return

        def download_wallpaper():
            try:
                self.anime_is_downloading = True
                self.anime_get_btn.config(state='disabled')
                self.update_anime_status("正在获取动漫壁纸...")

                # 删除之前的临时文件
                if hasattr(self, 'anime_current_image_path') and os.path.exists(self.anime_current_image_path):
                    try:
                        os.remove(self.anime_current_image_path)
                    except:
                        pass

                # 获取壁纸信息
                result = self.anime_api.get_wallpaper_info_only()
                
                if "error" in result:
                    raise Exception(result["error"])

                # 检查图片状态
                if result.get("Image_status") != "ok":
                    raise Exception(f"图片状态异常: {result.get('Image_status')}")

                image_url = result.get("image_links")
                if not image_url:
                    raise Exception("未获取到图片链接")

                # 确保images目录存在
                if not os.path.exists('images'):
                    os.makedirs('images')

                # 生成临时保存路径
                img_format = get_image_format_from_url(image_url)
                save_path = f"images/temp_anime_preview.{img_format}"
                
                # 下载图片
                response = requests.get(image_url, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"下载失败，状态码: {response.status_code}")

                with open(save_path, 'wb') as f:
                    f.write(response.content)

                # 图片清晰化处理
                clear_image(save_path)

                # 更新预览
                self.anime_current_image_path = save_path
                self.anime_current_wallpaper_info = result
                
                self.root.after(0, self.update_anime_preview, save_path)
                self.root.after(0, self.update_anime_status, "动漫壁纸获取成功")
                self.root.after(0, self.enable_anime_action_buttons)

            except Exception as e:
                self.root.after(0, self.update_anime_status, f"获取失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"获取动漫壁纸失败: {str(e)}")
            finally:
                self.anime_is_downloading = False
                self.root.after(0, lambda: self.anime_get_btn.config(state='normal'))

        threading.Thread(target=download_wallpaper, daemon=True).start()

    def update_anime_preview(self, image_path):
        """更新动漫壁纸预览"""
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 获取画布尺寸
            canvas_width = self.anime_preview_canvas.winfo_width()
            canvas_height = self.anime_preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 300

            # 计算缩放比例
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 缩放图片
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # 清除画布并显示图片
            self.anime_preview_canvas.delete("all")
            self.anime_preview_canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor='center')
            
            # 保持引用
            self.anime_current_photo = photo
            
        except Exception as e:
            self.anime_preview_canvas.delete("all")
            self.anime_preview_canvas.create_text(200, 150, text=f"预览失败: {str(e)}", 
                                               font=('Arial', 10), fill='red')

    def set_anime_as_wallpaper(self):
        """设置动漫壁纸为桌面壁纸"""
        if not hasattr(self, 'anime_current_image_path') or not os.path.exists(self.anime_current_image_path):
            messagebox.showwarning("警告", "请先获取动漫壁纸")
            return

        def set_wallpaper_thread():
            try:
                self.update_anime_status("正在保存并设置壁纸...")
                
                # 确保images目录存在
                if not os.path.exists('images'):
                    os.makedirs('images')
                
                # 生成保存路径
                img_num = count_files_in_directory('images')
                save_path = f"images/anime_wallpaper_{img_num + 1}.jpg"
                
                # 复制临时文件到永久保存位置
                import shutil
                shutil.copy2(self.anime_current_image_path, save_path)
                
                # 图片清晰化处理
                clear_image(save_path)
                
                # 设置为壁纸
                success = set_wallpaper(save_path)
                
                # 检查返回值
                if success:
                    self.root.after(0, self.update_anime_status, "壁纸设置成功")
                    self.root.after(0, messagebox.showinfo, "成功", f"动漫壁纸设置成功！\n已保存到: {save_path}")
                    self.root.after(0, self.update_anime_image_count)
                else:
                    self.root.after(0, self.update_anime_status, "壁纸设置失败")
                    self.root.after(0, messagebox.showerror, "错误", "壁纸设置失败")
                    
            except Exception as e:
                self.root.after(0, self.update_anime_status, f"设置失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"设置壁纸失败: {str(e)}")

        threading.Thread(target=set_wallpaper_thread, daemon=True).start()

    def save_anime_wallpaper(self):
        """保存动漫壁纸"""
        if not hasattr(self, 'anime_current_image_path') or not os.path.exists(self.anime_current_image_path):
            messagebox.showwarning("警告", "请先获取动漫壁纸")
            return

        # 选择保存位置
        file_types = [
            ('JPEG文件', '*.jpg'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]
        
        save_path = filedialog.asksaveasfilename(
            title="保存动漫壁纸",
            defaultextension=".jpg",
            filetypes=file_types
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy2(self.anime_current_image_path, save_path)
                self.update_anime_status("壁纸保存成功")
                messagebox.showinfo("成功", f"动漫壁纸已保存到: {save_path}")
                self.update_anime_image_count()
            except Exception as e:
                self.update_anime_status(f"保存失败: {str(e)}")
                messagebox.showerror("错误", f"保存动漫壁纸失败: {str(e)}")
        else:
            # 如果用户取消保存，可以选择自动保存到images文件夹
            try:
                # 生成保存路径
                img_num = count_files_in_directory('images')
                auto_save_path = f"images/anime_wallpaper_{img_num + 1}.jpg"
                
                import shutil
                shutil.copy2(self.anime_current_image_path, auto_save_path)
                self.update_anime_status("壁纸已自动保存")
                messagebox.showinfo("成功", f"动漫壁纸已自动保存到: {auto_save_path}")
                self.update_anime_image_count()
            except Exception as e:
                self.update_anime_status(f"自动保存失败: {str(e)}")
                messagebox.showerror("错误", f"自动保存动漫壁纸失败: {str(e)}")

    def enable_anime_action_buttons(self):
        """启用动漫壁纸操作按钮"""
        self.anime_set_btn.config(state='normal')
        self.anime_save_btn.config(state='normal')

    def update_anime_status(self, message):
        """更新动漫壁纸状态信息"""
        self.anime_status_label.config(text=message)

    def update_anime_image_count(self):
        """更新动漫壁纸图片计数"""
        count = count_files_in_directory('images')
        self.anime_count_label.config(text=f"图片数量: {count}")

    # 动态壁纸API相关方法
    def get_dynamic_wallpaper(self):
        """获取动态壁纸信息并生成预览"""
        if hasattr(self, 'dynamic_is_loading') and self.dynamic_is_loading:
            return

        def get_wallpaper_info():
            try:
                self.dynamic_is_loading = True
                self.dynamic_get_btn.config(state='disabled')
                self.update_dynamic_status("正在获取动态壁纸信息...")

                # 获取动态壁纸信息
                result = self.dynamic_api.get_wallpaper_info_only()
                
                if "error" in result:
                    raise Exception(result["error"])

                # 检查请求状态
                if not result.get("success", False):
                    raise Exception(f"API返回失败: {result.get('message', '未知错误')}")

                video_url = result.get("video_url")
                if not video_url:
                    raise Exception("未获取到视频链接")

                # 更新信息显示
                self.dynamic_current_wallpaper_info = result
                self.dynamic_current_video_url = video_url
                
                # 生成视频预览
                self.root.after(0, self.update_dynamic_status, "正在生成视频预览...")
                preview_success = self.generate_video_preview(video_url)
                
                if preview_success:
                    self.root.after(0, self.update_dynamic_status, "动态壁纸信息获取成功")
                    self.root.after(0, self.enable_dynamic_action_buttons)
                else:
                    # 如果预览失败，显示简单提示
                    self.root.after(0, self.show_video_info_preview, video_url, "")
                    self.root.after(0, self.update_dynamic_status, "动态壁纸信息获取成功")
                    self.root.after(0, self.enable_dynamic_action_buttons)

            except Exception as e:
                self.root.after(0, self.update_dynamic_status, f"获取失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"获取动态壁纸信息失败: {str(e)}")
            finally:
                self.dynamic_is_loading = False
                self.root.after(0, lambda: self.dynamic_get_btn.config(state='normal'))

        threading.Thread(target=get_wallpaper_info, daemon=True).start()

    def generate_video_preview(self, video_url):
        """生成视频预览"""
        try:
            # 确保videos目录存在
            if not os.path.exists('videos'):
                os.makedirs('videos')
            
            # 生成临时视频文件路径
            temp_video_path = "videos/temp_dynamic_preview.mp4"
            
            # 先清理之前的临时文件
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            # 下载完整的视频文件
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()
            
            with open(temp_video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 检查文件是否下载成功
            if not os.path.exists(temp_video_path) or os.path.getsize(temp_video_path) == 0:
                return False
            
            # 尝试使用OpenCV处理视频
            try:
                import cv2
                
                # 打开视频文件
                cap = cv2.VideoCapture(temp_video_path)
                
                # 检查视频是否成功打开
                if not cap.isOpened():
                    cap.release()
                    return False
                
                # 获取视频信息
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                # 保存视频信息
                self.dynamic_video_info = {
                    'fps': fps,
                    'frame_count': frame_count,
                    'duration': duration,
                    'video_path': temp_video_path
                }
                
                # 提取更多帧作为预览，尽量还原原视频
                frames = []
                # 根据视频长度调整帧间隔，确保有足够的帧数
                if duration <= 5:  # 5秒以内的视频，每秒提取15帧
                    frame_interval = max(1, int(fps / 15))
                    max_frames = min(75, frame_count)  # 最多75帧
                elif duration <= 10:  # 10秒以内的视频，每秒提取12帧
                    frame_interval = max(1, int(fps / 12))
                    max_frames = min(120, frame_count)  # 最多120帧
                else:  # 更长的视频，每秒提取10帧
                    frame_interval = max(1, int(fps / 10))
                    max_frames = min(150, frame_count)  # 最多150帧
                
                for i in range(max_frames):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        # 转换为RGB格式
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame_rgb)
                    else:
                        break
                
                cap.release()
                
                if frames:
                    # 保存帧数据
                    self.dynamic_video_frames = frames
                    self.dynamic_current_frame = 0
                    self.dynamic_is_playing = False
                    
                    # 显示第一帧
                    self.root.after(0, self.show_video_frame, 0)
                    
                    # 启用视频控制按钮并设置为播放状态
                    self.root.after(0, self.enable_video_controls)
                    self.root.after(0, self.reset_video_controls)
                    
                    return True
                else:
                    return False
                    
            except ImportError:
                # 如果没有OpenCV，显示提示信息
                self.root.after(0, self.show_opencv_warning)
                return False
            except Exception as e:
                print(f"生成视频预览失败: {e}")
                return False
                
        except Exception as e:
            print(f"下载视频预览失败: {e}")
            return False

    def show_opencv_warning(self):
        """显示OpenCV缺失警告"""
        self.dynamic_preview_canvas.delete("all")
        self.dynamic_preview_canvas.create_text(300, 150, 
                                               text="预览功能需要安装OpenCV\n请运行: pip install opencv-python", 
                                               font=('Arial', 12), fill='red', justify='center')

    def show_video_info_preview(self, video_url, info_text):
        """显示视频信息预览"""
        self.dynamic_preview_canvas.delete("all")
        
        # 显示简单提示信息
        preview_text = f"""🎬 动态壁纸视频
        
📹 视频链接: {video_url[:50]}...

💡 提示: 
• 点击"下载视频"按钮下载完整视频
• 下载后可使用Wallpaper Engine等软件设置动态壁纸
• 预览功能需要安装OpenCV: pip install opencv-python"""
        
        self.dynamic_preview_canvas.create_text(300, 150, 
                                               text=preview_text, 
                                               font=('Arial', 11), fill='black', justify='center')

    def show_video_frame(self, frame_index):
        """显示视频帧"""
        try:
            if not hasattr(self, 'dynamic_video_frames') or not self.dynamic_video_frames:
                return
            
            if frame_index >= len(self.dynamic_video_frames):
                frame_index = 0
            
            # 获取画布尺寸
            canvas_width = self.dynamic_preview_canvas.winfo_width()
            canvas_height = self.dynamic_preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 300
            
            # 获取帧数据
            frame = self.dynamic_video_frames[frame_index]
            
            # 转换为PIL图像
            from PIL import Image
            pil_image = Image.fromarray(frame)
            
            # 计算缩放比例
            img_width, img_height = pil_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 缩放图片
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # 清除画布并显示图片
            self.dynamic_preview_canvas.delete("all")
            self.dynamic_preview_canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor='center')
            
            # 添加帧信息
            frame_info = f"帧 {frame_index + 1}/{len(self.dynamic_video_frames)}"
            self.dynamic_preview_canvas.create_text(canvas_width//2, canvas_height-20, 
                                                   text=frame_info, 
                                                   font=('Arial', 10), fill='black')
            
            # 保持引用
            self.dynamic_current_photo = photo
            self.dynamic_current_frame = frame_index
            
            # 更新进度条
            if hasattr(self, 'dynamic_video_frames'):
                progress = (frame_index / len(self.dynamic_video_frames)) * 100
                self.video_progress['value'] = progress
            
        except Exception as e:
            print(f"显示视频帧失败: {e}")

    def enable_video_controls(self):
        """启用视频控制按钮"""
        self.video_play_btn.config(state='normal')
        self.video_stop_btn.config(state='normal')

    def reset_video_controls(self):
        """重置视频控制按钮状态"""
        self.video_play_btn.config(text="▶️ 播放")
        self.video_stop_btn.config(text="⏹️ 停止")
        self.video_progress['value'] = 0

    def toggle_video_playback(self):
        """切换视频播放/暂停"""
        if not hasattr(self, 'dynamic_video_frames') or not self.dynamic_video_frames:
            return
        
        if hasattr(self, 'dynamic_is_playing') and self.dynamic_is_playing:
            # 暂停播放
            self.dynamic_is_playing = False
            self.video_play_btn.config(text="▶️ 播放")
        else:
            # 开始播放
            self.dynamic_is_playing = True
            self.video_play_btn.config(text="⏸️ 暂停")
            self.play_video_animation()

    def play_video_animation(self):
        """播放视频动画"""
        if not hasattr(self, 'dynamic_is_playing') or not self.dynamic_is_playing:
            return
        
        if not hasattr(self, 'dynamic_video_frames') or not self.dynamic_video_frames:
            return
        
        # 显示当前帧
        self.show_video_frame(self.dynamic_current_frame)
        
        # 移动到下一帧
        self.dynamic_current_frame = (self.dynamic_current_frame + 1) % len(self.dynamic_video_frames)
        
        # 计算下一帧的延迟时间（约12fps，更流畅）
        delay = int(1000 / 12)  # 约83ms
        
        # 安排下一帧
        self.root.after(delay, self.play_video_animation)

    def stop_video_playback(self):
        """停止视频播放"""
        self.dynamic_is_playing = False
        self.video_play_btn.config(text="▶️ 播放")
        self.dynamic_current_frame = 0
        self.video_progress['value'] = 0
        self.show_video_frame(0)





    def download_dynamic_wallpaper(self):
        """下载动态壁纸视频"""
        if not hasattr(self, 'dynamic_current_video_url'):
            messagebox.showwarning("警告", "请先获取动态壁纸信息")
            return

        def download_video():
            try:
                self.dynamic_download_btn.config(state='disabled')
                self.update_dynamic_status("正在下载动态壁纸视频...")

                # 使用当前预览的视频URL进行下载
                video_url = self.dynamic_current_video_url
                
                # 确保videos目录存在
                if not os.path.exists('videos'):
                    os.makedirs('videos')
                
                # 生成保存路径
                video_num = self.count_video_files_in_directory('videos')
                save_path = f"videos/dynamic_wallpaper_{video_num + 1}.mp4"
                
                # 下载视频
                response = requests.get(video_url, timeout=60, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 更新进度（如果有总大小信息）
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                self.root.after(0, self.update_dynamic_status, 
                                              f"正在下载动态壁纸视频... {progress:.1f}%")
                
                # 检查下载是否成功
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    self.root.after(0, self.update_dynamic_status, "动态壁纸视频下载成功")
                    self.root.after(0, messagebox.showinfo, "成功", f"动态壁纸视频下载成功！\n已保存到: {save_path}")
                    self.root.after(0, self.update_dynamic_video_count)
                else:
                    self.root.after(0, self.update_dynamic_status, "动态壁纸视频下载失败")
                    self.root.after(0, messagebox.showerror, "错误", "动态壁纸视频下载失败")
                    
            except Exception as e:
                self.root.after(0, self.update_dynamic_status, f"下载失败: {str(e)}")
                self.root.after(0, messagebox.showerror, "错误", f"下载动态壁纸视频失败: {str(e)}")
            finally:
                self.root.after(0, lambda: self.dynamic_download_btn.config(state='normal'))

        threading.Thread(target=download_video, daemon=True).start()

    def enable_dynamic_action_buttons(self):
        """启用动态壁纸操作按钮"""
        self.dynamic_download_btn.config(state='normal')

    def update_dynamic_status(self, message):
        """更新动态壁纸状态信息"""
        self.dynamic_status_label.config(text=message)

    def count_video_files_in_directory(self, directory_path):
        """统计指定目录下的视频文件数量（排除临时文件）"""
        try:
            if not os.path.exists(directory_path):
                return 0
                
            file_count = 0
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if (os.path.isfile(item_path) and 
                    item.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')) and
                    not item.startswith('temp_')):  # 排除临时文件
                    file_count += 1
            return file_count
        except Exception as e:
            print(f"Error counting video files: {e}")
            return 0

    def update_dynamic_video_count(self):
        """更新动态壁纸视频计数"""
        try:
            count = self.count_video_files_in_directory('videos')
            self.dynamic_count_label.config(text=f"视频数量: {count}")
        except Exception as e:
            self.dynamic_count_label.config(text="视频数量: 0")

    def open_videos_folder(self):
        """打开视频文件夹"""
        videos_path = os.path.abspath('videos')
        if not os.path.exists(videos_path):
            os.makedirs(videos_path)
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(videos_path)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{videos_path}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{videos_path}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = ImageRandomGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # 设置窗口关闭事件
    def on_closing():
        app.cleanup_temp_files()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动GUI
    root.mainloop()


if __name__ == "__main__":
    main()
