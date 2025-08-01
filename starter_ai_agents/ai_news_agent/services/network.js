// services/network.js

import axios from 'axios';
import * as cheerio from 'cheerio';
import Mercury from '@postlight/mercury-parser';
import CONFIG from '../config.js';
import logger from '../utils/logger.js';

/**
 * 获取并使用Cheerio解析一个网页
 * @param {string} url - 要抓取的页面URL
 * @returns {Promise<cheerio.CheerioAPI>} - Cheerio实例
 * @throws 如果抓取或解析失败，则抛出错误
 */
export async function fetchAndParsePage(url) {
    try {
        const { data: html } = await axios.get(url, {
            headers: CONFIG.network.headers,
            timeout: CONFIG.network.fetchTimeout
        });
        return cheerio.load(html);
    } catch (error) {
        logger.error(`抓取并解析页面失败: ${url}`, { message: error.message });
        throw new Error(`抓取页面失败 ${url}: ${error.message}`);
    }
}

/**
 * 使用Mercury Parser提取文章核心内容
 * @param {string} url - 文章URL
 * @returns {Promise<{title: string, content: string}>} - 包含标题和纯文本内容的对象
 * @throws 如果内容提取失败，则抛出错误
 */
export async function extractArticleContent(url) {
    try {
        const result = await Mercury.parse(url, { headers: CONFIG.network.headers });
        if (!result) return { title: '无标题', content: '' };

        // 将HTML内容转换为纯文本
        const plainTextContent = result.content
            ? cheerio.load(result.content).text().replace(/\s{2,}/g, ' ').trim()
            : '';

        return {
            title: result.title || '无标题',
            content: plainTextContent,
        };
    } catch (error) {
        logger.error(`Mercury parser 在此URL失败: ${url}`, { message: error.message });
        throw new Error(`内容提取失败 ${url}: ${error.message}`);
    }
}

/**
 * 调用大语言模型 (LLM) API
 * @param {Array<object>} messages - 发送给LLM的消息数组 (遵循OpenAI格式)
 * @param {number} temperature - LLM的温度参数
 * @param {number} [timeout] - 本次请求的特定超时时间 (ms)，如果未提供则使用默认值
 * @returns {Promise<string>} - LLM返回的内容文本
 * @throws 如果LLM调用在所有重试后仍然失败，则抛出错误
 */
export async function callLLM(messages, temperature, timeout) {
    const body = {
        messages,
        temperature,
        max_tokens: CONFIG.llm.maxTokens,
        stream: false
    };

    logger.debug('LLM Request Start', { url: CONFIG.llm.studioUrl });
    logger.debug('LLM Request Body:', { prompt: messages.slice(-1)[0].user });

    for (let i = 0; i < CONFIG.llm.maxRetries; i++) {
        try {
            const response = await axios.post(CONFIG.llm.studioUrl, body, {
                timeout: timeout || CONFIG.llm.requestTimeout
            });
            const content = response.data.choices[0].message.content.trim();
            logger.debug('LLM Request Success', { response: content });
            return content;
        } catch (error) {
            logger.warn(`LLM调用在第 ${i + 1} 次尝试时失败`, { error: error.message });
            if (i === CONFIG.llm.maxRetries - 1) {
                throw new Error(`LLM调用失败 (已达最大重试次数): ${error.message}`);
            }
            await new Promise(res => setTimeout(res, CONFIG.llm.retryDelay * (i + 1)));
        }
    }
    // 此处理论上不会到达，因为循环内已抛出错误
    throw new Error('LLM调用在所有重试后仍然失败。');
}