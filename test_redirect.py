#!/usr/bin/env python
"""
测试重定向问题的脚本
"""

import os
import sys
from urllib.parse import urlparse

import django
import requests

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")
django.setup()


def test_redirect():
    """测试重定向问题"""
    print("🔍 测试重定向问题...")

    base_urls = [
        "http://127.0.0.1:8000/",
        "http://localhost:8000/",
        "http://127.0.0.1:8001/",
    ]

    for url in base_urls:
        print(f"\n📡 测试URL: {url}")
        try:
            # 发送请求，不自动跟随重定向
            response = requests.get(url, allow_redirects=False, timeout=5)

            print(f"   状态码: {response.status_code}")

            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get("Location", "未找到Location头")
                print(f"   ❌ 发现重定向到: {location}")
            elif response.status_code == 200:
                print(f"   ✅ 正常响应")
                # 检查响应内容
                if "stocks" in response.text.lower():
                    print(f"   ⚠️  响应内容中包含'stocks'")
                else:
                    print(f"   ✅ 响应内容正常")
            else:
                print(f"   ⚠️  其他状态码: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败 - 服务器可能未运行")
        except requests.exceptions.Timeout:
            print(f"   ❌ 请求超时")
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")


def test_stocks_url():
    """测试stocks URL"""
    print(f"\n🔍 测试 /stocks/ 路径...")

    url = "http://127.0.0.1:8000/stocks/"
    try:
        response = requests.get(url, allow_redirects=False, timeout=5)
        print(f"   状态码: {response.status_code}")

        if response.status_code == 404:
            print(f"   ✅ 正确返回404 - 路径不存在")
        else:
            print(f"   ⚠️  意外的状态码: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"   ❌ 连接失败")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")


def check_django_urls():
    """检查Django URL配置"""
    print(f"\n🔍 检查Django URL配置...")

    from django.conf import settings
    from django.urls import reverse

    try:
        # 检查根URL
        root_url = reverse("home")
        print(f"   根URL配置: {root_url}")

        # 检查是否有stocks相关的URL
        from django.urls import get_resolver

        resolver = get_resolver()

        # 获取所有URL模式
        all_patterns = []

        def collect_patterns(patterns, prefix=""):
            for pattern in patterns:
                if hasattr(pattern, "url_patterns"):
                    collect_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
                else:
                    all_patterns.append(prefix + str(pattern.pattern))

        collect_patterns(resolver.url_patterns)

        stocks_patterns = [p for p in all_patterns if "stocks" in p.lower()]
        if stocks_patterns:
            print(f"   ⚠️  发现stocks相关URL: {stocks_patterns}")
        else:
            print(f"   ✅ 没有发现stocks相关URL")

    except Exception as e:
        print(f"   ❌ 检查URL配置失败: {e}")


def main():
    """主函数"""
    print("🚀 重定向问题诊断工具")
    print("=" * 50)

    check_django_urls()
    test_redirect()
    test_stocks_url()

    print(f"\n💡 解决建议:")
    print(f"   1. 清除浏览器缓存 (Ctrl+Shift+R)")
    print(f"   2. 使用隐私模式访问")
    print(f"   3. 检查浏览器代理设置")
    print(f"   4. 尝试使用 localhost:8000 而不是 127.0.0.1:8000")
    print(f"   5. 检查浏览器的自动完成历史")


if __name__ == "__main__":
    main()
