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
        
        # 设置第一个标签页内容
        self.setup_tab1_content()
        
        # 设置第二个标签页内容
        self.setup_tab2_content()

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
                self.update_status("正在设置壁纸...")
                
                # 直接调用set_wallpaper函数
                success = set_wallpaper(self.current_image_path)
                
                # 检查返回值
                if success:
                    self.root.after(0, self.update_status, "壁纸设置成功")
                    self.root.after(0, messagebox.showinfo, "成功", "壁纸设置成功！")
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
                self.update_yuanmeng_status("正在设置壁纸...")
                
                # 直接调用set_wallpaper函数
                success = set_wallpaper(self.yuanmeng_current_image_path)
                
                # 检查返回值
                if success:
                    self.root.after(0, self.update_yuanmeng_status, "壁纸设置成功")
                    self.root.after(0, messagebox.showinfo, "成功", "壁纸设置成功！")
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

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理第一标签页的临时文件
            if hasattr(self, 'current_image_path') and os.path.exists(self.current_image_path):
                if 'temp_preview' in self.current_image_path:
                    os.remove(self.current_image_path)
            
            # 清理远梦API的临时文件
            if hasattr(self, 'yuanmeng_current_image_path') and os.path.exists(self.yuanmeng_current_image_path):
                if 'temp_yuanmeng_preview' in self.yuanmeng_current_image_path:
                    os.remove(self.yuanmeng_current_image_path)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")


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
