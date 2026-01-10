#!/usr/bin/env python
"""
API测试脚本 - 使用requests直接测试API端点
"""

import requests
import json


def test_save_teacher_comment_api():
    """测试save_teacher_comment API端点"""
    print("=== 测试 save_teacher_comment API ===")
    
    # API端点
    url = "http://127.0.0.1:8000/grading/save_teacher_comment/"
    
    # 测试数据
    data = {
        'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
        'comment': '测试评价：作业完成质量良好，需要注意格式规范。',
        'grade': 'B',
        'repo_id': '11',
        'course': 'Web前端开发'
    }
    
    print(f"请求URL: {url}")
    print(f"请求数据: {data}")
    
    try:
        # 发送POST请求（不带认证，测试错误处理）
        response = requests.post(url, data=data, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print(f"JSON响应: {json.dumps(json_response, ensure_ascii=False, indent=2)}")
        except:
            print(f"文本响应: {response.text[:500]}...")
        
        # 分析响应
        if response.status_code == 200:
            print("✅ API响应成功")
            return True
        elif response.status_code == 400:
            print("⚠️  请求被拒绝（可能是认证或参数问题）")
            return False
        elif response.status_code == 403:
            print("⚠️  权限不足（需要登录）")
            return False
        elif response.status_code == 500:
            print("❌ 服务器内部错误")
            return False
        else:
            print(f"❓ 未知状态码: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 服务器可能未运行")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {type(e).__name__}: {e}")
        return False


def test_get_teacher_comment_api():
    """测试get_teacher_comment API端点"""
    print("\n=== 测试 get_teacher_comment API ===")
    
    # API端点
    url = "http://127.0.0.1:8000/grading/get_teacher_comment/"
    
    # 测试参数
    params = {
        'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
        'repo_id': '11',
        'course': 'Web前端开发'
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        # 发送GET请求
        response = requests.get(url, params=params, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print(f"JSON响应: {json.dumps(json_response, ensure_ascii=False, indent=2)}")
        except:
            print(f"文本响应: {response.text[:500]}...")
        
        # 分析响应
        if response.status_code == 200:
            print("✅ API响应成功")
            return True
        else:
            print(f"⚠️  API响应异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {type(e).__name__}: {e}")
        return False


def check_server_status():
    """检查服务器状态"""
    print("=== 检查服务器状态 ===")
    
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"服务器状态: {response.status_code}")
        return response.status_code == 200
    except:
        print("❌ 服务器无法访问")
        return False


if __name__ == '__main__':
    print("开始API测试...\n")
    
    # 检查服务器状态
    server_ok = check_server_status()
    
    if not server_ok:
        print("服务器不可用，请先启动Django开发服务器")
        exit(1)
    
    # 测试GET API（应该能工作）
    get_success = test_get_teacher_comment_api()
    
    # 测试POST API（测试我们的修复）
    save_success = test_save_teacher_comment_api()
    
    print(f"\n=== 测试结果总结 ===")
    print(f"服务器状态: {'✅ 正常' if server_ok else '❌ 异常'}")
    print(f"get_teacher_comment: {'✅ 成功' if get_success else '❌ 失败'}")
    print(f"save_teacher_comment: {'✅ 成功' if save_success else '❌ 失败'}")
    
    if save_success:
        print("\n🎉 修复验证成功！")
    else:
        print("\n📝 说明: 失败可能是由于认证问题，但重要的是检查错误处理是否改善")