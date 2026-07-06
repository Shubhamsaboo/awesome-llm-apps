# 🗺️ awesome-llm-apps — 未来12个月更新路线图

> **仓库**: ghshhf/awesome-llm-apps (fork from Shubhamsaboo/awesome-llm-apps)
> **时间范围**: 2026年7月 — 2027年6月
> **当前状态**: 文档质量冲刺完成，CI 基础设施就绪，1025 次提交，落后上游 4 个提交

---

## 一、现状评估

### ✅ 已完成的基础设施
- CI 工作流：lint_and_test.yml + ruff.toml
- 公共依赖管理：根目录 requirements.txt
- 全仓库零破损链接（从 68→0）
- 14 个分类目录已建立
- 约 100+ 个可运行模板

### ⚠️ 关键差距（作为 fork 的独特机会）
| 维度 | 上游状态 | 本 fork 可做的差异化 |
|------|---------|-------------------|
| 国产模型 | 仅支持基础 OpenAI API | 深度集成 DeepSeek/Qwen/GLM 等 |
| 中文生态 | 英文为主，有 1 个 zh README | 全量中文文档 + 本土案例 |
| 企业级增强 | 侧重演示级代码 | 添加生产级加固（错误处理、日志、限流） |
| 测试覆盖 | 几乎为零 | 添加单元测试和集成测试 |
| 多模态 | 基础图片/视频 | 扩展音视频、3D、文档理解 |
| 部署指南 | 零散 | 系统化部署（Docker/K8s/Serverless） |

---

## 二、总体架构设计

```
                   ┌──────────────────────────┐
                   │   awesome-llm-apps 门户    │
                   │  (README + 多语言导航)      │
                   └──────────┬───────────────┘
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                     ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
   │  核心模板层    │   │  框架速成课程   │   │   DevOps 基础设施  │
   │  (14 个分类)   │   │  (ADK/OpenAI) │   │  (测试/CI/部署)    │
   └──────────────┘   └──────────────┘   └──────────────────┘
          │
          ▼
   ┌─────────────────────────────────────────────┐
   │           差异化价值层（fork 独特）            │
   │  ├─ 国产模型深度集成                           │
   │  ├─ 中文生态（文档 + 案例 + 社区）              │
   │  └─ 生产级增强（错误处理/安全/可观测性）          │
   └─────────────────────────────────────────────┘
```

---

## 三、12 个月里程碑概览

| 季度 | 阶段 | 核心主题 | 关键交付 |
|------|------|---------|---------|
| **Q3 2026** (7-9月) | **追齐与本土化** | 同步上游 + 国产模型 + 中文文档 | 30+ 新模板，全量中文 README |
| **Q4 2026** (10-12月) | **扩展与深化** | 多模态 + 企业级加固 + 测试体系 | Agent 技能库翻倍，测试覆盖率 >60% |
| **Q1 2027** (1-3月) | **集成与智能化** | 深度 RAG + 代理框架 + 可观测性 | 10+ 深度教程，监控体系就绪 |
| **Q2 2027** (4-6月) | **成熟与规模化** | 部署体系 + 社区建设 + 基准测试 | 一键部署方案，500+ 模板 |

---

## 四、详细计划

### 🎯 Phase 1: 追齐与本土化（2026年7月 - 9月）

#### M1 — 同步上游（2026年7月）

**目标**: 消除与上游的 4 个提交差距，建立定期合并策略

| 周次 | 任务 | 交付物 |
|------|------|--------|
| W1 | 审查上游 4 个待合并提交 | 合并冲突分析报告 |
| W2 | 合并上游提交，验证 CI 通过 | 同步后的 main 分支 |
| W3 | 建立上游跟踪自动化 | GitHub Actions: weekly-sync 工作流 |
| W4 | 建立合并策略 ADR | ADR-001: 上游同步策略 |

**自动化**:
- 创建 `weekly-sync.yml`：每周自动检查上游变更
- 创建 `auto-merge.yml`：无冲突时自动合并

---

#### M2 — 国产模型深度集成（2026年7月 - 8月）

**目标**: 让 30+ 模板支持国产大模型无缝切换

| 任务 | 说明 | 模板覆盖数 |
|------|------|-----------|
| 添加 DeepSeek 适配器 | DeepSeek API / DeepSeek-R1 推理 | 10+ |
| 添加 Qwen 适配器 | 通义千问 API + QwQ-32B | 8+ |
| 添加 GLM 适配器 | 智谱 GLM-4 系列 | 6+ |
| 添加 百度文心 适配器 | ERNIE 系列 | 6+ |
| 添加 Moonshot 适配器 | Kimi API | 4+ |
| 创建模型切换指南 | `docs/model-switch-guide.md` | 通用 |

**实现策略**:
```
在每个模板中引入环境变量 MODEL_PROVIDER
├─ openai → 默认
├─ deepseek → DeepSeek Chat API
├─ qwen → 通义千问 DashScope API
└─ glm → 智谱开放平台 API
```

**关键模板清单**:
- `starter_ai_agents/`: ai_reasoning_agent, ai_travel_agent, openai_research_agent, xai_finance_agent
- `advanced_ai_agents/single_agent_apps/`: 所有单 Agent
- `rag_tutorials/`: 基础 RAG 链、Agentic RAG

---

#### M3 — 中文生态建设（2026年8月 - 9月）

**目标**: 全仓库中文 README + 本土化案例

| 任务 | 交付物 |
|------|--------|
| 根目录 README 中文本地化 | `README.zh-CN.md` |
| 14 个分类目录 README 中文化 | 14 个 `README.zh-CN.md` |
| 30 个重点模板 README 中文化 | 每模板配套中文教程 |
| 中文使用指南 | `docs/getting-started-zh.md` |
| 中国开发者 FAQ | `docs/faq-zh.md` |
| 添加中文搜索标签 | Topics: `ai-agent中文教程` |

**优先级顺序**:
1. 根目录 README + 入门指南
2. starter_ai_agents 全部中文化（最易上手）
3. rag_tutorials + mcp_ai_agents（技术热点）
4. advanced_ai_agents + generative_ui_agents（深度用户）
5. 剩余分类

---

### 🎯 Phase 2: 扩展与深化（2026年10月 - 12月）

#### M4 — Agent 技能库翻倍（2026年10月）

**目标**: 从 19 个技能扩展到 40+，覆盖更多垂直场景

**新增技能方向**:

| 类别 | 新技能 | 说明 |
|------|--------|------|
| 🖥️ 编程 | `security-auditor` | 安全审计与合规检查 |
| 🖥️ 编程 | `api-designer` | REST/GraphQL API 设计 |
| 🔍 研究 | `market-researcher` | 市场调研与竞品分析 |
| 🔍 研究 | `patent-researcher` | 专利检索与分析 |
| ✍️ 写作 | `resume-writer` | 简历优化与定制 |
| ✍️ 写作 | `translation-expert` | 专业翻译与本地化 |
| 📋 规划 | `roadmap-planner` | 产品路线图规划 |
| 📋 规划 | `risk-assessor` | 风险评估与缓解 |
| 📊 数据 | `ml-pipeline-designer` | 机器学习管道设计 |
| ⚡ 效率 | `prompt-optimizer` | 提示词优化与模板 |
| ⚡ 效率 | `api-tester` | 自动 API 测试生成 |
| 🏭 垂直 | `legal-analyzer` | 法律文件分析 |
| 🏭 垂直 | `medical-consultant` | 医疗咨询辅助 |
| 🏭 垂直 | `financial-advisor` | 财务规划建议 |
| 🏭 垂直 | `hr-recruiter` | 招聘与简历筛选 |
| 🏭 垂直 | `education-tutor` | 个性化教育辅导 |
| 🏭 垂直 | `real-estate-agent` | 房地产分析 |
| 🏭 垂直 | `social-media-manager` | 社交媒体管理 |
| 🌐 国产 | `douyin-marketing` | 抖音营销策略 |
| 🌐 国产 | `wechat-operator` | 微信公众号运营 |
| 🌐 国产 | `china-tax-advisor` | 中国税务咨询 |

**实现规范**:
```markdown
每个技能目录结构：
skill-name/
├── SKILL.md          # Agent 指令
├── scripts/          # 辅助脚本（可选）
├── references/       # 支持文档（可选）
├── examples/         # 使用示例（新增）
└── tests/            # 技能测试（新增）
```

---

#### M5 — 多模态 Agent 扩展（2026年10月 - 11月）

**目标**: 从现有的图片/视频基础扩展到全面的多模态谱系

| 模态 | 新增模板 | 数量 |
|------|---------|------|
| 🎤 音频 | 语音转录 Agent、语音情感分析、音乐生成增强 | 3 |
| 🎬 视频 | 视频摘要 Agent、视频问答、实时视频分析 | 3 |
| 📄 文档 | PDF 智能分析、扫描件 OCR + RAG | 2 |
| 🏗️ 3D | 3D 模型描述生成、SDF 理解 | 2 |
| 📊 图表 | 图表理解 Agent、信息图分析 | 2 |

**架构**:
```
multimodal_agents/
├── audio_agents/
├── video_agents/
├── document_agents/
├── chart_agents/
└── fusion_agents/     (多模态融合)
```

---

#### M6 — 测试体系构建（2026年11月 - 12月）

**目标**: 为所有模板建立基本测试覆盖

| 测试类型 | 覆盖范围 | 工具 |
|---------|---------|------|
| 单元测试 | 核心逻辑函数 | pytest |
| 集成测试 | API 调用链 | pytest + responses |
| 烟雾测试 | 模板能否启动 | pytest + subprocess |
| 文档测试 | README 代码块 | doctest |
| CI 集成 | PR 自动运行 | GitHub Actions |

**测试覆盖率目标**:
- Phase 2 结束: 60% 模板有基础测试
- Phase 3 结束: 90% 模板有基础测试

**关键测试文件结构**:
```
每个模板目录下新增：
├── tests/
│   ├── test_unit.py          # 单元测试
│   ├── test_integration.py   # 集成测试（mock API）
│   └── conftest.py           # 测试夹具
```

---

### 🎯 Phase 3: 集成与智能化（2027年1月 - 3月）

#### M7 — 深度 RAG 体系（2027年1月）

**目标**: 构建 5 种以上高级 RAG 模式

| RAG 模式 | 说明 | 新增/增强模板 |
|----------|------|-------------|
| Agentic RAG | Agent 自主决策检索时机 | 3 个新模板 |
| Graph RAG | 知识图谱增强检索 | 2 个新模板 |
| Multi-Modal RAG | 跨模态检索（文本+图片） | 2 个新模板 |
| Corrective RAG | 自纠正检索管道 | 1 个新模板 |
| Speculative RAG | 推测性预检索 | 1 个新模板 |
| Hybrid Search RAG | 稠密+稀疏向量混合 | 增强现有模板 |

**架构抽象**:
```
rag_tutorials/
├── basic_rag/              # 已有
├── advanced_rag/           # 新增
│   ├── agentic_rag/
│   ├── graph_rag/
│   ├── multi_modal_rag/
│   ├── corrective_rag/
│   └── speculative_rag/
├── hybrid_search_rag/      # 增强
└── evaluation/             # 新增
    └── rag_evaluation_bench/
```

---

#### M8 — Agent 框架速成课程深化（2027年1月 - 2月）

**目标**: 补充当前框架课程缺失的主题

**现有课程**:
- Google ADK 速成课程（10 章节）
- OpenAI SDK 速成课程（10 章节）

**新增课程**:

| 框架 | 章节数 | 主题 |
|------|--------|------|
| LangGraph | 8 | 状态图、条件边、持久化、流式 |
| Agno (原 Phidata) | 6 | 多 Agent 编排、工具集成、记忆 |
| CrewAI | 6 | 角色分配、任务委派、流程控制 |
| AutoGen | 6 | 多 Agent 对话、代码执行、函数调用 |
| Dify | 4 | 可视化编排、插件系统、RAG 管道 |

**课程结构模板**:
```
ai_agent_framework_crash_course/
├── langgraph_crash_course/
├── agno_crash_course/
├── crewai_crash_course/
├── autogen_crash_course/
└── dify_crash_course/
```

---

#### M9 — 可观测性与可靠性（2027年2月 - 3月）

**目标**: 为生产级模板添加可观测性能力

| 能力 | 工具/技术 | 覆盖模板数 |
|------|----------|-----------|
| 日志记录 | loguru / structlog | 50+ |
| 追踪 | OpenTelemetry | 20+ |
| 指标 | Prometheus 客户端 | 10+ |
| 错误边界 | 重试 + 熔断 + 降级 | 30+ |
| 速率限制 | 令牌桶 + 滑动窗口 | 20+ |

**生产级模板标记**:
```
在每个模板 README 中添加:
🏭 生产级别: Bronze | Silver | Gold

Gold 标准:
- ✅ 完整的错误处理
- ✅ 结构化日志
- ✅ 可配置的重试策略
- ✅ API 密钥安全存储
- ✅ 输入验证与清理
- ✅ 有单元测试
- ✅ 有部署指南
```

---

### 🎯 Phase 4: 成熟与规模化（2027年4月 - 6月）

#### M10 — 一键部署体系（2027年4月）

**目标**: 让每个模板都能一行命令部署

**部署目标**:

| 平台 | 支持模板数 | 方式 |
|------|-----------|------|
| Docker Compose | 全部 | 标准 Dockerfile |
| Streamlit Cloud | 50+ | GitHub 一键部署按钮 |
| Hugging Face Spaces | 30+ | Space 配置 |
| Railway / Render | 30+ | 部署模板 |
| Kubernetes (生产) | 10+ | Helm Chart |
| Serverless (AWS Lambda) | 10+ | SAM 模板 |

**部署结构**:
```
每个模板目录下新增：
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .streamlit/config.toml
│   └── README-deploy.md
```

---

#### M11 — 基准测试与评估（2027年4月 - 5月）

**目标**: 建立 Agent/RAG 基准测试对比

| 基准测试 | 方法 | 输出 |
|---------|------|------|
| RAG 检索质量 | MRR / Recall@K / NDCG | 排行榜 |
| Agent 任务完成率 | 人工评估 + 自动检查 | 成功率报告 |
| 成本基准 | 每任务的 Token 消耗 | 性价比报告 |
| 延迟基准 | P50 / P95 / P99 延迟 | 响应时间报告 |
| 模型对比 | 同一模板在不同模型上的表现 | 模型对比图 |

**输出**: `docs/benchmarks/` 目录下的定期报告

---

#### M12 — 社区建设与长期维护（2027年5月 - 6月）

**目标**: 建立可持续的社区贡献机制

| 任务 | 交付物 |
|------|--------|
| 贡献指南 | `CONTRIBUTING.md` |
| 模板提交模板 | `.github/ISSUE_TEMPLATE/new-template.md` |
| 代码审查清单 | `docs/review-checklist.md` |
| 社区提案流程 | `docs/proposal-process.md` |
| 每周精选 | GitHub Discussions 每周精选模板 |
| 模板质量分级 | Bronze / Silver / Gold 标签体系 |

**维护策略**:
```
每季度:
├─ 审查上游合并请求
├─ 更新依赖版本
├─ 运行全仓库 CI
├─ 修复报告的问题
└─ 发布 Release Notes
```

---

## 五、关键指标追踪

### 增长目标

| 指标 | 当前值 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|-------|---------|---------|---------|---------|
| 模板总数 | ~100 | 130+ | 200+ | 300+ | 500+ |
| 中文 README | 1 | 30+ | 80+ | 150+ | 全部 |
| 国产模型支持模板 | 0 | 30+ | 60+ | 100+ | 150+ |
| Agent 技能数 | 19 | 19 | 40+ | 40+ | 50+ |
| 测试覆盖模板 | ~0 | 10+ | 60% | 90% | 95%+ |
| 框架课程章节 | 20 | 20 | 20 | 50+ | 60+ |
| 一键部署模板 | 0 | 10+ | 30+ | 80+ | 全部 |
| 可观测性覆盖 | 0 | 0 | 20+ | 50+ | 80+ |

### 质量指标

- **文档完整性**: README 中文覆盖率 >95%
- **代码可运行性**: 新模板 100% 通过 CI 烟雾测试
- **破损链接**: 持续保持 0
- **PR 合并时间**: < 7 天（社区贡献）
- **依赖更新频率**: 每季度一次全量 audit

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 上游仓库被删除/归档 | 低 | 高 | 本 fork 已完全独立，持续维护 |
| 国产模型 API 兼容性变化 | 中 | 中 | 抽象适配层，集成 API 版本检测 |
| 模板依赖包过时 | 高 | 中 | 每季度 Dependabot 批量更新 |
| 社区贡献质量参差 | 中 | 低 | 严格审查流程 + 模板质量分级 |
| AI 框架快速迭代 | 高 | 中 | 框架课程每年更新一次内容 |

---

## 七、发布节奏

```
每两周一个小版本（x.y.z）
每月一个中版本（x.y）
每季度一个大版本（x）

版本号规则:
- Patch: Bug 修复、文档更新
- Minor: 新增模板、技能、框架
- Major: 架构变更、重大功能上线
```

---

## 八、附录

### A. 与 MiMo-Code 的协同机会

本 fork 与你的 **MiMo-Code** 项目有以下协同点：

| 协同方向 | 说明 |
|---------|------|
| Provider 复用 | MiMo-Code 的国产模型适配层可直接复用 |
| Memory 系统 | 将 MiMo-Code 的记忆集成带到 Agent 模板中 |
| CI/CD 经验 | 借鉴 MiMo-Code 的跨平台 CI 配置 |
| Skill 生态 | 两个仓库的 skills 可以交叉引用 |

### B. 技术栈偏好

- **语言**: Python 3.11+
- **Web 框架**: Streamlit (首选), FastAPI (后端 API)
- **Agent 框架**: Agno, OpenAI SDK, LangChain/LangGraph, Google ADK
- **数据**: ChromaDB, Qdrant, SQLite
- **部署**: Docker, Streamlit Cloud, Hugging Face Spaces

### C. ADR 索引（规划中）

| 编号 | 标题 | 预计时间 |
|------|------|---------|
| ADR-001 | 上游同步策略 | 2026-07 |
| ADR-002 | 国产模型适配层设计 | 2026-07 |
| ADR-003 | 测试体系选择 | 2026-11 |
| ADR-004 | RAG 架构抽象 | 2027-01 |
| ADR-005 | 部署标准化方案 | 2027-04 |

---

> **最后更新**: 2026年7月7日
> **维护者**: ghshhf
> **许可证**: Apache-2.0
