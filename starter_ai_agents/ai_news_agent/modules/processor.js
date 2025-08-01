import path from 'path';
import fs from 'fs/promises';
import chalk from 'chalk';
import CONFIG from '../config.js';
import logger from '../utils/logger.js';
import { createSafeArticleFilename } from '../utils/helpers.js';
import { extractArticleContent, callLLM } from '../services/network.js';

/**
 * ===================================================================
 * vvvvvvvvvvvvvvvv     核心修改区域开始     vvvvvvvvvvvvvvvvvv
 * ===================================================================
 * (新) 从LLM的原始响应中稳健地解析出JSON结构化数据。
 * 替换了旧的基于分隔符的解析方法，健壮性极高。
 * @param {string} llmResponse - LLM返回的完整文本。
 * @returns {object} - 解析并验证后的数据对象。
 * @throws 如果响应中不包含有效的JSON，或JSON缺少关键字段，则抛出错误。
 */
function robustParseLLMResponse(llmResponse) {
    let jsonString = llmResponse;

    // 步骤1: 稳健地提取JSON块。LLM有时会在JSON前后添加额外文本。
    const jsonMatch = llmResponse.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
        throw new Error(`LLM响应中未找到有效的JSON对象结构。收到的内容: "${llmResponse}"`);
    }
    jsonString = jsonMatch[0];

    // 步骤2: 解析JSON字符串，并捕获语法错误。
    let data;
    try {
        data = JSON.parse(jsonString);
    } catch (error) {
        logger.error(`JSON解析失败。原始文本: "${jsonString}"`);
        throw new Error(`LLM返回的不是一个有效的JSON格式: ${error.message}`);
    }

    // 步骤3: 验证解析出的对象结构和内容。
    const { title, conciseSummary, keywords, category, detailedSummary } = data;

    if (!title || typeof title !== 'string' || title.trim() === '') {
        throw new Error("JSON数据中缺少有效的'title'字段。");
    }
    if (!detailedSummary || typeof detailedSummary !== 'string' || detailedSummary.trim() === '') {
        throw new Error("JSON数据中缺少有效的'detailedSummary'字段。");
    }
    if (!keywords || !Array.isArray(keywords)) {
        throw new Error("JSON数据中'keywords'字段必须是一个数组。");
    }

    // 步骤4: 数据清洗和设置默认值。
    const newTitle = title.trim();
    let finalConciseSummary = (conciseSummary || '').trim();
    const finalKeywords = keywords.map(k => String(k).trim()).filter(Boolean);
    const finalCategory = category || '其他';

    // 步骤5: 执行优雅降级（Fallback）逻辑，与旧版保持一致。
    if (!finalConciseSummary && detailedSummary.trim().length > 0) {
        logger.warn(`未能从JSON中获取'conciseSummary'，将使用详细摘要的第一句话作为替代。`);
        const firstSentence = detailedSummary.trim().split(/[。！？]/)[0];
        if (firstSentence) {
            finalConciseSummary = `${firstSentence.trim()}。`;
        }
    }

    // 返回最终的、干净的结构化数据
    return {
        title: newTitle,
        conciseSummary: finalConciseSummary,
        keywords: finalKeywords,
        category: finalCategory,
        detailedSummary: detailedSummary.trim(),
    };
}


/**
 * (已更新) 处理单篇文章，一次性调用LLM并使用新的JSON解析器。
 * @param {object} articleMeta - 文章元数据 { title, content, url }
 * @param {function} progressCallback - 用于报告进度的回调
 * @returns {Promise<object>} - 包含所有处理后数据的对象
 * @throws 如果LLM调用或JSON解析、验证失败，则抛出错误。
 */
async function processSingleArticle(articleMeta, progressCallback = () => {}) {
    const { title: originalTitle, content, url } = articleMeta;
    logger.debug(`开始处理文章: 《${originalTitle}》`);

    // --- 单次LLM调用 (Prompt已在config.js中更新为要求JSON) ---
    progressCallback(`深度处理中`);
    const { system, user } = CONFIG.prompts.processArticleSingleCall(content, originalTitle);
    const llmResponse = await callLLM(
        [{ role: 'system', content: system }, { role: 'user', content: user }],
        0.5,
        CONFIG.llm.longRequestTimeout
    );

    // --- 使用全新的、基于JSON的健壮解析逻辑 ---
    let processedData;
    try {
        processedData = robustParseLLMResponse(llmResponse);
    } catch (parseError) {
        logger.error(`解析LLM的JSON响应失败: ${parseError.message}`, { articleTitle: originalTitle });
        // 为了调试，可以把完整的llmResponse也打出来，但它可能很长
        logger.debug(`导致解析失败的LLM原文: \n---\n${llmResponse}\n---`);
        throw new Error(`解析LLM响应失败: ${parseError.message}`);
    }
    
    processedData.originalTitle = originalTitle; // 保留原始标题

    // 校验分类是否在预设范围内
    if (!Object.keys(CONFIG.output.categoryEmojis).includes(processedData.category)) {
        logger.warn(`文章《${originalTitle}》的新分类 "${processedData.category}" 不在预设中, 将使用默认分类“其他”。`);
        processedData.category = '其他';
    }

    // 再次校验关键字段，确保 fallback 逻辑后内容依然有效 (这步在新的解析器中已完成，此处为双重保险)
    if (!processedData.title || !processedData.detailedSummary) {
        throw new Error('经过解析和验证后，响应中仍缺少必要的标题或详细摘要。');
    }
    
    // 如果一句话摘要在 fallback 后仍然为空，给出警告但程序不中断
    if (!processedData.conciseSummary) {
        logger.warn(`文章《${originalTitle}》最终未能生成有效的一句话摘要。`);
    }

    logger.info(`文章《${originalTitle}》处理成功，新标题为《${processedData.title}》！`);
    return processedData;
}


/**
 * (已适配新流程和失败队列) 串行处理入选的文章，并保存独立报告。
 * 包含一个无限重试循环，直到所有文章被处理或达到最大重试轮次。
 */
export async function processAndSummarizeArticles(articles, dailyOutputDir, progressBar) {
    if (articles.length === 0) {
        logger.info('没有需要处理的文章。');
        return [];
    }

    const individualArticlesDir = path.join(dailyOutputDir, 'articles_markdown');
    await fs.mkdir(individualArticlesDir, { recursive: true });
    logger.info(`单篇文章的 Markdown 报告将保存在: ${individualArticlesDir}`);

    let processingQueue = [...articles];
    const successfulArticles = [];
    const failedArticles = new Map(); // 使用Map存储最终失败的文章和原因
    let overallRetryCount = 0;

    while (processingQueue.length > 0 && overallRetryCount < CONFIG.processing.maxOverallRetries) {
        if (overallRetryCount > 0) {
            console.log(chalk.yellow.bold(`\n--- 开始第 ${overallRetryCount} 轮失败重试 (${processingQueue.length}篇) ---`));
            const delay = CONFIG.llm.retryDelay * Math.pow(2, overallRetryCount - 1); // 指数退避
            console.log(chalk.gray(`(等待 ${delay / 1000} 秒后重试...)`));
            await new Promise(res => setTimeout(res, delay));
        }

        const currentBatch = [...processingQueue];
        processingQueue = []; // 清空当前队列，准备接收本轮失败的文章

        for (const [index, meta] of currentBatch.entries()) {
            const shortTitle = (meta.title || '未知标题').slice(0, 35);
            progressBar.setTotal(currentBatch.length); // 动态更新进度条总数
            progressBar.update(index, { status: `[提取原文] ${shortTitle}...` });
            
            try {
                const { content } = await extractArticleContent(meta.url);
                
                if (content.length < CONFIG.processing.minContentLength) {
                    throw new Error(`正文过短 (${content.length}字符), 已跳过。`);
                }

                const articleData = { title: meta.title, content, url: meta.url };

                const processedData = await processSingleArticle(articleData, (taskName) => {
                    progressBar.update(index, { status: `[${taskName}] ${shortTitle}...` });
                });

                // 使用LLM生成的新标题来创建文件名
                const safeFilename = createSafeArticleFilename(successfulArticles.length, processedData.title);
                const articleFilePath = path.join(individualArticlesDir, safeFilename);
                
                const finalResult = { ...meta, ...processedData };

                const articleMarkdown = `
# ${finalResult.title}
- **一句话摘要**: ${finalResult.conciseSummary || 'N/A'}
- **核心词**: ${finalResult.keywords.join('、') || 'N/A'}
- **重要性排名**: ${finalResult.rank} (得分: ${finalResult.tournamentScore})
- **原文链接**: ${finalResult.url}

---

### 详细内容
${finalResult.detailedSummary}

---

*报告生成时间: ${new Date().toLocaleString('zh-CN')}*
*原始标题: ${finalResult.originalTitle}*
`.trim();

                await fs.writeFile(articleFilePath, articleMarkdown);
                logger.info(`[处理成功] ${safeFilename}`);

                successfulArticles.push(finalResult);
                progressBar.update(index + 1, { status: `[处理完成] ${chalk.green(finalResult.title.slice(0, 30))}...` });

            } catch (error) {
                const errorMessage = error.message || '未知错误';
                logger.error(`文章处理失败: ${meta.url}`, { error: errorMessage });
                failedArticles.set(meta.url, { ...meta, message: errorMessage }); // 记录失败信息
                processingQueue.push(meta); // 加入到下一轮重试队列
                progressBar.update(index + 1, { status: `[处理失败] ${chalk.red(shortTitle)}... 将重试` });
            }
        }
        overallRetryCount++;
    }

    progressBar.stop();
    
    // 报告最终无法处理的文章
    if (processingQueue.length > 0) {
        console.log(chalk.red.bold(`\n❌ 经过 ${CONFIG.processing.maxOverallRetries} 轮尝试后，仍有 ${processingQueue.length} 篇文章处理失败:`));
        processingQueue.forEach(fail => {
            const failReason = failedArticles.get(fail.url)?.message || '未知错误';
            console.log(chalk.red(`     - ${fail.title}: ${failReason}`));
        });
    }

    return successfulArticles;
}