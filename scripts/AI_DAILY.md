# 每日 AI 知识任务

- 配置：`.github/workflows/fenno.yml`，每天北京时间 09:15 运行。
- 输出：`ai-daily/YYYY-MM-DD.md`；`ai-daily/README.md` 是历史索引。
- 来源：Hugging Face 博客、Google Research 博客、arXiv cs.AI 论文 RSS。
- 范围：近 7 天内未收录的文章，每个来源每天最多 3 条，标题及摘要保留原文。
- 无第三方 Python 依赖，无需配置 API 密钥。手动执行：`python scripts/ai_daily.py`。
- 在仓库 Actions 页面选择「Fenno 每日 AI 知识」，点击 Run workflow 可立即运行。
- 修改来源和条数：编辑 `scripts/ai_daily.py`；修改时间：编辑工作流中的 cron（UTC）。
- 单个来源失败时继续收集并在日报中注明；所有来源失败则任务失败，不覆盖已有结果。
- 同日重复运行会跳过已有日报；已收录链接保存在 `ai-daily/seen.json`，不会跨日重复收录。
- GitHub 定时运行可能延迟；公开仓库 60 天无活动时定时工作流可能自动停用。
- 工作流需要仓库允许 Actions 写入内容；分支保护禁止机器人直接推送时，保存步骤会失败，需按仓库策略调整。
- 这是公开资料收集任务，不使用大模型生成中文总结，也不会修改现有 `AI资讯.md`。
