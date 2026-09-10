# 后端 API 契约

当前版本：0.1.0。基础地址：`http://127.0.0.1:8000`。Swagger：`/docs`；机器可读契约：`/openapi.json`。本文记录当前实现，字段细节以同一版本的 OpenAPI 为准。

## 接口清单

| 方法与路径 | 作用 |
|---|---|
| `GET /api/health` | 检查应用与数据库 |
| `POST /api/resumes/parse` | 解析粘贴的简历文本 |
| `POST /api/resumes/upload-pdf` | 提取并解析文本型 PDF（≤10MB、≤30页） |
| `POST /api/resumes/diagnose` | 规则化简历诊断 |
| `POST /api/jobs/parse` | 解析岗位标题、必需/加分/否定技能及证据 |
| `POST /api/matches` | 解析 JD、评分并原子保存一条历史记录 |
| `GET /api/matches?limit=10&offset=0` | 返回最近记录摘要，默认最近 10 条 |
| `GET /api/matches/{record_id}` | 按服务端 UUID 返回完整详情 |
| `POST /api/suggestions/star` | 返回 STAR 与 JD 定向建议，支持兼容模型/规则回退 |
| `POST /api/analysis-records` | 保存调用方已计算结果，供内部集成/测试使用 |
| `PATCH /api/analysis-records/{record_id}` | 只修改历史岗位名称 |
| `DELETE /api/analysis-records/{record_id}` | 删除指定历史记录 |

## 匹配

请求示例：

```json
{
  "resume_text": "项目经历\n使用 Python、SQL 完成数据分析",
  "jd_text": "数据分析实习生\n必须掌握 Python、SQL，了解 Tableau 者加分",
  "job_title": "数据分析实习生",
  "confirmed_skills": ["python", "SQL"],
  "confirmed_name": "合成候选人"
}
```

- `resume_text`、`jd_text` 必填，去除首尾空白后必须有内容，最多 100000 字符。
- `job_title` 最多 200 字符；为空时尝试从 JD 提取。
- `confirmed_skills` 不传时从原文提取；传空数组表示用户确认没有技能，不会回退原文。规范名、大小写变体和同义词统一处理。
- `confirmed_name` 可选，最多 200 字符，随结果快照保存。
- JD 非空但没有识别出任何可匹配技能时返回 422，不保存记录。

成功响应包含：`id`、`job_title`、`score`、`score_breakdown`、`matched_skills`、`missing_skills`、`resume_sections`、`job_skills`、`suggestions`、`evidence_items`、`confirmed_skills`、`confirmed_name`、`algorithm_version`。

评分使用固定规则：必需技能 60、加分技能 20、经历证据质量 20，总分为三项整数之和。人工确认但原文没有的技能，其证据 `source=confirmed_resume`、`line=null`，不会伪造原文行号。匹配分用于辅助判断，不代表录用概率。

## 历史

列表响应：

```json
{
  "items": [
    {
      "id": "服务端 UUID",
      "job_title": "数据分析实习生",
      "score": 91,
      "algorithm_version": "rule-v1",
      "created_at": "2026-09-10T09:00:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

`limit` 范围 1–100，`offset` 为非负整数。列表不返回简历/JD 大字段；详情必须使用 `id`，不能使用数组下标。详情包含创建时的原文、确认值、评分、证据和时间。记录按 `created_at`、`id` 降序稳定排列。

## STAR 建议

请求：

```json
{
  "experience": "参与课程报名系统，负责接口测试。",
  "jd_text": "需要 Python、SQL 和数据分析能力"
}
```

响应包含原文、`star.situation/task/action/result`、`optimized_draft`、`jd_keywords`、`metric_prompts`、`source` 和人工核实提示。`source` 为 `llm` 或 `rule-fallback`。

当 `backend/.env` 同时配置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 时，服务调用兼容的 `{LLM_BASE_URL}/chat/completions`；超时由 `LLM_TIMEOUT_SECONDS` 控制，默认 8 秒。无配置或模型/网络/响应失败时返回确定性规则建议，Level 1 不受影响。前端不会自动覆盖原简历。

## 持久化与错误

默认数据库为 `backend/jd_select.db`。`analysis_records` 使用 UUID 主键，结果保存为 JSON 快照；成功创建后 commit，异常 rollback，失败请求不留下半条记录。启动只创建缺失表，不删除数据。

统一错误结构：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数不符合要求",
    "details": []
  }
}
```

404 表示记录/路由不存在，405 表示方法不支持，422 表示输入校验失败，503 表示数据库不可用，500 表示未预期内部错误。错误响应和错误日志不回显完整简历、JD、SQL 参数或栈。

## 本地检查

启动项目后可执行：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Start-Process http://127.0.0.1:8000/docs
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

完整 B 复验入口为 `backend/.venv/Scripts/python.exe scripts/b-review.py`，证据写入 `docs/evidence/b-candidate/`。
