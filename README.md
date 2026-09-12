# 自招学习（zizhao-learning）

上海中考**自主招生**每日素材系统：哲学 / 历史 / 高中古诗文 / 课程体系拔高点。  
面向初三：知识补漏 + 自招素材 + 找茬式追问，不是温柔陪聊。

## 特性

- 每日幂等素材（`GET /api/material/today`）
- 去重三层：硬键 → Jaccard → prompt 负例
- 归档降维（指纹可全量进 prompt）
- Agent 工具：邻仓检索摘要、计算器、画像、找茬、正文分段
- 人格：不讨好、催办事、绝望才兜底、前台无 Markdown
- 英语背诵批改、上传收纳（讲解/素材/三观/知识体系/英语背诵）
- 可选 Bearer 鉴权（`settings.api_password`）

## 共享源

只读接入同级目录 `学习Agent_new`（课程体系 / 知识树 / 海马体 / API 密钥）。  
跨仓说明见 `docs/letter_to_learningAgent_new.md`。  
对方可 `SHARED_ACCESS: denied` 拒绝。

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
python -m unittest test_material_system test_agent_stack test_audit_fixes -v
```

## 文档

| 文件 | 内容 |
|------|------|
| `自招素材系统技术方案.md` | 架构与机制 |
| `backend/README.md` | 接口与硬约定 |
| `updates/20260912_深度检修R01.md` | 深度检修记录 |

## License

[AGPL-3.0](LICENSE)

网络提供服务时，若修改本项目，须按 AGPL 向用户提供对应源码。
