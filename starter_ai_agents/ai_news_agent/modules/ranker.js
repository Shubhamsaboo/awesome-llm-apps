// modules/ranker.js

import pLimit from 'p-limit';
import _ from 'lodash';
import CONFIG from '../config.js';
import logger from '../utils/logger.js';
import { callLLM } from '../services/network.js';

/**
 * (已重构) 对候选文章进行多轮瑞士制锦标赛排名。
 * 每一轮都根据当前总分进行排序，然后将分数相近的文章分在一组进行比较。
 * @param {Array<object>} articles - 待排名的文章元数据列表
 * @param {import('cli-progress').SingleBar} progressBar - 进度条实例
 * @returns {Promise<Array<object>>} - 经过排名和评分并排序后的文章列表
 */
export async function runFinalTournament(articles, progressBar) {
    const { tournamentRounds, tournamentGroupSize, tournamentPoints, tournamentConcurrency } = CONFIG.ranking;
    
    // 初始化所有文章的分数
    const articlesWithScores = articles.map(a => ({ ...a, tournamentScore: 0 }));

    const totalComparisons = tournamentRounds * Math.ceil(articles.length / tournamentGroupSize);
    progressBar.start(totalComparisons, 0, { status: "决赛圈 - 初始化..." });

    for (let round = 1; round <= tournamentRounds; round++) {
        // 核心改动：根据当前分数对文章进行排序，而不是随机洗牌
        const sortedArticles = _.orderBy(articlesWithScores, ['tournamentScore'], ['desc']);
        
        // 将排序后的文章分组成小组，这样分数相近的文章会被分到一起
        const groups = _.chunk(sortedArticles, tournamentGroupSize);
        const limit = pLimit(tournamentConcurrency);

        const rankingPromises = groups.map(group => limit(async () => {
            try {
                if (group.length < 2) {
                    // 如果小组只有一篇文章，它会自动晋级，无需比较，但也要更新进度
                    progressBar.increment(1, { status: `决赛圈 - 第 ${round}/${tournamentRounds} 轮` });
                    return; 
                }

                const { system, user } = CONFIG.prompts.rankContenders(group, CONFIG.taskDescription);
                const messages = [{ role: 'system', content: system }, { role: 'user', content: user }];
                const responseText = await callLLM(messages, 0.3);

                const rankedIndices = responseText.split(',').map(n => parseInt(n.trim(), 10) - 1);
                if (rankedIndices.length !== group.length || rankedIndices.some(isNaN)) {
                    throw new Error(`无效的排名回应: "${responseText}"`);
                }

                // 根据LLM的排名给文章加分
                rankedIndices.forEach((originalIndex, rank) => {
                    const articleInGroup = group[originalIndex];
                    if (articleInGroup && tournamentPoints[rank] !== undefined) {
                        // 找到在原始列表中的对应文章并更新其分数
                        const targetArticle = articlesWithScores.find(a => a.url === articleInGroup.url);
                        if(targetArticle) {
                            targetArticle.tournamentScore += tournamentPoints[rank];
                        }
                    }
                });
            } catch (error) {
                logger.warn(`决赛小组排名失败`, { group: group.map(a => a.title), error: error.message });
            } finally {
                progressBar.increment(1, { status: `决赛圈 - 第 ${round}/${tournamentRounds} 轮` });
            }
        }));
        await Promise.all(rankingPromises);
    }

    progressBar.stop();
    logger.info(`决赛圈排名完成。`);

    // 最终将文章按总分排序，并附加最终排名
    const finalRankedArticles = _.orderBy(articlesWithScores, ['tournamentScore'], ['desc']);

    return finalRankedArticles.map((article, index) => ({
        ...article,
        rank: index + 1,
    }));
}