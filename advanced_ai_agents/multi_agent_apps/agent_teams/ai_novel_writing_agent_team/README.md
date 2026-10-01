# 📖 AI Novel Writing Agent Team

**7 个职责单一的 Agent 接力写一章小说**：检索 → 大纲 → 设计 → 场景 → 门禁 → 撰稿 → 评审，
中间用一个四维记忆图谱（实体 / 时间 / 因果 / 语义）保证长篇不崩。

写长篇，模型能力不是主要瓶颈，**一致性**和**流程失控**才是。这个模板把「写一章」拆成阶段流水线：
每个 Agent 只干一件事、产物落盘、错稿在动笔前就被门禁拦下。

完整框架（配置驱动、可换任意作品）：<https://github.com/jiawood2006/novel-agent-pipeline>

## 怎么跑

**① 离线预览（不需要 API key、不需要 streamlit，只要标准库）**

```bash
python3 novel_writing_agent_team.py --dry-run
```

打印出每个 Agent 将收到的**完整提示词**与阶段产物清单，不调用任何 LLM——先看清流程再花钱。

**② 网页版（Streamlit）**

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=sk-...          # 或 OPENAI_API_KEY，任意 OpenAI 兼容接口
streamlit run novel_writing_agent_team.py
```

侧栏填书名/类型/视角/本章目标 → 点「生成章节」→ 逐阶段展开查看产出。

可选环境变量：`MODEL_BASE_URL`（默认 `https://api.deepseek.com/v1`）、`MODEL_NAME`（默认 `deepseek-chat`）。

## 流水线

| 阶段 | Agent | 输入 | 产出 | 职责 |
|:--|:--|:--|:--|:--|
| 1 | `context` | 记忆图谱 + 上一章 | `context_ch{N}.md` | 写前检索：前情 / 不能矛盾的事实 / 本章主线 |
| 2 | `outline` | context | `outline_ch{N}.md` | 事件节点 + 情绪温度曲线 + 结尾钩子 |
| 3 | `design` | outline | `design_ch{N}.md` | 每个节点怎么"展示"（场景/动作/细节）+ 埋收伏笔 |
| 4 | `scene` | design | `scene_ch{N}.md` | 拆 3-5 个可写场景，控制单场景篇幅 |
| 5 | `gate` | scene | `gate_ch{N}.json` | 四维评分门禁，不达标即拦回修改 |
| 6 | `draft` | scene + design | `draft_ch{N}.md` | 写完整正文 |
| 7 | `editor` | draft | `editor_ch{N}.json` | 规则初筛 + LLM 五维评审 |
| — | 记忆引擎 | draft | `memory.json` | 把本章事实吸收回图谱（不调 LLM） |

## 记忆图谱（四维）

| 维度 | 存什么 | 解决什么 |
|:--|:--|:--|
| entity | 人物 / 地点 / 物件的属性 | 角色设定写着写着就崩 |
| temporal | 按章记录的事件流 | 时间线前后矛盾 |
| causal | 伏笔/线索的 `open → resolved` | 挖了坑忘了填 |
| semantic | 世界观与叙事约定 | 设定漂移 |

每章**动笔前查**（写进上下文包）、**写完后写**（吸收本章事实）。

## 门禁口径（可复现）

- **p5 创意门禁**：主线推进 / 人物一致性 / 伏笔 / 节奏 四项各 0-10 分，
  **平均分 ≥ 7.0 且无单项 < 5** 才放行（阈值写死在 `gate_score()`，不随模型波动）。
- **p7 规则初筛**：只报**可观测计数**——命中的 AI 腔套话列表、连续重复词、字数、行数。
  不输出主观"AI 味分数"（避免无法复现的指标）。

## 说明

- 示例数据（《临江夜航》、沈砚等人物）为**虚构 demo**，仅用于演示流程。
- 只依赖标准库即可 `--dry-run`；真实生成需要 `streamlit` + `openai`。
