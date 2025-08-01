// utils/logger.js

import winston from 'winston';
import path from 'path';
import fs from 'fs/promises';
import CONFIG from '../config.js';

const logsDir = path.join(CONFIG.outputBaseDir, '..', 'logs'); // 将日志文件放在output目录的同级
await fs.mkdir(logsDir, { recursive: true });

/**
 * @description 应用的日志记录器实例 (winston)
 */
const logger = winston.createLogger({
    level: 'debug', // 记录所有级别的日志
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        // 将 'info' 及以上级别的日志写入文件
        new winston.transports.File({
            filename: path.join(logsDir, `${new Date().toISOString().slice(0, 10)}.log`),
            level: 'info',
        }),
    ],
});

// 根据调试模式决定是否向控制台输出日志
if (!CONFIG.debugMode) {
    // 非调试模式，只在控制台显示 info 及以上级别
    logger.add(new winston.transports.Console({
        level: 'info',
        format: winston.format.combine(
            winston.format.colorize(),
            winston.format.printf(info => `${new Date(info.timestamp).toLocaleTimeString()} ${info.level}: ${info.message}`)
        ),
    }));
} else {
    // 调试模式，在控制台显示所有 debug 及以上级别
    logger.add(new winston.transports.Console({
        level: 'debug',
        format: winston.format.combine(
            winston.format.colorize(),
            winston.format.printf(info => `${new Date(info.timestamp).toLocaleTimeString()} ${info.level}: ${info.message}`)
        ),
    }));
}

export default logger;