"""
FastAPI 客户端示例
=============================================

功能：
  - 调用 FastAPI /process 端点发送用户输入并获取 LangGraph 工作流处理结果
  - 演示如何与中医知识图谱服务进行 HTTP 通信
  - 包含完善的异常处理（连接失败、超时、HTTP 错误等）

使用方式：
  1. 先启动服务端: python __005__fastapi/__001__langgraph_fastapi.py
  2. 再运行本客户端: python __005__fastapi/__002__langgraph_fastapi_client.py

注意事项：
  - 本文件是命令行示例客户端，仅调用非流式 /process 端点
  - Streamlit 前端使用 utils/api.py 中的封装函数，功能更完善（含流式 SSE 支持）
"""

import sys

import requests


def query_zhongyi_fastapi(user_input: str) -> str:
    """调用中医 FastAPI 服务，发送用户输入并获取 LangGraph 工作流处理结果。

    向 http://127.0.0.1:8000/process 发送 POST 请求，
    请求体中包含 {"input": user_input}。
    服务端通过 LangGraph 自动判断意图并路由到对应处理链路。

    参数:
        user_input: 用户输入文本，支持中医问题、小红书发布指令等

    返回:
        str: LangGraph 工作流的处理结果（Markdown 格式文本）

    异常处理:
        - ConnectionError:  服务未启动或网络不可达 → stderr 输出提示并退出
        - Timeout:          请求超过 120 秒 → stderr 输出超时提示并退出
        - HTTPError:        服务端返回非 2xx 状态码 → stderr 输出错误详情并退出
        - 其他异常:          统一捕获 → stderr 输出错误信息并退出
    """
    # FastAPI /process 端点的完整 URL
    url = "http://127.0.0.1:8000/process"
    # 构造请求体，仅需 input 字段
    payload = {"input": user_input}

    try:
        # 发送 POST 请求，超时设为 120 秒（LangGraph 工作流可能耗时较长）
        res = requests.post(url, json=payload, timeout=120)
        # 检查 HTTP 状态码，非 2xx 时抛出 HTTPError
        res.raise_for_status()
        # 解析 JSON 响应获取 output 字段
        json_dict = res.json()
        return json_dict.get("output", "")
    except requests.exceptions.ConnectionError:
        # 连接被拒绝：通常意味着 FastAPI 服务未启动
        print("❌ 无法连接到 FastAPI 服务，请确认服务已启动（python __001__langgraph_fastapi.py）", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        # 请求超时：LangGraph 工作流执行时间超过 120 秒
        print("❌ 请求超时（120s），工作流可能耗时过长", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        # HTTP 错误：服务端返回了错误状态码（4xx/5xx）
        print(f"❌ 服务端返回错误: {e}", file=sys.stderr)
        # 尝试从响应体中读取详细错误信息（FastAPI 会返回 {"output": "错误详情"}）
        try:
            error_detail = res.json()
            print(f"   详情: {error_detail.get('output', '无')}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        # 其他未预期的异常
        print(f"❌ 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    # 示例：发送 "你好" 到服务端并打印结果
    # 实际使用时替换为任意中医问题或小红书发布指令
    result = query_zhongyi_fastapi("你好")
    print(result)
