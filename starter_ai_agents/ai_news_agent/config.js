// config.js

import path from 'path';
import { fileURLToPath } from 'url';

// --- ES Module 环境下的 __dirname ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * @description 应用程序的核心配置对象
 */
const CONFIG = {
    // 任务定义
    taskDescription: '为中国大陆的读者提供一份关于国家重要新闻的每日简报。',
    startUrl: 'https://www.sina.com.cn/',

    // 调试与输出
    debugMode: false, // 设置为 true 可在控制台看到详细的 LLM 请求日志
    outputBaseDir: path.join(__dirname, 'output'),

    // 网络相关
    network: {
        headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        },
        fetchTimeout: 20000, // 页面抓取超时时间 (ms)
    },

    // 爬取与链接筛选
    crawling: {
        maxDepth: 2, // 爬取最大深度
        maxCategoryPages: 10, // 在每个深度探索的“栏目页”数量上限
        uselessTitleKeywords: ['关于我们', '联系我们', '隐私政策', '登录', '注册', '下载', '更多', '广告', '订阅'],
    },

    // 锦标赛排名配置
    ranking: {
        // --- 资格赛配置 (已更新) ---
        qualificationRounds: 2,         // (新) 资格赛进行轮次，实现更公平的筛选
        qualificationGroupSize: 10,     // 资格赛中，每组比较多少个链接标题
        qualificationTopN: 3,           // (行为变更) 多轮后，仅用于最终选择，不再是每组淘汰
        qualificationPoints: [5, 3, 2, 1, 0], // (新) 资格赛小组得分
        qualificationConcurrency: 10,   // 资格赛并发请求数

        // --- 决赛圈配置 ---
        contendersToRank: 60,       // 最多选出多少位“选手”进入决赛圈
        tournamentRounds: 3,        // 进行多少轮决赛
        tournamentGroupSize: 3,     // 决赛每轮比较中，每组包含多少篇文章
        tournamentPoints: [3, 1, 0], // 决赛小组前三名得分
        tournamentConcurrency: 8,   // 决赛并发请求数
    },

    // 文章处理
    processing: {
        maxArticlesToProcess: 15, // 最终处理的文章数量上限
        minContentLength: 150, // 认为文章有效的最小内容长度（字符）
        maxOverallRetries: 5, // 针对失败队列的整体最大重试轮次，防止无限循环
    },

    // 大语言模型 (LLM)
    llm: {
        studioUrl: 'http://localhost:1234/v1/chat/completions',
        maxRetries: 1, // 单次处理失败后不再立即重试，交由失败队列统一管理
        retryDelay: 3000, // 每次重试的延迟时间 (ms)
        requestTimeout: 120000, // 普通LLM请求超时时间 (ms)
        longRequestTimeout: 300000, // 长任务LLM请求超时时间 (ms)
        maxTokens: 999999, // LLM返回的最大token数
    },

    // 输出格式化
    output: {
        categoryEmojis: { '国际': '🌍', '国内': '🇨🇳', '财经': '💼', '科技': '🔬', '社会': '👥', '观点': '✍️', '其他': '📰', '默认': '📰' }
    },

    // Prompt 模板中心
    prompts: {
        qualifyLinks: (linkTitles, taskDescription) => ({
            system: '你是一位反应迅速、判断精准的新闻编辑，任务是快速判断在一组新闻标题中，哪些对目标读者最重要。你的回应必须极端简洁，严格遵循格式。内容使用简体中文。',
            user: `**任务目标**: “${taskDescription}”\n\n**待评估的标题列表**:\n${linkTitles.map((title, i) => `${i + 1}. ${title}`).join('\n')}\n\n**你的指令**:\n根据任务目标，对列表中的标题进行重要性排序。你的回应【只能】是标题的【编号】，从最重要到最不重要排列，并用英文逗号 (,) 分隔。不要包含任何理由、解释或多余的文字。\n\n**格式示例**: 3,1,2,5,4\n\n**你的回应**:`,
        }),

        classifyLinkType: (linkTitle) => ({
            system: '你是一个链接分类工具，任务是判断一个链接标题指向的是“文章页面”还是“栏目列表页面”。你的回应必须是单个词。内容使用简体中文。',
            user: `请判断以下链接标题更可能是一个具体的新闻“文章”（article）还是一个新闻“栏目”（category）。\n标题：“${linkTitle}”\n\n你的回应只能是 "article" 或 "category"。\n\n回应:`,
        }),

        // <-- 新增的 Prompt -->
        extractKeywordsFromTitle: (title) => ({
            system: '你是一个关键词提取API。你的任务是从给定的新闻标题中提取出最核心的1-3个关键词。你的回应必须极端简洁，严格遵循格式，不能有任何解释。',
            user: `**新闻标题**: "${title}"\n\n**你的指令**:\n提取1-3个核心关键词。你的回应【只能】是关键词本身，用英文逗号 (,) 分隔。如果标题信息不足以提取，请返回空。\n\n**格式示例**: 俄乌冲突,基辅,空袭\n\n**你的回应**:`,
        }),
        // <-- 新增结束 -->

        rankContenders: (articles, taskDescription) => ({
            system: '你是一位顶级的、拥有宏观视野的总编辑，任务是判断在一组新闻中，哪些对于目标读者最重要、最具有新闻价值。你的判断必须果断、精准，且严格遵循输出格式。内容使用简体中文。',
            user: `**任务目标**: “${taskDescription}”\n\n**待排名新闻列表**:\n${articles.map((a, i) => `${i + 1}. ${a.title}`).join('\n')}\n\n**你的指令**:\n请根据上述任务目标，对列表中的新闻进行重要性排序。你的回应【只能】是新闻的【编号】，从最重要到最不重要排列，并用英文逗号 (,) 分隔。不要包含任何理由、解释或多余的文字。\n\n**格式示例**: 3,1,2\n\n**你的回应**:`,
        }),
        
         processArticleSingleCall: (articleContent, originalTitle) => ({
            system: '你是一个高度专业化的信息提取和处理API。你的唯一功能是接收文本，并根据用户指定的结构，返回一个【纯粹的、格式完美的JSON对象】。你的输出严禁包含任何JSON之外的文本、解释或Markdown标记（如```json）。内容使用简体中文。',
            user: `
**新闻原文全文**:
---
${articleContent}
---

**你的任务**:
根据以上原文，执行下列所有指令，并生成一个【单一、完整、无任何多余内容】的JSON对象回复。

**# JSON对象结构定义**
你必须生成一个包含以下key的JSON对象：
1.  \`"title"\`: (string) 生成一个全新的、精炼、中立、信息量大的中文标题。
2.  \`"conciseSummary"\`: (string) 用一句话（不超过60字）高度凝练其核心内容。
3.  \`"keywords"\`: (string[]) 提取3-5个最重要的核心关键词，并存为一个JSON字符串数组。
4.  \`"category"\`: (string) 从 ['国际', '国内', '财经', '科技', '社会', '观点', '其他'] 中选择一个最匹配的分类。
5.  \`"detailedSummary"\`: (string) 撰写一篇详尽、流畅、结构清晰的深度摘要（约200-300字），可使用Markdown换行符 \`\\n\` 和列表来增强可读性。

**# 绝对规则 (!!!必须严格遵守!!!)**
1.  **【规则1：纯净JSON】** 你的整个回复【必须且只能】是一个完整的JSON对象，从 \`{\` 开始，到 \`}\` 结束。
2.  **【规则2：无外部文本】** 严禁在JSON对象前后添加任何文本、注释、或Markdown代码块标记。

---
**# 格式示例 (请严格模仿此JSON结构)**

\`\`\`json
{
  "title": "俄乌冲突升级：基辅遭遇大规模空袭，平民伤亡引发国际谴责",
  "conciseSummary": "俄罗斯对乌克兰首都基辅发动新一轮大规模空袭，导致多栋民用建筑受损和大量平民伤亡，引发国际社会强烈谴责和对人道危机的担忧。",
  "keywords": ["俄乌冲突", "基辅", "空袭", "人道危机", "国际谴责"],
  "category": "国际",
  "detailedSummary": "俄罗斯军队于周四凌晨对乌克兰首都基辅发动了数月来最大规模的空袭之一。乌克兰军方表示，防空系统拦截了大部分来袭的导弹和无人机，但仍有部分袭击造成了严重后果。\\n\\n**主要影响包括：**\\n* **人员伤亡**: 市长报告称，至少有10名平民在袭击中丧生，超过50人受伤。救援工作仍在进行中。\\n* **基础设施破坏**: 一栋居民楼被直接击中，引发大火。一个关键的能源设施也遭到破坏。\\n\\n国际社会迅速对此事做出反应。美国总统谴责此次袭击是“野蛮行径”，联合国秘书长也呼吁立即停止针对平民的袭击。"
}
\`\`\`
---

**请严格遵照以上所有规则，开始生成你的JSON对象：**
`
        }),

        generateEditorIntro: (conciseSummariesText) => ({
            system: '你是一位视野宏大、洞察力敏锐的资深总编辑。内容使用简体中文。',
            user: `根据以下今日核心新闻的一句话摘要，撰写一段200-300字的“总编导语”。\n\n**写作要求:**\n1.  **宏观视角**: 从全局角度，高度概括当日最重要的新闻动态和趋势。\n2.  **深度洞察**: 指出不同新闻事件之间潜在的联系，或它们共同揭示的宏观意义。\n3.  **专业文笔**: 风格沉稳、精炼、富有洞见，符合国家级新闻机构的定位。\n4.  **纯净输出**: 你的回应【只能】包含导语本身，禁止任何额外文字。\n\n---[今日核心新闻摘要]---\n${conciseSummariesText}\n---`
        }),
    }
};

export default CONFIG;