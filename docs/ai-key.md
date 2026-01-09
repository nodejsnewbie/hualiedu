# Ark API 密钥排查与诊断

## 常见问题
- 环境变量名不一致：统一使用 `ARK_API_KEY`
- 密钥格式错误：`ark-` / `sk-` / 原始格式
- 账户/权限/余额/区域未配置

## 排查步骤
1) 确认 `.env` 中 `ARK_API_KEY` 与 `ARK_MODEL`
2) 使用 `uv run python -c "from dotenv import load_dotenv;import os;load_dotenv();print(os.getenv('ARK_API_KEY'))"`
3) 诊断与连通：可运行集成测试或最小化调用

## 失败示例与建议
- 401 The API key format is incorrect → 复制完整密钥/重新生成/检查权限
- 网络或区域错误 → 校验端点、区域、网络策略

## 预防
- 不硬编码密钥；仅 `.env`
- 定期轮换/权限最小化
- 本地和 CI 使用不同密钥
