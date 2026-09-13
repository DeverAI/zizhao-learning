# 自招学习 · 平台后端

多组件学习平台：自招素材 / 英语背诵 / 古诗文 / 时间表 / 资料库 / 设备。  
可选只读共享同级 `学习Agent_new`；**本仓常驻资料与时间表不依赖邻仓**。

## 快速开始

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

- 前端：http://127.0.0.1:8010/
- OpenAPI：http://127.0.0.1:8010/docs

## 鉴权

| 方式 | 说明 |
|------|------|
| 邮箱验证码 | send-code → login；未配 SMTP 写 local outbox |
| PassKey | begin/finish/login（简化挑战流） |
| ESP 设备 | provision 一次性 PassKey → device/login 换 sid |
| 会话 | HttpOnly Cookie `zsid` = `sid.hmac` |

限流分桶（default/auth/upload）。SQL 参数化。`ZIZHAO_SESSION_SECRET` 生产必改。

## 主要 API

- `GET /api/home` 组件主页  
- `POST /api/components/toggle|request`  
- `GET/POST /api/timetable` · `POST /api/timetable/bulk`  
- `GET/POST /api/resident` 常驻资料  
- `POST /api/media/upload` OCR/文本/MP3 · `GET /api/media/{id}/download`  
- `POST /api/material/today|chat|challenge` 自招链路  
- `POST /api/auth/device/*` ESP  

## 脱敏

不含 API Key、`settings.json`、`storage/`、用户绝对路径。

## 审核门控（硬约定）

- 当日素材必须 **多轮挑刺** 直到 `review_status=passed`  
- **未通过禁止出音频**；离线包 `audio_ready=false` 时板子禁播  
- `POST /api/review/run` 手动；夜间巡检自动审全用户  

## 自注册 API（OpenAI 兼容）

主页「自注册 API」：文本模型 + TTS 各一个。  
`GET/POST /api/settings/apis*`；生成/对话/TTS **优先用户 Key**，再共享 fallback。

## 设备

- 登录：`/api/auth/device/login`  
- 离线：`/api/offline/manifest|bundle`（登录后自动下载缓存）  
- 开关机：`/api/device/power` 默认 04:30 关 / 06:00 开 / 开机 15min 无活动再关  
- 现场配网：AP `Zizhao-Setup-*` + `/api/device/onsite-config`  
- 10 分钟无操作音量最小（板端，见 `hardware/`）  

## 测试

```powershell
python -m unittest test_review_gate test_offline_api test_multiuser test_r03_fixes test_platform test_material_system test_audit_fixes test_agent_stack -v
# 活体 LLM（需已配置自注册 Key）：
# $env:RUN_LLM_LIVE='1'; python -m unittest test_llm_live -v
```

记录：`updates/20260912_R05审核门控与设备策略.md`  
License：AGPL-3.0
