// modules/reporter.js

import fs from 'fs/promises';
import path from 'path';
import chalk from 'chalk';
import CONFIG from '../config.js';
import logger from '../utils/logger.js';
import { getCategoryEmoji } from '../utils/helpers.js';
import { callLLM } from '../services/network.js';

/**
 * 根据处理好的文章数据，生成最终的Markdown简报
 * @param {Array<object>} articles - 已处理并包含所有元数据的文章列表
 * @param {string} dailyOutputDir - 当日输出目录
 * @param {import('ora').Ora} spinner - Ora微调器实例
 * @returns {Promise<object|null>} - 包含报告路径的对象，或在无文章时返回null
 */
export async function generateFinalReport(articles, dailyOutputDir, spinner) {
    if (articles.length === 0) {
        logger.warn('未成功处理任何文章，无法生成简报。');
        console.log('\n' + chalk.red.bold('❌ 未成功处理任何文章，无法生成简报。'));
        return null;
    }

    spinner.start('AI正在撰写总编导语...');
    const today = new Date().toISOString().slice(0, 10);
    const conciseSummariesText = articles
        // 使用LLM生成的新标题
        .map((a, i) => `${i + 1}. 【${a.category}】${a.title}: ${a.conciseSummary}`)
        .join('\n');
    
    const { system, user } = CONFIG.prompts.generateEditorIntro(conciseSummariesText);
    let editorIntroduction = "今日要闻看点：";
    try {
        editorIntroduction = await callLLM(
            [{ role: 'system', content: system }, { role: 'user', content: user }], 
            0.6, 
            CONFIG.llm.longRequestTimeout
        );
    } catch (error) {
        spinner.warn(chalk.yellow("总编导语生成失败，将使用默认导语。"));
        logger.error("总编导语生成失败", { error });
    }
    spinner.succeed(chalk.green.bold('总编导语已生成!'));

    let finalMarkdown = `# 每日新闻简报 (${today})\n\n`;
    finalMarkdown += `> **总编导语**\n> ${editorIntroduction.replace(/\n/g, '\n> ')}\n\n---\n\n`;

    // 生成目录
    finalMarkdown += `### **目录 (Table of Contents)**\n`;
    articles.forEach((article, index) => {
        // 使用LLM生成的新标题
        finalMarkdown += `${index + 1}. [${getCategoryEmoji(article.category)}【${article.category}】${article.title}](#${index + 1})\n`;
    });
    finalMarkdown += `\n---\n\n`;

    // 生成正文
    for (const [index, article] of articles.entries()) {
        // 使用LLM生成的新标题
        finalMarkdown += `### <a id="${index + 1}"></a> ${index + 1}. ${getCategoryEmoji(article.category)}【${article.category}】${article.title}\n\n`;
        finalMarkdown += `* **一句话摘要**: ${article.conciseSummary}\n`;
        finalMarkdown += `* **重要性排名**: ${article.rank} (锦标赛得分: ${article.tournamentScore})\n`;
        if (article.keywords && article.keywords.length > 0) {
            finalMarkdown += `* **核心词**: ${article.keywords.join('、')}\n\n`;
        } else {
            finalMarkdown += `\n`;
        }
        finalMarkdown += `#### **详细内容**\n${article.detailedSummary}\n\n`;
        finalMarkdown += `[阅读原文](${article.url})\n\n---\n\n`;
    }

    const reportFileName = `News-Briefing-${today}.md`;
    const reportFilePath = path.join(dailyOutputDir, reportFileName);
    await fs.writeFile(reportFilePath, finalMarkdown);
    logger.info(`最终报告已生成: ${reportFilePath}`);

    return {
        reportFilePath,
        individualArticlesDir: path.join(dailyOutputDir, 'articles_markdown')
    };
}