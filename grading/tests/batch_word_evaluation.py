import os

from docx import Document
from volcenginesdkarkruntime import Ark


def read_word_file(file_path):
    """读取 Word 文件内容"""
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


def get_ai_evaluation(api_key, text):
    """调用火山引擎 AI 获取成绩和评价"""
    client = Ark(api_key=api_key)
    prompt = f"请阅读以下内容并给出成绩和 50 字以内的评价：\n{text}"
    try:
        resp = client.chat.completions.create(
            model="deepseek-r1-250528",
            messages=[{"content": prompt, "role": "user"}],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"请求出错：{str(e)}"


def process_multiple_files(api_key, file_paths):
    """处理多个 Word 文件"""
    results = {}
    for file_path in file_paths:
        try:
            text = read_word_file(file_path)
            evaluation = get_ai_evaluation(api_key, text)
            results[file_path] = evaluation
        except Exception as e:
            results[file_path] = f"处理文件出错：{str(e)}"
    return results


if __name__ == "__main__":
    # 从环境变量获取 API Key
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("请设置 ARK_API_KEY 环境变量")
        print("示例: export ARK_API_KEY=your_api_key_here")
    else:
        # 请替换为你的 Word 文件路径列表
        file_paths = [
            "/Users/linyuan/jobs/22g-class-java-homework/第二次作业/曾思琪.docx",
            # 可添加更多文件路径
        ]
        results = process_multiple_files(api_key, file_paths)
        for file_path, result in results.items():
            print(f"文件: {file_path}")
            print(f"结果: {result}")
            print("-")
