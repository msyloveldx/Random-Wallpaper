#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态壁纸API - 随机动态壁纸视频获取工具
基于 https://i18.net/video.php 的API接口
API文档: https://api.aa1.cn/doc/pcwallpaper.html
"""

import requests
import json
import os
from typing import Optional, Dict, Any
import logging
from myAPI import count_files_in_directory

# 配置日志
try:
    from logging_config import get_logger
    logger = get_logger("dynamicWallpaperAPI")
    logger.propagate = False
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("dynamicWallpaperAPI")
    logger.propagate = False

class DynamicWallpaperAPI:
    """动态壁纸API获取类"""
    
    def __init__(self):
        self.base_url = "https://i18.net/video.php"
        self.api_name = "HudsonAPI"
    
    def get_random_dynamic_wallpaper(self) -> Dict[str, Any]:
        """
        获取随机动态壁纸视频信息
        
        Returns:
            API响应数据，包含以下字段：
            - success: 成功与否 (boolean)
            - message: 请求结果信息 (string)
            - video_url: 视频的地址 (string)
        """
        try:
            logger.info("正在获取随机动态壁纸视频...")
            # 添加return=json参数确保返回JSON格式
            params = {"return": "json"}
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            logger.info(f"成功获取动态壁纸视频，状态: {data.get('success', 'N/A')}")
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
    
    def download_dynamic_wallpaper(self, save_path: Optional[str] = None) -> bool:
        """
        下载动态壁纸视频到本地
        
        Args:
            save_path: 保存路径，如果为None则自动生成
            
        Returns:
            是否下载成功
        """
        try:
            # 获取视频信息
            result = self.get_random_dynamic_wallpaper()
            
            if "error" in result:
                logger.error(f"获取动态壁纸失败: {result['error']}")
                return False
            
            # 检查请求状态
            if not result.get("success", False):
                logger.error(f"API返回失败: {result.get('message', '未知错误')}")
                return False
            
            video_url = result.get("video_url")
            if not video_url:
                logger.error("未获取到视频链接")
                return False
            
            # 生成保存路径
            if save_path is None:
                video_num = count_files_in_directory('videos')
                save_path = f"videos/dynamic_wallpaper_{video_num + 1}.mp4"
            
            # 确保videos目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 下载视频
            success = self._download_video(video_url, save_path)
            
            if success:
                logger.info(f"动态壁纸视频已保存到: {save_path}")
                logger.info(f"API信息 - 状态: {result.get('success')}, 消息: {result.get('message')}")
                return True
            else:
                logger.error("下载动态壁纸视频失败")
                return False
            
        except Exception as e:
            logger.error(f"下载动态壁纸视频失败: {e}")
            return False
    
    def _download_video(self, video_url: str, save_path: str) -> bool:
        """
        下载视频文件
        
        Args:
            video_url: 视频URL
            save_path: 保存路径
            
        Returns:
            是否下载成功
        """
        try:
            logger.info(f"正在下载视频: {video_url}")
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            logger.info(f"下载进度: {progress:.1f}% ({downloaded_size}/{total_size} bytes)")
            
            logger.info(f"视频下载完成: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"下载视频失败: {e}")
            return False
        except Exception as e:
            logger.error(f"保存视频失败: {e}")
            return False
    
    def get_wallpaper_info_only(self) -> Dict[str, Any]:
        """
        仅获取动态壁纸信息，不下载
        
        Returns:
            动态壁纸信息字典
        """
        return self.get_random_dynamic_wallpaper()
    
    def test_api_connection(self) -> bool:
        """
        测试API连接是否正常
        
        Returns:
            连接是否成功
        """
        try:
            result = self.get_random_dynamic_wallpaper()
            return "error" not in result and result.get("success", False)
        except Exception:
            return False
    
    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        获取视频文件信息
        
        Args:
            video_url: 视频URL
            
        Returns:
            视频信息字典
        """
        try:
            logger.info(f"正在获取视频信息: {video_url}")
            response = requests.head(video_url, timeout=10)
            response.raise_for_status()
            
            headers = response.headers
            return {
                "content_type": headers.get("content-type", "unknown"),
                "content_length": headers.get("content-length", "unknown"),
                "last_modified": headers.get("last-modified", "unknown"),
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {"error": str(e)}


def count_video_files_in_directory(directory_path: str) -> int:
    """
    统计指定目录下的视频文件数量
    
    Args:
        directory_path: 目录路径
        
    Returns:
        视频文件数量
    """
    try:
        if not os.path.exists(directory_path):
            logger.info(f"Directory {directory_path} does not exist")
            return 0
            
        file_count = 0
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) and item.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')):
                file_count += 1
        logger.info(f"Found {file_count} video files in {directory_path}")
        return file_count
    except Exception as e:
        logger.error(f"Error counting video files in directory: {e}")
        return 0


def main():
    """主函数 - 演示API使用"""
    api = DynamicWallpaperAPI()
    
    print("=== 动态壁纸API - 随机动态壁纸视频获取工具 ===")
    print("API地址: https://i18.net/video.php")
    print("API文档: https://api.aa1.cn/doc/pcwallpaper.html")
    print()
    
    # 测试API连接
    print("1. 测试API连接:")
    if api.test_api_connection():
        print("✓ API连接正常")
    else:
        print("✗ API连接失败")
        return
    print()
    
    # 获取动态壁纸信息
    print("2. 获取随机动态壁纸视频信息:")
    result = api.get_wallpaper_info_only()
    if "error" not in result:
        print("API响应信息:")
        print(f"  成功状态: {result.get('success', 'N/A')}")
        print(f"  消息: {result.get('message', 'N/A')}")
        print(f"  视频链接: {result.get('video_url', 'N/A')}")
        
        # 获取视频详细信息
        video_url = result.get('video_url')
        if video_url:
            print("\n3. 获取视频详细信息:")
            video_info = api.get_video_info(video_url)
            if "error" not in video_info:
                print(f"  内容类型: {video_info.get('content_type', 'N/A')}")
                print(f"  文件大小: {video_info.get('content_length', 'N/A')} bytes")
                print(f"  最后修改: {video_info.get('last_modified', 'N/A')}")
                print(f"  状态码: {video_info.get('status_code', 'N/A')}")
            else:
                print(f"  获取视频信息失败: {video_info['error']}")
    else:
        print(f"错误: {result['error']}")
    print()
    
    # 下载动态壁纸视频
    print("4. 下载动态壁纸视频:")
    if api.download_dynamic_wallpaper():
        print("✓ 动态壁纸视频下载成功!")
    else:
        print("✗ 动态壁纸视频下载失败!")
    print()
    
    # 显示当前视频数量
    video_count = count_video_files_in_directory('videos')
    print(f"当前videos文件夹中共有 {video_count} 个视频文件")
    
    # 显示使用说明
    print("\n=== 使用说明 ===")
    print("1. 动态壁纸视频已下载到 videos/ 目录")
    print("2. 您可以使用支持动态壁纸的软件来设置这些视频作为桌面壁纸")
    print("3. 推荐软件: Wallpaper Engine (Steam), Lively Wallpaper 等")
    print("4. 注意: 动态壁纸会消耗更多系统资源，请根据电脑性能选择使用")


if __name__ == "__main__":
    main()
