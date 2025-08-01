// utils/helpers.js

import chalk from 'chalk';
import logger from './logger.js';
import CONFIG from '../config.js';

/**
 * 优雅地关闭程序，处理日志和退出码
 * @param {Error} [error] - 如果是错误退出，则传入Error对象
 * @returns {Promise<void>}
 */
export async function gracefulShutdown(error) {
    return new Promise(resolve => {
        if (error) {
            const errorMessage = `程序因致命错误而终止: ${error.message}`;
            console.error(chalk.red.bold(`\n❌ ${errorMessage}`));
            logger.error('顶层异常捕获', { error: error.message, stack: error.stack });
        } else {
            logger.info('--- 程序正常执行完毕 ---');
        }

        // 结束日志写入流
        logger.end(() => {
            console.log(chalk.blue.italic('日志系统已关闭。'));
            resolve();
            process.exit(error ? 1 : 0);
        });

        // 设置一个超时，防止日志系统关闭卡死
        setTimeout(() => {
            console.error(chalk.red('日志系统关闭超时，强制退出。'));
            resolve();
            process.exit(error ? 1 : 0);
        }, 3000);
    });
}

/**
 * 根据文章标题创建一个安全的文件名
 * @param {number} index - 文章的索引
 * @param {string} title - 文章标题
 * @returns {string} - 处理后的安全文件名
 */
export function createSafeArticleFilename(index, title) {
    const prefix = String(index + 1).padStart(2, '0');
    // 移除非法字符，替换空格，并截断长度
    const sanitizedTitle = title
        .replace(/[\/\\?%*:|"<>]/g, '-')
        .replace(/\s+/g, '_')
        .slice(0, 80);
    return `${prefix}_${sanitizedTitle}.md`;
}

/**
 * 根据分类名称获取对应的 Emoji 图标
 * @param {string} category - 分类名称
 * @returns {string} - Emoji 图标
 */
export function getCategoryEmoji(category) {
    return CONFIG.output.categoryEmojis[category] || CONFIG.output.categoryEmojis['默认'];
}