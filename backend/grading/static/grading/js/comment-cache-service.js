/**
 * CommentCacheService - 评价缓存服务
 * 
 * 功能：
 * - 自动保存评价内容到浏览器本地存储
 * - 加载缓存的评价内容
 * - 清除缓存
 * - 清理过期缓存（7天前）
 * 
 * 需求: 5.1.1-5.1.8
 */
class CommentCacheService {
    constructor() {
        // 缓存键前缀
        this.cacheKeyPrefix = 'comment_cache_';
        // 自动保存间隔（毫秒）
        this.autosaveInterval = 2000; // 2秒
        // 缓存过期时间（毫秒）
        this.cacheExpiry = 7 * 24 * 60 * 60 * 1000; // 7天
        // 自动保存定时器
        this.autosaveTimer = null;
        // 当前文件路径
        this.currentFilePath = null;
        
        console.log('CommentCacheService initialized');
        
        // 启动时清理过期缓存
        this.cleanupExpired();
    }
    
    /**
     * 生成缓存键
     * @param {string} filePath - 文件路径
     * @returns {string} 缓存键
     */
    _generateCacheKey(filePath) {
        if (!filePath) {
            console.error('文件路径为空，无法生成缓存键');
            return null;
        }
        
        // 使用简单的哈希函数生成缓存键
        // 这样可以避免路径过长导致的存储问题
        const hash = this._simpleHash(filePath);
        return `${this.cacheKeyPrefix}${hash}`;
    }
    
    /**
     * 简单哈希函数
     * @param {string} str - 要哈希的字符串
     * @returns {string} 哈希值
     */
    _simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(36);
    }
    
    /**
     * 自动保存评价内容
     * 需求 5.1.1: 每隔2秒自动缓存评价内容到浏览器本地存储
     * 
     * @param {string} filePath - 文件路径
     * @param {string} commentText - 评价内容
     */
    autosave(filePath, commentText) {
        if (!filePath) {
            console.error('文件路径为空，无法自动保存');
            return;
        }
        
        // 清除之前的定时器
        if (this.autosaveTimer) {
            clearTimeout(this.autosaveTimer);
        }
        
        // 更新当前文件路径
        this.currentFilePath = filePath;
        
        // 设置新的定时器
        this.autosaveTimer = setTimeout(() => {
            this._saveToStorage(filePath, commentText);
            console.log(`评价已自动保存 - 文件: ${filePath}`);
        }, this.autosaveInterval);
    }
    
    /**
     * 保存到本地存储
     * @param {string} filePath - 文件路径
     * @param {string} commentText - 评价内容
     * @private
     */
    _saveToStorage(filePath, commentText) {
        const cacheKey = this._generateCacheKey(filePath);
        if (!cacheKey) {
            return;
        }
        
        const cacheData = {
            comment: commentText,
            timestamp: Date.now(),
            file_path: filePath
        };
        
        try {
            localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            console.log('评价已保存到本地存储:', cacheKey);
        } catch (e) {
            console.error('保存评价到本地存储失败:', e);
            // 如果存储空间不足，尝试清理过期缓存后重试
            if (e.name === 'QuotaExceededError') {
                console.log('存储空间不足，清理过期缓存后重试');
                this.cleanupExpired();
                try {
                    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
                    console.log('清理后重试成功');
                } catch (retryError) {
                    console.error('清理后重试仍然失败:', retryError);
                }
            }
        }
    }
    
    /**
     * 加载缓存的评价内容
     * 需求 5.1.3: 重新打开同一文件的评价对话框时，检查是否存在缓存的评价
     * 
     * @param {string} filePath - 文件路径
     * @returns {Object|null} 缓存数据 {comment, timestamp, file_path} 或 null
     */
    load(filePath) {
        if (!filePath) {
            console.error('文件路径为空，无法加载缓存');
            return null;
        }
        
        const cacheKey = this._generateCacheKey(filePath);
        if (!cacheKey) {
            return null;
        }
        
        try {
            const cacheDataStr = localStorage.getItem(cacheKey);
            if (!cacheDataStr) {
                console.log('没有找到缓存数据:', cacheKey);
                return null;
            }
            
            const cacheData = JSON.parse(cacheDataStr);
            
            // 检查缓存是否过期
            const age = Date.now() - cacheData.timestamp;
            if (age > this.cacheExpiry) {
                console.log('缓存已过期，删除:', cacheKey);
                this.clear(filePath);
                return null;
            }
            
            console.log('加载缓存成功:', cacheKey, cacheData);
            return cacheData;
        } catch (e) {
            console.error('加载缓存失败:', e);
            return null;
        }
    }
    
    /**
     * 清除指定文件的缓存
     * 需求 5.1.6: 评价成功保存到文件后，清除该文件对应的评价缓存
     * 
     * @param {string} filePath - 文件路径
     */
    clear(filePath) {
        if (!filePath) {
            console.error('文件路径为空，无法清除缓存');
            return;
        }
        
        const cacheKey = this._generateCacheKey(filePath);
        if (!cacheKey) {
            return;
        }
        
        try {
            localStorage.removeItem(cacheKey);
            console.log('缓存已清除:', cacheKey);
            
            // 如果清除的是当前文件的缓存，清除定时器
            if (this.currentFilePath === filePath && this.autosaveTimer) {
                clearTimeout(this.autosaveTimer);
                this.autosaveTimer = null;
            }
        } catch (e) {
            console.error('清除缓存失败:', e);
        }
    }
    
    /**
     * 清理过期缓存
     * 需求 5.1.7: 缓存数据超过7天，自动清理过期缓存
     */
    cleanupExpired() {
        console.log('开始清理过期缓存...');
        
        let cleanedCount = 0;
        const now = Date.now();
        
        try {
            // 遍历所有localStorage键
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                
                // 只处理评价缓存键
                if (key && key.startsWith(this.cacheKeyPrefix)) {
                    try {
                        const cacheDataStr = localStorage.getItem(key);
                        if (cacheDataStr) {
                            const cacheData = JSON.parse(cacheDataStr);
                            const age = now - cacheData.timestamp;
                            
                            // 如果缓存超过7天，删除
                            if (age > this.cacheExpiry) {
                                localStorage.removeItem(key);
                                cleanedCount++;
                                console.log('删除过期缓存:', key, '年龄:', Math.floor(age / (24 * 60 * 60 * 1000)), '天');
                            }
                        }
                    } catch (e) {
                        console.error('处理缓存键时出错:', key, e);
                        // 如果解析失败，删除这个损坏的缓存
                        localStorage.removeItem(key);
                        cleanedCount++;
                    }
                }
            }
            
            console.log(`清理完成，共删除 ${cleanedCount} 个过期缓存`);
        } catch (e) {
            console.error('清理过期缓存失败:', e);
        }
    }
    
    /**
     * 停止自动保存
     */
    stopAutosave() {
        if (this.autosaveTimer) {
            clearTimeout(this.autosaveTimer);
            this.autosaveTimer = null;
            console.log('自动保存已停止');
        }
    }
    
    /**
     * 获取所有缓存的文件路径
     * @returns {Array} 文件路径数组
     */
    getAllCachedFiles() {
        const files = [];
        
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                
                if (key && key.startsWith(this.cacheKeyPrefix)) {
                    try {
                        const cacheDataStr = localStorage.getItem(key);
                        if (cacheDataStr) {
                            const cacheData = JSON.parse(cacheDataStr);
                            files.push({
                                filePath: cacheData.file_path,
                                timestamp: cacheData.timestamp,
                                comment: cacheData.comment
                            });
                        }
                    } catch (e) {
                        console.error('解析缓存数据失败:', key, e);
                    }
                }
            }
        } catch (e) {
            console.error('获取缓存文件列表失败:', e);
        }
        
        return files;
    }
    
    /**
     * 检查是否有缓存
     * @param {string} filePath - 文件路径
     * @returns {boolean} 是否有缓存
     */
    hasCache(filePath) {
        const cacheData = this.load(filePath);
        return cacheData !== null && cacheData.comment && cacheData.comment.trim() !== '';
    }
}

// 创建全局实例
window.commentCacheService = new CommentCacheService();

console.log('CommentCacheService 已加载并初始化');
