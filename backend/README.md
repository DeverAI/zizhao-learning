# 自招素材系统 · 后端

面向上海中考自主招生的每日素材服务。  
**资料共享 / 记忆共享来源**：左邻右舍 `../学习Agent_new`（只读，不复制其数据）。  
跨仓告知信：`学习Agent_new/updates/20260912_自招系统共享调用告知.md`（副本 `docs/letter_to_learningAgent_new.md`）。

## 产品硬约定

1. 不讨好；情绪支持仅限绝望档；默认催办事  
2. 渐进画像 stranger → observed → known，从提问方式学  
3. 前台无 Markdown（防 `**` 显示成「美元美元星号」）  
4. 无密钥/关 LLM 时 `degraded=true`，禁止伪造成功  
5. 邻仓先搜再读、限量摘要，禁止一次倾倒全仓  

## 共享源

| 类型 | 路径 | 用途 |
|------|------|------|
| 课程体系 | `学习Agent_new/backend/data/curriculum_cn_junior.json` | `band=自招` 灌计划表 |
| 知识树 | `.../storage/knowledge_tree.json` | 检索 |
| 海马体 | `.../hippocampus/profile.json` | 薄弱点注入 |
| 密钥 | `.../settings.json` | LLM（不落日志明文） |

拒绝方式：告知信头 `SHARED_ACCESS: denied`，或 `*_REVOKED.md`，或 AGENTS.md 声明。  
本地画像/增量只写本仓，不回写共享海马体。

## 启动

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

- 工作台：http://127.0.0.1:8010/  
- OpenAPI：http://127.0.0.1:8010/docs  

## Agent 工具

`search_shared` · `read_shared_excerpt` · `calculator` · `profile_note` · `set_agenda` · `refresh_material` · `challenge_material` · `segment_material_text`

## 找茬与补漏

- `POST /api/material/challenge`：定义边界/出处/反例/考法/行动，多轮抬杠  
- `POST /api/material/plan/seed_gap`：海马体弱项 → 补漏计划  
- `POST /api/material/plan/recycle`：计划耗尽后回收  
- `POST /api/material/segment`：正文分段（TTS 未接时 `audio_ready=false`）  
- `GET /api/material/archive/{id}/body`：归档正文回读  

## 鉴权

`settings.json` 里 `api_password` **非空**时，除 `/` `/docs` `/static` `/api/system/health` 外需  
`Authorization: Bearer <password>`。本地留空则开放。

## 上传收纳

`POST /api/upload`：PNG/JPG/TXT/MD/PDF/DOC/DOCX（≤20MB）  
框架：讲解 / 素材 / 三观 / 知识体系 / 英语背诵  

- 素材 → 进 `material_plan`  
- 英语背诵 → 自动切段进背诵库  
- 图片不假装 OCR  

## 英语背诵

- `GET /api/recitation/next`  
- `POST /api/recitation/grade`（规则找茬；可选 LLM 点评）  

## 主要 API

| 方法 | 路径 |
|------|------|
| GET | `/api/material/today` |
| POST | `/api/material/chat` |
| POST | `/api/material/refresh` |
| POST | `/api/upload` |
| GET | `/api/profile` |
| GET | `/api/shared/status` |

## 去重三层

L1 硬键 `domain|source|title` → L2 Jaccard≥0.6 → L3 prompt 负例

## 测试

```powershell
python -m unittest test_material_system test_agent_stack test_audit_fixes -v
```

深度检修记录：`updates/20260912_深度检修R01.md`  
备份目录：`backups/audit_r01_20260912/`

## 对应技术方案

P1–P4/P6 主链路 + Agent + 上传收纳 + 背诵 + 画像 + 补漏灌种 + 找茬 + 文本分段；  
P5 MP3 文件生成仍未接 TTS（不伪造）。
