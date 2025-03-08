import docx
from volcengine import maas

# 配置火山引擎 API 信息
maas_client = maas.Client()
maas_client.set_ak("AKLTZmI5OGIyNjFjYTNiNDMxN2E1NDg1ZGNlYWY1MTFiZTc==")
# 替换为你的 Secret Access Key
maas_client.set_sk(
    "TWpOaFlUZ3lNemsxTURNd05EUmxOVGswWlRZelptUXpNakJqT1RCa05HRQ ==                  ")


def read_docx(file_path):
    """
    读取 DOCX 文件内容
    :param file_path: DOCX 文件路径
    :return: 文件内容字符串
    """
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def get_score_from_maas(question, model_name="deepseek"):
    """
    调用火山引擎 MaaS API 获取作业分数
    :param question: 作业内容
    :param model_name: 使用的模型名称，默认为 deepseek
    :return: 作业分数
    """
    request = {
        "model": {
            "name": model_name
        },
        "parameters": {
            "temperature": 0.7
        },
        "messages": [
            {
                "role": "user",
                "content": f"请根据作业内容给出一个 0 - 100 的分数：{question}"
            }
        ]
    }
    try:
        response = maas_client.chat(request)
        score_text = response.get('choices', [{}])[0].get(
            'message', {}).get('content')
        # 简单处理，假设返回的内容是一个有效的分数
        try:
            score = int(score_text.strip())
            if 0 <= score <= 100:
                return score
            else:
                print("返回的分数不在 0 - 100 范围内")
                return None
        except ValueError:
            print("无法将返回内容转换为有效的分数")
            return None
    except Exception as e:
        print(f"调用 API 时出现错误: {e}")
        return None


def main(file_path):
    # 读取作业文件内容
    content = read_docx(file_path)
    # 获取作业分数
    score = get_score_from_maas(content)
    if score is not None:
        print(f"作业分数: {score}")


if __name__ == "__main__":
    file_path = "何颖怡.docx"  # 替换为你的作业文件路径
    main(file_path)
