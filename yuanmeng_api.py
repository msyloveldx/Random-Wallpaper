#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远梦API - 随机PC壁纸获取工具
基于 https://api.mmp.cc/doc/pcwallpaper.html 的API接口
"""

import requests
import json
import os
from typing import Optional, Dict, Any
import logging
from myAPI import count_files_in_directory, get_image_format_from_url

# 配置日志
try:
    from logging_config import get_logger
    logger = get_logger("yuanmengAPI")
    logger.propagate = False
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("yuanmengAPI")
    logger.propagate = False

class WallpaperAPI:
    """远梦API壁纸获取类"""
    
    def __init__(self):
        self.base_url = "https://api.mmp.cc/api/pcwallpaper"
        self.categories = {
            "4k": "4K高清壁纸",
            "landscape": "风景壁纸", 
            "belle": "妹子壁纸",
            "game": "游戏壁纸",
            "photo": "影视剧照",
            "cool": "炫酷壁纸",
            "star": "明星壁纸",
            "car": "汽车靓照",
            "cartoon": "动漫壁纸"
        }
    
    def get_random_wallpaper(self, category: Optional[str] = None, 
                           response_type: str = "json") -> Dict[str, Any]:
        """
        获取随机壁纸
        
        Args:
            category: 壁纸分类，可选值见self.categories
            response_type: 返回类型，"json"或"jpg"
            
        Returns:
            API响应数据
        """
        try:
            # 构建请求参数
            params = {"type": response_type}
            if category and category in self.categories:
                params["category"] = category
            
            # 发送请求
            logger.info(f"正在获取{self.categories.get(category, '随机')}壁纸...")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            if response_type == "json":
                return response.json()
            else:
                return {"image_data": response.content, "content_type": response.headers.get("content-type")}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return {"error": f"请求失败: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return {"error": f"数据解析失败: {str(e)}"}
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {"error": f"未知错误: {str(e)}"}
    
    def download_wallpaper(self, category: Optional[str] = None, 
                          save_path: str = "images/wallpaper.jpg") -> bool:
        """
        下载壁纸到本地
        
        Args:
            category: 壁纸分类
            save_path: 保存路径
            
        Returns:
            是否下载成功
        """
        try:
            # 获取图片数据
            result = self.get_random_wallpaper(category, "jpg")
            
            if "error" in result:
                logger.error(f"获取壁纸失败: {result['error']}")
                return False
            
            # 保存图片
            with open(save_path, "wb") as f:
                f.write(result["image_data"])
            
            logger.info(f"壁纸已保存到: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载壁纸失败: {e}")
            return False
    
    def get_categories(self) -> Dict[str, str]:
        """获取所有可用的壁纸分类"""
        return self.categories.copy()
    
    def print_categories(self):
        """打印所有可用的壁纸分类"""
        print("可用的壁纸分类:")
        for key, value in self.categories.items():
            print(f"  {key}: {value}")


def main():
    """主函数 - 演示API使用"""
    api = WallpaperAPI()
    
    print("=== 远梦API - 随机PC壁纸获取工具 ===")
    print()
    
    # 显示可用分类
    api.print_categories()
    print()

    img_num = count_files_in_directory('images')
    logger.info(f"在images文件夹中找到{img_num}张壁纸！")

    # 示例1: 获取随机壁纸信息
    print("1. 获取随机壁纸信息:")
    result = api.get_random_wallpaper()
    if "error" not in result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"错误: {result['error']}")
    print()
    
    # 示例2: 获取动漫壁纸信息
    print("2. 获取动漫壁纸信息:")
    result = api.get_random_wallpaper("cartoon")
    if "error" not in result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"错误: {result['error']}")
    print()
    
    # 示例3: 下载风景壁纸
    print("3. 下载风景壁纸:")
    if api.download_wallpaper("landscape", f"images/landscape_wallpaper_{img_num + 1}.jpg"):
        print("风景壁纸下载成功!")
    else:
        print("风景壁纸下载失败!")
    print()
    
    # 示例4: 下载4K壁纸
    print("4. 下载4K壁纸:")
    if api.download_wallpaper("4k", f"images/4k_wallpaper_{img_num + 1}.jpg"):
        print("4K壁纸下载成功!")
    else:
        print("4K壁纸下载失败!")


if __name__ == "__main__":
    main()
