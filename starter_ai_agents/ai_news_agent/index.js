// index.js

import path from 'path';
import fs from 'fs/promises';
import chalk from 'chalk';
import ora from 'ora';
import cliProgress from 'cli-progress';
import boxen from 'boxen';

import CONFIG from './config.js';
import logger from './utils/logger.js';
import { gracefulShutdown } from './utils/helpers.js';
import { discoverAndRankContenders } from './modules/crawler.js';
import { groupAndDeduplicateArticles } from './modules/grouper.js'; // <-- 引入新模块
import { runFinalTournament } from './modules/ranker.js';
import { processAndSummarizeArticles } from './modules/processor.js';
import { generateFinalReport } from './modules/reporter.js';


/**
 * @description 主执行函数
 */
async function main() {
    console.log(boxen(chalk.bold.cyan('AI新闻简报生成器 (模块化版)'), { padding: 1, margin: 1, borderStyle: 'double', borderColor: 'cyan' }));
    logger.info('--- 程序启动 ---');

    const today = new Date().toISOString().slice(0, 10);
    const domain = CONFIG.startUrl.split('://')[1]?.split('/')[0]
    const dailyOutputDir = path.join(CONFIG.outputBaseDir, `${today}_${domain}`);
    await fs.mkdir(dailyOutputDir, { recursive: true });

    // 初始化UI组件
    const spinner = ora({ text: '初始化...', spinner: 'dots' });
    const multiBar = new cliProgress.MultiBar({
        clearOnComplete: false,
        hideCursor: true,
        format: `{step} |${chalk.cyan('{bar}')}| {percentage}% | {value}/{total} | {status}`,
    }, cliProgress.Presets.shades_classic);

    let articlesToProcessCount = 0;
    let successfulArticleCount = 0;

    try {
        // --- 步骤 1: 抓取与资格赛 ---
        console.log(boxen(chalk.bold.cyan('[步骤 1/5] 抓取链接并进行资格赛筛选'), { padding: 1, margin: { top: 1, bottom: 1 }, borderStyle: 'round', borderColor: 'cyan' }));
        const qualificationProgressBar = multiBar.create(1, 0, { step: chalk.magenta.bold('资格赛'.padStart(6)) });
        const contenders = await discoverAndRankContenders(spinner, qualificationProgressBar);
        multiBar.remove(qualificationProgressBar);

        if (contenders.length === 0) {
            console.log(chalk.green('\n任务完成。根据筛选标准，未发现足够进入决赛圈的文章。'));
            logger.info('任务正常结束，未发现高价值文章。');
            await gracefulShutdown();
            return;
        }

        // --- (新) 步骤 2: 文章聚类与去重 ---
        console.log(boxen(chalk.bold.cyan('[步骤 2/5] 基于关键词的文章聚类与去重'), { padding: 1, margin: { top: 1, bottom: 1 }, borderStyle: 'round', borderColor: 'cyan' }));
        const groupingProgressBar = multiBar.create(contenders.length, 0, { step: chalk.cyan.bold('文章聚类'.padStart(6)) });
        const uniqueContenders = await groupAndDeduplicateArticles(contenders, groupingProgressBar);
        multiBar.remove(groupingProgressBar);
        console.log(chalk.cyan.bold(`\n✅ 聚类完成! 从 ${contenders.length} 篇候选文章中筛选出 ${uniqueContenders.length} 篇独特的文章进入决赛圈.`));

        // --- 步骤 3: 决赛圈排名 ---
        console.log(boxen(chalk.bold.cyan('[步骤 3/5] 决赛圈锦标赛排名'), { padding: 1, margin: { top: 1, bottom: 1 }, borderStyle: 'round', borderColor: 'cyan' }));
        const tournamentProgressBar = multiBar.create(1, 0, { step: chalk.yellow.bold('决赛圈'.padStart(6)) });
        const rankedArticles = await runFinalTournament(uniqueContenders, tournamentProgressBar); // <-- 使用去重后的文章列表
        multiBar.remove(tournamentProgressBar);

        const articlesToProcess = rankedArticles.slice(0, CONFIG.processing.maxArticlesToProcess);
        articlesToProcessCount = articlesToProcess.length;
        console.log(chalk.cyan.bold(`\n✅ 决赛圈完成! 最终选定 ${articlesToProcess.length} 篇文章进行深度处理.`));

        // --- 步骤 4: 处理文章与生成报告 ---
        console.log(boxen(chalk.bold.cyan(`[步骤 4/5] 逐篇处理 ${articlesToProcess.length} 篇高价值文章 (内置失败重试)`), { padding: 1, margin: { top: 1, bottom: 1 }, borderStyle: 'round', borderColor: 'cyan' }));
        const processingProgressBar = multiBar.create(articlesToProcess.length, 0, { step: chalk.blue.bold('文章处理'.padStart(6)) });
        const successfulArticles = await processAndSummarizeArticles(articlesToProcess, dailyOutputDir, processingProgressBar);
        successfulArticleCount = successfulArticles.length;
        
        // --- 步骤 5: 生成最终简报 ---
        console.log(boxen(chalk.bold.cyan('[步骤 5/5] 生成最终简报'), { padding: 1, margin: { top: 1, bottom: 1 }, borderStyle: 'round', borderColor: 'cyan' }));
        const output = await generateFinalReport(successfulArticles, dailyOutputDir, spinner);

        multiBar.stop();

        // 输出最终的任务总结信息
        if (output) {
            const summaryBox = boxen(
                `${chalk.bold.green('🎉 所有任务已成功完成!')}\n\n` +
                `主报告已保存至: ${chalk.yellow(output.reportFilePath)}\n\n` +
                `计划处理文章数: ${articlesToProcessCount} 篇\n` +
                `成功生成报告篇数: ${chalk.green(successfulArticleCount)} 篇\n` +
                `最终失败篇数: ${chalk.red(articlesToProcessCount - successfulArticleCount)} 篇\n\n` +
                `每篇文章的独立Markdown报告保存在:\n${chalk.yellow(output.individualArticlesDir)}`,
                { padding: 1, margin: 1, borderStyle: 'round', borderColor: 'green', title: '任务总结' }
            );
            console.log(summaryBox);
        } else if (successfulArticleCount === 0) {
             console.log(boxen(
                `${chalk.bold.yellow('⚠️  任务已结束，但未能成功处理任何文章。')}\n\n` +
                `计划处理文章数: ${articlesToProcessCount} 篇\n` +
                `成功生成报告篇数: ${chalk.green(0)} 篇\n` +
                `最终失败篇数: ${chalk.red(articlesToProcessCount)} 篇\n\n` +
                `请检查日志文件获取详细的错误信息。`,
                { padding: 1, margin: 1, borderStyle: 'round', borderColor: 'yellow', title: '任务总结' }
            ));
        }

        await gracefulShutdown();

    } catch (error) {
        spinner.fail(chalk.red.bold(`主流程发生严重错误: ${error.message}`));
        multiBar.stop();
        await gracefulShutdown(error);
    }
}

// --- 全局进程异常捕获 ---
process.on('unhandledRejection', (reason, promise) => {
    const error = new Error(`未处理的Promise拒绝: ${reason instanceof Error ? reason.message : reason}`);
    gracefulShutdown(error);
});

process.on('uncaughtException', (error, origin) => {
    error.message = `未捕获的异常 (${origin}): ${error.message}`;
    gracefulShutdown(error);
});

// --- 启动程序 ---
main();