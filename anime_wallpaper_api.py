#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动漫壁纸API - 随机动漫壁纸获取工具
基于 https://img.8845.top/random.php 的API接口
API文档: https://api.aa1.cn/doc/json.html
"""

import requests
import json
import os
from typing import Optional, Dict, Any
import logging
from myAPI import count_files_in_directory, get_image_format_from_url, download_and_set_wallpaper

# 配置日志
try:
    from logging_config import get_logger
    logger = get_logger("animeWallpaperAPI")
    logger.propagate = False
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("animeWallpaperAPI")
    logger.propagate = False

class AnimeWallpaperAPI:
    """动漫壁纸API获取类"""
    
    def __init__(self):
        self.base_url = "https://img.8845.top/random.php"
        self.api_name = "FengAPI"
    
    def get_random_anime_wallpaper(self) -> Dict[str, Any]:
        """
        获取随机动漫壁纸信息
        
        Returns:
            API响应数据，包含以下字段：
            - API_name: API名称
            - IP: 你的IP地址
            - image_links: 图片链接
            - Image_status: 图片状态
            - delay: 延迟时间
        """
        try:
            logger.info("正在获取随机动漫壁纸...")
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            logger.info(f"成功获取动漫壁纸，延迟: {data.get('delay', 'N/A')}")
            return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return {"error": f"请求失败: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return {"error": f"数据解析失败: {str(e)}"}
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {"error": f"未知错误: {str(e)}"}
    
    def download_anime_wallpaper(self, save_path: Optional[str] = None) -> bool:
        """
        下载动漫壁纸到本地
        
        Args:
            save_path: 保存路径，如果为None则自动生成
            
        Returns:
            是否下载成功
        """
        try:
            # 获取壁纸信息
            result = self.get_random_anime_wallpaper()
            
            if "error" in result:
                logger.error(f"获取动漫壁纸失败: {result['error']}")
                return False
            
            # 检查图片状态
            if result.get("Image_status") != "ok":
                logger.error(f"图片状态异常: {result.get('Image_status')}")
                return False
            
            image_url = result.get("image_links")
            if not image_url:
                logger.error("未获取到图片链接")
                return False
            
            # 生成保存路径
            if save_path is None:
                img_num = count_files_in_directory('images')
                img_format = get_image_format_from_url(image_url)
                save_path = f"images/anime_wallpaper_{img_num + 1}.{img_format}"
            
            # 确保images目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 下载并设置壁纸
            success = download_and_set_wallpaper(image_url, save_path)
            
            if success:
                logger.info(f"动漫壁纸已保存到: {save_path}")
                logger.info(f"API信息 - 名称: {result.get('API_name')}, 延迟: {result.get('delay')}")
                return True
            else:
                logger.error("下载动漫壁纸失败")
                return False
            
        except Exception as e:
            logger.error(f"下载动漫壁纸失败: {e}")
            return False
    
    def get_wallpaper_info_only(self) -> Dict[str, Any]:
        """
        仅获取壁纸信息，不下载
        
        Returns:
            壁纸信息字典
        """
        return self.get_random_anime_wallpaper()
    
    def test_api_connection(self) -> bool:
        """
        测试API连接是否正常
        
        Returns:
            连接是否成功
        """
        try:
            result = self.get_random_anime_wallpaper()
            return "error" not in result and result.get("Image_status") == "ok"
        except Exception:
            return False


def main():
    """主函数 - 演示API使用"""
    api = AnimeWallpaperAPI()
    
    print("=== 动漫壁纸API - 随机动漫壁纸获取工具 ===")
    print("API地址: https://img.8845.top/random.php")
    print("API文档: https://api.aa1.cn/doc/json.html")
    print()
    
    # 测试API连接
    print("1. 测试API连接:")
    if api.test_api_connection():
        print("✓ API连接正常")
    else:
        print("✗ API连接失败")
        return
    print()
    
    # 获取壁纸信息
    print("2. 获取随机动漫壁纸信息:")
    result = api.get_wallpaper_info_only()
    if "error" not in result:
        print("API响应信息:")
        print(f"  API名称: {result.get('API_name', 'N/A')}")
        print(f"  IP地址: {result.get('IP', 'N/A')}")
        print(f"  图片状态: {result.get('Image_status', 'N/A')}")
        print(f"  响应延迟: {result.get('delay', 'N/A')}")
        print(f"  图片链接: {result.get('image_links', 'N/A')}")
    else:
        print(f"错误: {result['error']}")
    print()
    
    # 下载并设置壁纸
    print("3. 下载并设置动漫壁纸:")
    if api.download_anime_wallpaper():
        print("✓ 动漫壁纸下载并设置成功!")
    else:
        print("✗ 动漫壁纸下载失败!")
    print()
    
    # 显示当前图片数量
    img_count = count_files_in_directory('images')
    print(f"当前images文件夹中共有 {img_count} 张图片")


if __name__ == "__main__":
    main()
