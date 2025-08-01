// modules/crawler.js

import chalk from 'chalk';
import pLimit from 'p-limit';
import _ from 'lodash';
import CONFIG from '../config.js';
import logger from '../utils/logger.js';
import { fetchAndParsePage, callLLM } from '../services/network.js';

/**
 * (已重构) 发现文章链接并通过多轮瑞士制资格赛筛选出候选者。
 * 不再是简单的分组淘汰，而是通过多轮比拼和积分，更公平地选出优胜者。
 * @param {import('ora').Ora} spinner - Ora微调器实例，用于显示状态
 * @param {import('cli-progress').SingleBar} progressBar - 进度条实例
 * @returns {Promise<Array<object>>} - 通过资格赛的候选文章元数据列表
 */
export async function discoverAndRankContenders(spinner, progressBar) {
    let pagesToVisit = [{ url: CONFIG.startUrl, depth: 1 }];
    const visitedUrls = new Set([CONFIG.startUrl]);
    const allFoundLinks = new Map();

    spinner.start(chalk.cyan('开始抓取网站链接...'));

    let pagesExplored = 0;
    while (pagesToVisit.length > 0) {
        const currentPage = pagesToVisit.shift();
        if (currentPage.depth > CONFIG.crawling.maxDepth) continue;

        pagesExplored++;
        spinner.text = `[${pagesExplored}] [深度 ${currentPage.depth}] 探索页面: ${currentPage.url}`;

        try {
            const $ = await fetchAndParsePage(currentPage.url);
            const baseUrl = currentPage.url;
            const newCategoryPages = [];
            const linkElements = $('a').toArray();

            for (const el of linkElements) {
                const linkUrl = $(el).attr('href');
                const linkTitle = $(el).text().trim().replace(/\s+/g, ' ');

                if (linkUrl && linkTitle && linkTitle.length > 4 && !CONFIG.crawling.uselessTitleKeywords.some(kw => linkTitle.includes(kw))) {
                    try {
                        const absoluteUrl = new URL(linkUrl, baseUrl).href;
                        const urlObject = new URL(absoluteUrl);
                        const canonicalUrl = `${urlObject.protocol}//${urlObject.hostname}${urlObject.pathname}`;

                        if ((urlObject.protocol === 'http:' || urlObject.protocol === 'https:') &&
                            !urlObject.pathname.match(/\.(pdf|zip|jpg|png|gif|css|js|mp3|mp4|xml|ico)$/i) &&
                            !visitedUrls.has(canonicalUrl)) {
                            
                            visitedUrls.add(canonicalUrl);
                            const { system, user } = CONFIG.prompts.classifyLinkType(linkTitle);
                            const type = await callLLM([{ role: 'system', content: system }, { role: 'user', content: user }], 0.1);

                            if (type.includes('article')) {
                                allFoundLinks.set(canonicalUrl, { url: canonicalUrl, title: linkTitle, type: 'article' });
                            } else if (type.includes('category') && currentPage.depth < CONFIG.crawling.maxDepth) {
                                newCategoryPages.push({ url: canonicalUrl, title: linkTitle, type: 'category' });
                            }
                        }
                    } catch (e) { /* 忽略无效URL */ }
                }
            }
            if (newCategoryPages.length > 0) {
                const pagesToAdd = newCategoryPages
                    .slice(0, CONFIG.crawling.maxCategoryPages)
                    .map(p => ({ url: p.url, depth: currentPage.depth + 1 }));
                pagesToVisit.push(...pagesToAdd);
            }
        } catch (error) {
            spinner.warn(chalk.yellow(`页面探索失败 ${currentPage.url}: ${error.message}`));
            continue;
        }
    }

    spinner.succeed(chalk.green(`链接抓取完成! 共发现 ${allFoundLinks.size} 篇不重复的文章链接.`));

    let articleLinks = Array.from(allFoundLinks.values()).map(link => ({ ...link, score: 0 }));
    if (articleLinks.length === 0) return [];

    // --- 资格赛 (重构为瑞士制) ---
    const { qualificationRounds, qualificationGroupSize, qualificationPoints, qualificationConcurrency } = CONFIG.ranking;
    const totalComparisons = qualificationRounds * Math.ceil(articleLinks.length / qualificationGroupSize);
    progressBar.start(totalComparisons, 0, { status: "资格赛 - 初始化..." });

    const limit = pLimit(qualificationConcurrency);

    for (let round = 1; round <= qualificationRounds; round++) {
        // 第一轮随机分组，后续轮次根据分数排序分组
        const articlesToRank = round === 1 
            ? _.shuffle(articleLinks) 
            : _.orderBy(articleLinks, ['score'], ['desc']);

        const groups = _.chunk(articlesToRank, qualificationGroupSize);

        const qualificationPromises = groups.map(group => limit(async () => {
            try {
                const groupTitles = group.map(link => link.title);
                const { system, user } = CONFIG.prompts.qualifyLinks(groupTitles, CONFIG.taskDescription);
                const responseText = await callLLM([{ role: 'system', content: system }, { role: 'user', content: user }], 0.2);

                const rankedIndices = responseText.split(',').map(n => parseInt(n.trim(), 10) - 1).filter(n => !isNaN(n));

                rankedIndices.forEach((originalIndex, rank) => {
                    const articleInGroup = group[originalIndex];
                    if (articleInGroup && qualificationPoints[rank] !== undefined) {
                        // 在主列表中找到对应的文章并累加分数
                        const targetArticle = articleLinks.find(a => a.url === articleInGroup.url);
                        if (targetArticle) {
                            targetArticle.score += qualificationPoints[rank];
                        }
                    }
                });
            } catch (error) {
                logger.warn('资格赛小组排名失败', { error: error.message });
            } finally {
                progressBar.increment(1, { status: `第 ${round}/${qualificationRounds} 轮评估中...` });
            }
        }));
        await Promise.all(qualificationPromises);
    }

    progressBar.stop();
    
    // 按最终得分排序，选出优胜者进入决赛圈
    const finalRankedLinks = _.orderBy(articleLinks, ['score'], ['desc']);
    const contenders = finalRankedLinks.slice(0, CONFIG.ranking.contendersToRank);
    
    logger.info(`资格赛完成，根据 ${qualificationRounds} 轮积分，选出 ${contenders.length} 位决赛选手。`);

    if (contenders.length > 0) {
        console.log(chalk.cyan.bold(`\n✅ 资格赛完成! ${contenders.length} 篇文章晋级决赛圈.`));
    }
    
    return contenders;
}