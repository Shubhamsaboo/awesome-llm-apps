# AI 旅行规划师（LangGraph 改造版）

一个基于大模型的个性化旅行行程生成器。输入目的地和天数，Agent 会生成按天分时段的详细行程，并调用预算工具计算住宿、餐饮、交通和门票总费用。生成结果支持导出为 `.ics` 日历。

> 本项目 fork 自 [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) 的 `starter_ai_agents/ai_travel_agent`。原仓库采用 Apache-2.0 许可证，本派生项目沿用相同许可证。

## 相对原版的改动

| 改动点 | 说明 |
| --- | --- |
| 去除付费搜索依赖 | 移除了原版必须配置的 SerpAPI，使用 DeepSeek 生成行程。 |
| 切换模型接入方式 | 使用 `langchain-openai` 的 `ChatOpenAI` 兼容接口连接 DeepSeek。 |
| 引入 LangGraph 工作流 | 把请求校验、模型生成、工具调用和最终输出组织成可追踪的状态图。 |
| 增加预算工具 | `calculate_trip_budget` 由代码执行确定性计算，不再用正则从自然语言中猜总价。 |
| 增加输入分支 | 目的地或天数不合法时，工作流直接结束，不调用大模型。 |
| 分离页面和业务代码 | Streamlit 页面留在 `my_travel_agent.py`，Agent 逻辑放进 `travel_graph.py`。 |
| 结构化行程 | 每天按上午、中午、下午、晚上、住宿和当日预算分段输出。 |

核心流程：

```text
START
  ↓
validate_request
  ├─ 输入不合法 → END
  └─ 输入合法 → assistant
                  ├─ 需要预算 → tools → assistant
                  └─ 输出完成 → END
```

## 技术栈

- **界面**：Streamlit
- **Agent 工作流**：LangGraph
- **模型调用与工具绑定**：LangChain、DeepSeek `deepseek-chat`
- **数据校验**：Pydantic
- **日历导出**：icalendar
- **Python**：3.10+

## 首次配置

在 `starter_ai_agents/ai_travel_agent` 目录打开 PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-langgraph.txt
```

如果国内网络导致下载很慢，或出现 `HASHES DO NOT MATCH`，改用清华镜像重试：

```powershell
.\.venv\Scripts\python.exe -m pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-langgraph.txt
```

如果把命令提示符里的路径写错了，先执行：

```powershell
cd D:\AgentDev\repos\starter_ai_agents\ai_travel_agent
```

然后双击同目录下的 `run.bat`。启动后访问：

```text
http://127.0.0.1:8501
```

在页面中填写自己的 DeepSeek API Key、目的地和旅行天数，再点击“生成行程”。

也可以手动启动：

```powershell
.\.venv\Scripts\python.exe -m streamlit run my_travel_agent.py
```

## 自动检查

运行不需要 API Key 的单元测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

当前检查包括：

- 预算工具的计算结果是否正确。
- 空目的地是否在调用模型前被拦截。
- UI 是否能从工具消息中读取总预算。

## 项目文件

| 文件 | 作用 |
| --- | --- |
| `my_travel_agent.py` | Streamlit 页面和日历导出 |
| `travel_graph.py` | LangGraph 状态、图节点、预算工具和模型调用 |
| `tests/test_travel_graph.py` | 不消耗 API Token 的自动测试 |
| `requirements-langgraph.txt` | 改造版依赖 |
| `run.bat` | 使用项目虚拟环境的一键启动脚本 |

## 面试时怎么讲

我先把原项目跑通，再把单次模型调用改成 LangGraph 状态图：输入先经过校验节点，合法请求进入模型节点；模型通过工具调用请求预算计算，工具节点按结构化参数返回总价，随后回到模型生成最终行程。这样预算结果由代码保证确定性，同时保留了 LangGraph 的工具循环和条件分支。

## 许可证

基于 [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)（Apache-2.0）派生，遵循 **Apache-2.0** 许可证。
