import sys
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, parse_qs
import time

def fetch_bing_search_page(url, save_path='bing_page.html'):
    """
    爬取指定URL的Bing搜索结果页面并保存
    
    Args:
        url (str): 要爬取的URL
        save_path (str): 保存文件的路径，默认为'bing_page.html'
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 发送GET请求
        print(f"正在请求URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 如果状态码不是200，抛出异常
        
        # 设置正确的编码
        response.encoding = response.apparent_encoding
        
        # 处理保存路径
        final_save_path = save_path
        
        # 检查是否传入了目录路径（以路径分隔符结尾）
        if save_path.endswith(('\\', '/')) or os.path.isdir(save_path):
            # 确保目录路径格式正确
            if not save_path.endswith(('\\', '/')):
                save_path = save_path + os.sep
            
            # 创建目录（如果不存在）
            os.makedirs(save_path, exist_ok=True)
            
            # 从URL生成文件名
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'q' in query_params:
                filename = f"bing_search_{query_params['q'][0]}.html"
            else:
                filename = f"bing_search_{int(time.time())}.html"
            
            final_save_path = os.path.join(save_path, filename)
        
        # 确保父目录存在
        parent_dir = os.path.dirname(final_save_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            print(f"已创建目录: {parent_dir}")
        
        # 使用BeautifulSoup格式化HTML（新增的格式化逻辑）
        soup = BeautifulSoup(response.text, 'html.parser')
        formatted_html = soup.prettify()
        
        # 保存格式化后的HTML内容
        with open(final_save_path, 'w', encoding='utf-8') as f:
            f.write(formatted_html)
        
        print(f"格式化后的页面已成功保存到: {final_save_path}")
        print(f"文件大小: {len(formatted_html)} 字符")
        
        # 获取页面标题
        title = soup.title.string if soup.title else "无标题"
        print(f"页面标题: {title}")
        
        # 获取搜索结果数量（如果存在）
        result_stats = soup.find('div', class_='sb_count')
        if result_stats:
            print(f"搜索结果: {result_stats.get_text()}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("请提供要爬取的URL作为参数")
        print("用法: python script.py <URL> [保存路径]")
        print("示例: python script.py \"https://cn.bing.com/search?q=爬虫翻译\"")
        print("示例: python script.py \"https://cn.bing.com/search?q=爬虫翻译\" \"D:\\output\\\"")
        print("示例: python script.py \"https://cn.bing.com/search?q=爬虫翻译\" \"my_page.html\"")
        return
    
    # 获取目标URL
    target_url = sys.argv[1]
    
    # 获取可选的保存路径（默认为'bing_page.html'）
    save_path = sys.argv[2] if len(sys.argv) > 2 else 'bing_page.html'
    
    # 爬取页面
    success = fetch_bing_search_page(target_url, save_path)
    
    if success:
        print("爬取任务完成!")
    else:
        print("爬取任务失败!")

if __name__ == "__main__":
    main()