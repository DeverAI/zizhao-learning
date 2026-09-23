# 自招学习（zizhao-learning）

上海中考**自主招生**每日素材系统：哲学 / 历史 / 高中古诗文 / 课程体系拔高点。  
面向初三：知识补漏 + 自招素材 + 找茬式追问，不是温柔陪聊。

## 特性

- 每日幂等素材（`GET /api/material/today`）
- 去重三层：硬键 → Jaccard → prompt 负例
- 归档降维（指纹可全量进 prompt）
- Agent 工具：邻仓检索摘要、计算器、画像、找茬、正文分段
- 人格：不讨好、催办事、绝望才兜底、前台无 Markdown
- 英语：单词卡三库（高考高频 / 介词搭配 / 熟词生义，会·模糊·不会 + 错词库）+ 段落背诵批改
- 小工具：语音/文本计算器（口述→算式→本地安全求值）、邻仓讲题黑板稿
- 上传收纳（讲解/素材/三观/知识体系/英语背诵）
- 顶栏**北京时间时钟 + 日期**；时间表自动高亮「今天」并默认选中
- 可选 Bearer 鉴权（`settings.api_password`）

## 时间基准

全项目只有一个时间口径：**北京时间（UTC+8）**，出口是 `GET /api/system/time`（免鉴权）。

- 网页顶栏每秒走时、每 10 分钟跟服务端校一次（防本机时钟被改错导致看错「今天」）
- 板端 SNTP 失败时改调同一接口做 HTTP 兜底对时（校园网常封 UDP 123）
- 素材 `day_key`、离线包 `day_key`、时间表「今天」都基于它
- Python 侧统一用 `config.beijing_now()`，禁止再出现裸 `datetime.now()`

## 素材域与字数

`settings.material_domains` 是**真正生效**的白名单（不再是摆设）：
`philosophy` / `history` / `classics` / `shared_curriculum` / `gap_fill`（初三补漏）/ `upload` / `knowledge`。
正文长度与音频预算同源：`material_body_min_chars` / `max_chars`（默认 1500–4500 字）→ 约 300 秒 MP3，
生成、审核挑刺、改写三处共用同一个预算函数，不再各写各的。

## 错误处理

任何 RE / 未捕获异常落项目根 `Err.log`（`backend/logger.record_error`）：
修复前先读 `Err.log`，修复后清空内容（不删文件）。夜间巡检、全局异常处理器均已接入。

## 共享源

只读接入同级目录 `学习Agent_new`（课程体系 / 知识树 / 海马体 / 本地 API 密钥）。  
可用环境变量 `ZIZHAO_SHARED_ROOT` 覆盖路径（本机配置，勿写进仓库）。  
跨仓说明见 `docs/letter_to_learningAgent_new.md`。

**脱敏**：本仓不含 API Key、`settings.json`、`storage/`、`backups/`、用户绝对路径。

## 快速开始

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

- 工作台：http://127.0.0.1:8010/
- OpenAPI：http://127.0.0.1:8010/docs

## 测试

```powershell
cd backend
python -m unittest discover -s . -p 'test_*.py' -v
# 活体 LLM（需已配置自注册 Key）：
# $env:RUN_LLM_LIVE='1'; python -m unittest test_llm_live -v
```

## 文档

| 文件 | 内容 |
|------|------|
| `自招素材系统技术方案.md` | 架构与机制 |
| `backend/README.md` | 接口与硬约定 |
| `updates/20260916_深度检修R10.md` | 最新一轮深度检修（硬伤 / 缺口 / 全链路验证） |
| `updates/20260912_深度检修R01.md` | 历史检修记录 |

## License

[AGPL-3.0](LICENSE)

网络提供服务时，若修改本项目，须按 AGPL 向用户提供对应源码。
