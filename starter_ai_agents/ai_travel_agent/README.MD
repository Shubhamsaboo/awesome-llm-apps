# AI 旅行规划师（改造版）

一个基于大模型的个性化旅行行程生成器：输入目的地和天数，AI 自动输出**按天分时段（上午 / 中午 / 下午 / 晚上 / 住宿）的详细行程**，并在每天结尾给出**当日预算估算**。支持单城市规划，并可一键导出 `.ics` 日历。

> 本项目 fork 自 [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) 的 `starter_ai_agents/ai_travel_agent`，在原版基础上做了自主改造（详见下方「相对原版的改动」）。原仓库采用 Apache-2.0 许可证，本派生项目沿用相同许可证。

---

## 相对原版的改动（自主开发部分）

| 改动点 | 说明 |
| --- | --- |
| 去除付费依赖 | 移除原版强制要求的 SerpAPI 联网搜索，仅用大模型自身知识生成行程，零额外付费。 |
| 切换模型接入方式 | 将模型从 OpenAI + agno Agent 框架改为 **DeepSeek 直连**（OpenAI SDK 标准调用），规避框架与接口的兼容问题，代码更简洁。 |
| 简化交互 | 界面只保留一个 API Key 输入框，降低使用门槛。 |
| 结构化行程排版 | 在提示词中固定输出格式：每天一个主题大标题，并按 `上午 / 中午 / 下午 / 晚上 / 住宿` 分段论述，阅读更清晰。 |
| 每日预算估算 | 让 AI 在每一天结尾输出当日预算明细（住宿 / 餐饮 / 交通 / 门票），并在页面顶部汇总多日总花费。 |

以上均为**业务逻辑 / 交互层面**的实质性改动，非仅替换配色或文本。

---

## 技术栈

- **前端 / 界面**：Streamlit
- **后端 / 模型调用**：DeepSeek `deepseek-chat`（OpenAI 兼容接口，Python `openai` SDK 直连）
- **日历导出**：`icalendar`
- **语言**：Python 3.12

---

## 环境要求

- Windows（已验证）/ macOS / Linux
- Python 3.10+
- 一个可用的 **DeepSeek API Key**（在 https://platform.deepseek.com 的 API Keys 页面免费创建）

---

## 运行方式（推荐：一键启动）

1. 双击本目录下的 **`run.bat`**，程序会自动启动并在浏览器打开 `http://127.0.0.1:8501`。
   - 首次启动只需按一次回车跳过 Streamlit 的欢迎问卷，之后不再提示。
2. 在页面中粘贴你的 DeepSeek API Key，填写目的地与天数，点击「生成行程」。
3. 等待十几秒，即可看到结构化行程；可点击「下载行程日历 (.ics)」保存。

> 若不使用 `run.bat`，也可手动在终端执行：
> ```bash
> pip install -r requirements.txt
> streamlit run my_travel_agent.py
> ```

---

## 项目文件说明

| 文件 | 作用 |
| --- | --- |
| `my_travel_agent.py` | 主程序：DeepSeek 调用 + Streamlit 界面 + 行程 / 预算逻辑 |
| `run.bat` | Windows 一键启动脚本（自动清理端口冲突） |
| `requirements.txt` | Python 依赖清单 |

---

## 许可证

基于 [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)（Apache-2.0）派生，遵循 **Apache-2.0** 许可证。改造部分同样以 Apache-2.0 开源。

---

## 可继续扩展的方向

- 多城市行程并排对比
- 行程卡片化 / 地图可视化
- 接入联网搜索（需另行配置搜索 API）
