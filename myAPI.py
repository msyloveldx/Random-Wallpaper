import ctypes
import os
import random
import requests
import logging
from PIL import Image, ImageEnhance

try:
    from logging_config import get_logger
    logger = get_logger("myAPI")
    logger.propagate = False
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("myAPI")
    logger.propagate = False


def set_wallpaper(image_path):
    try:
        # 确保路径是绝对路径
        abs_path = os.path.abspath(image_path)
        logger.info(f"Setting wallpaper with path: {abs_path}")
        
        # Windows系统设置壁纸
        if os.name == 'nt':
            SPI_SETDESKWALLPAPER = 20
            SPIF_UPDATEINIFILE = 1
            SPIF_SENDCHANGE = 2
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )
            if result:
                logger.info("Wallpaper set successfully on Windows")
                return True
            else:
                logger.error("Failed to set wallpaper on Windows")
                return False
        # macOS系统设置壁纸
        elif os.name == 'posix' and os.uname().sysname == 'Darwin':
            os.system(f"""osascript -e 'tell application "Finder" to set desktop picture to POSIX file "{abs_path}"'""")
            logger.info("Wallpaper set successfully on macOS")
            return True
        # Linux系统设置壁纸(GNOME)
        elif os.name == 'posix':
            os.system(f"gsettings set org.gnome.desktop.background picture-uri 'file://{abs_path}'")
            logger.info("Wallpaper set successfully on Linux")
            return True
    except Exception as e:
        logger.error(f"Error setting wallpaper: {e}")
        return False
    
    return False


def download_and_set_wallpaper(image_url, save_path):
    try:
        # 从API下载图片
        logger.info(f"Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=30)
        if response.status_code != 200:
            logger.error(f"Failed to download image from {image_url}, status code: {response.status_code}")
            return False
            
        # 确保images目录存在
        if not os.path.exists('images'):
            os.makedirs('images')
            logger.info("Created images directory")

        # 保存图片
        with open(save_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Image saved to: {save_path}")

        # 图片清晰化处理
        # image = Image.open(save_path)
        # image.save(save_path, quality=95, dpi=(720, 720), optimize=True)
        clear_image(save_path)

        # 验证文件是否存在
        if not os.path.exists(save_path):
            logger.error(f"Saved file does not exist: {save_path}")
            return False

        # 设置壁纸
        set_wallpaper(save_path)
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while downloading image: {e}")
        return False
    except Exception as e:
        logger.error(f"Error in download_and_set_wallpaper: {e}")
        return False

# 统计images目录下的文件数量
def count_files_in_directory(directory_path):
    try:
        if not os.path.exists(directory_path):
            logger.info(f"Directory {directory_path} does not exist")
            return 0
            
        file_count = 0
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) and item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                file_count += 1
        logger.info(f"Found {file_count} image files in {directory_path}")
        return file_count
    except Exception as e:
        logger.error(f"Error counting files in directory: {e}")
        return 0


# 获取图片格式
def get_image_format_from_url(image_url):
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        content_type = response.headers.get('Content-Type', '')

        # 处理可能的附加参数如charset
        mime_type = content_type.split(';')[0].strip().lower()

        # 常见图片MIME类型映射
        mime_to_extension = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/bmp': 'bmp',
            'image/webp': 'webp',
            'image/svg+xml': 'svg'
        }

        extension = mime_to_extension.get(mime_type, 'jpg')  # 默认使用jpg
        logger.info(f"Detected MIME type: {mime_type}, using extension: {extension}")
        return extension
        
    except Exception as e:
        logger.error(f"Error getting image format: {e}")
        return 'jpg'  # 默认返回jpg

# 获取随机图片api的随机地址
def get_random_image_api(api_type):
    api_urls = {
        'api1': 'https://api.btstu.cn/sjbz/api.php',        # 随机各类壁纸
        'api2': 'https://api.paugram.com/wallpaper/',    # 随机动漫壁纸
        'api3': 'https://cdn.seovx.com/d/?mom=302',      # 随机二次元
        'api4': 'https://cdn.seovx.com/?mom=302',        # 随机美图
        'api5': 'https://cdn.seovx.com/ha/?mom=302',     # 随机古风
        'api6': 'https://www.dmoe.cc/random.php',        # 樱花二次元
    }

    try:
        # 如果api_type在预定义的API列表中，直接返回对应的URL
        if api_type in api_urls:
            api_url = api_urls[api_type]
            logger.info(f"用户指定系统中的api：{api_url}")
            return api_url
        # 如果api_type是'random'，随机选择一个API
        elif api_type == 'random':
            api_url = random.choice(list(api_urls.values()))
            logger.info(f"用户选择随机api：{api_url}")
            return api_url
        # 其他情况，使用默认的api2
        else:
            api_url = api_urls['api2']
            logger.info(f"用户未指定有效的api，使用默认api2：{api_url}")
            return api_url
            
    except Exception as e:
        logger.error(f"Error getting random image API: {e}")
        return ''


# 将api获取的【随机图片】进行清晰化处理
def clear_image(save_path):
    logger.info("Clearing image...")
    # 打开图片
    image = Image.open(save_path)

    # 调整对比度
    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(1.2)  # 1.5倍对比度增强

    # # 调整亮度
    # brightness = ImageEnhance.Brightness(image)
    # image = brightness.enhance(1.2)  # 1.2倍亮度增强
    #
    # # 锐化处理
    # sharpness = ImageEnhance.Sharpness(image)
    # image = sharpness.enhance(2.0)  # 2.0倍锐化

    image.save(save_path, quality=95, dpi=(500, 500), optimize=True)

# 使用示例
if __name__ == '__main__':
    try:
        # 检查images目录是否存在，如果不存在则创建
        if not os.path.exists('images'):
            os.makedirs('images')
            logger.info("Created images directory")

        api_url = ''
        api_type = 'api2'

        img_num = count_files_in_directory('images')
        logger.info(f"Found {img_num} existing images")

        if api_url:
            image_url = api_url
            logger.info(f"用户指定api：{image_url}")
        else:
            image_url = get_random_image_api(api_type)  # 随机API端点
            logger.info(f"用户未指定api，应用默认随机api：{image_url}")
        
        img_type = get_image_format_from_url(image_url)
        logger.info(f"Detected image type: {img_type}")
        
        save_path = f"images/img_{img_num + 1}.{img_type}"  # 替换为您想保存的路径
        logger.info(f"Save path: {save_path}")
        
        success = download_and_set_wallpaper(image_url, save_path)
        if success:
            logger.info("Wallpaper set successfully!")
            print("壁纸设置成功！")
        else:
            logger.error("Failed to set wallpaper")
            print("壁纸设置失败，请查看日志文件")
            
    except Exception as e:
        logger.error(f"Main program error: {e}")
        print(f"程序运行出错: {e}")