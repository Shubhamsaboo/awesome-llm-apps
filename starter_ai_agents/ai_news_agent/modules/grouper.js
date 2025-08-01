// modules/grouper.js

import pLimit from 'p-limit';
import _ from 'lodash';
import chalk from 'chalk';
import CONFIG from '../config.js';
import logger from '../utils/logger.js';
import { callLLM } from '../services/network.js';

/**
 * 从单个标题中提取关键词。
 * @param {string} title - 文章标题。
 * @returns {Promise<string[]>} - 小写关键词数组。
 */
async function getKeywordsForTitle(title) {
    const { system, user } = CONFIG.prompts.extractKeywordsFromTitle(title);
    const response = await callLLM([{ role: 'system', content: system }, { role: 'user', content: user }], 0.1);
    
    // LLM响应应该是一个用逗号分隔的关键词列表
    // 进行清洗，去除空字符串，并转换为小写
    return response.split(',')
        .map(k => k.trim().toLowerCase())
        .filter(Boolean);
}

/**
 * 对文章进行聚类和去重。
 * @param {Array<object>} articles - 候选文章列表。
 * @param {import('cli-progress').SingleBar} progressBar - 进度条实例。
 * @returns {Promise<Array<object>>} - 去重后的文章列表。
 */
export async function groupAndDeduplicateArticles(articles, progressBar) {
    if (articles.length === 0) {
        return [];
    }
    
    progressBar.start(articles.length, 0, { status: "提取标题关键词..." });

    // 步骤 1: 并发地为所有文章提取关键词
    const limit = pLimit(CONFIG.ranking.qualificationConcurrency); // 复用资格赛的并发设置
    const articlesWithKeywords = [];

    const keywordPromises = articles.map(article => limit(async () => {
        try {
            const keywords = await getKeywordsForTitle(article.title);
            articlesWithKeywords.push({ ...article, keywords });
        } catch (error) {
            logger.warn(`未能从标题提取关键词: "${article.title}"`, { error: error.message });
            // 即使失败，也加入列表，确保文章不丢失
            articlesWithKeywords.push({ ...article, keywords: [] });
        } finally {
            progressBar.increment();
        }
    }));
    await Promise.all(keywordPromises);
    progressBar.stop();

    // 步骤 2: 基于共享的关键词对文章进行分组
    console.log(chalk.cyan('\n正在进行相似文章聚类...'));
    const groups = [];
    let remainingArticles = [...articlesWithKeywords];

    while (remainingArticles.length > 0) {
        // 从剩余文章中取出第一篇作为“种子”
        const seedArticle = remainingArticles.shift();
        
        // 如果种子文章没有关键词，它自己成为一个独立的组
        if (!seedArticle.keywords || seedArticle.keywords.length === 0) {
            groups.push([seedArticle]);
            continue;
        }

        const currentGroup = [seedArticle];
        const seedKeywords = new Set(seedArticle.keywords);

        // 从后向前遍历剩余文章，以安全地在循环中删除元素
        for (let i = remainingArticles.length - 1; i >= 0; i--) {
            const targetArticle = remainingArticles[i];
            
            // 检查目标文章的关键词是否与种子文章的关键词有交集
            const hasSharedKeyword = targetArticle.keywords.some(kw => seedKeywords.has(kw));

            if (hasSharedKeyword) {
                currentGroup.push(targetArticle);
                // 将已分组的文章从剩余列表中移除
                remainingArticles.splice(i, 1);
            }
        }
        groups.push(currentGroup);
    }
    
    logger.info(`已将 ${articles.length} 篇文章聚类成 ${groups.length} 个独立议题。`);
    console.log(chalk.green(`聚类分析完成，共形成 ${groups.length} 个独立新闻议题。`));

    // 步骤 3: 从每个组中选出得分最高的代表
    const uniqueContenders = groups.map(group => {
        // 如果组内只有一篇文章，直接返回它
        if (group.length === 1) {
            // 使用 alodash.omit 移除临时的 keywords 属性
            return _.omit(group[0], 'keywords');
        }
        
        // 如果组内有多篇相似文章，选出在资格赛中得分最高的作为代表
        const representative = _.orderBy(group, ['score'], ['desc'])[0];
        
        const groupTitles = group.map(a => `  - "${a.title}" (得分: ${a.score})`).join('\n');
        logger.debug(`合并了 ${group.length} 篇相似文章，选出代表: "${representative.title}"。\n该组包含:\n${groupTitles}`);
        
        return _.omit(representative, 'keywords');
    });

    // 按资格赛分数对最终选出的代表们进行一次排序
    return _.orderBy(uniqueContenders, ['score'], ['desc']);
}