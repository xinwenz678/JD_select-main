# 简历解析契约草案（成员 B，任务 B1）

> 状态：**草案待确认**。本契约冻结前请在群里知会 A（持久化）、C（匹配）、D（结果页）。
> 实现见 `backend/app/schemas/resume.py`、`backend/app/services/resume_parser.py`
> 与 `backend/app/services/resume_diagnose.py`。

## 接口

`POST /api/resumes/parse`

请求：

```json
{ "text": "<简历全文纯文本>" }
```

- `text` 必填，去除首尾空白后不能为空；超长（>50000 字符）返回 422。

响应（HTTP 200）：

```json
{
  "schema_version": "resume-v1",
  "algorithm_version": "rule-v1",
  "resume": {
    "basic": { "name": "李明", "contact": { "email": "...", "phone": "..." } },
    "sections": [
      {
        "kind": "education",
        "heading": "教育背景",
        "line_start": 4,
        "line_end": 6,
        "lines": ["2021.09 - 2025.06   XX大学  计算机科学与技术  本科", "..."]
      }
    ],
    "skills": ["Python", "SQL", "FastAPI", "Docker"],
    "warnings": []
  }
}
```

## 字段约定

- `resume.basic`：姓名/联系方式**可缺失**，缺失时填 `null`。
- `resume.sections[].kind`：`education` | `experience` | `projects` | `skills` | `other`；
  `lines` 保留原文行，`line_start/line_end` 为该区块首尾非空行在原文中的行号（1 起），供诊断定位。
- `resume.skills`：仅来自「技能」区块的拆分结果，**不做同义词归一化**（归 C 的词典任务 C1）。
- `resume.warnings`：识别不完整时的提示（如缺教育区块、无技能词），不用于阻断。

## PDF 上传接口

`POST /api/resumes/upload-pdf`

- 请求头为 `Content-Type: application/pdf`，请求体直接传 PDF 二进制；
- 限制 10 MB、30 页，支持含文本层的 PDF，暂不支持扫描件 OCR 和密码保护文件；
- 成功响应在 `/parse` 的完整结果外增加 `text`（提取后的原文）和 `pages`（页数）；
- 错误文件返回 413、415 或 422，且不在日志中输出简历正文。

## 供大家确认的 3 个问题

1. C 做匹配时希望拿到「分好块的原文」（现状：`sections`），还是需要 B 额外输出「逐条经历条目」（需要进一步拆分条目粒度，工作量更大）？
2. 若简历没有独立「技能」区块（技能写在项目/经历里），C 是否直接在全文里扫技能词？（现状：B 只在技能区块里拆）
3. D 的结果页是否需要 B 额外返回「是否缺少某类区块」的布尔字段，还是用 `warnings` 文案即可？

## 诊断接口（任务 B4）

`POST /api/resumes/diagnose`：同一份 `text` 入参，输出**确定性规则诊断**（不依赖 LLM），
供结果页展示“量化亮点 / 表达建议 / 结构性缺失”。请求约束与 `/parse` 相同。

响应（HTTP 200）：

```json
{
  "schema_version": "resume-v1",
  "algorithm_version": "rule-v1",
  "summary": { "total": 4, "quantified": 1, "action_verb": 1, "suggestion": 2 },
  "diagnoses": [
    {
      "category": "suggestion",
      "line": 11,
      "section": "experience",
      "message": "该条有动作但缺少量化结果，说服力可以更强",
      "suggestion": "尝试补上数字：规模/时长/性能提升等，例如“…，使响应时间下降 30%”。"
    }
  ]
}
```

字段约定：

- `diagnoses[].category`：`quantified`（命中量化指标，正向亮点）| `action_verb`
  （经历行不以动作动词开头，建议改写）| `suggestion`（结构性缺失建议）。
- `line`：结论定位到的原文非空行号（1 起），区块级/全局结论为 `null`；
  `section`：`line` 所在区块 kind（可能为 `null`）。
- `summary` 为分类计数，等于 `diagnoses` 各 `category` 的计数和。

规则范围（详见 `backend/app/services/resume_diagnose.py` docstring）：

1. **行级（仅 experience/projects 正文行）**：正文行需以动作动词开头、含量化指标或含
   成果宾语词（系统/接口/app/pipeline 等），三者皆无的行视为岗位头衔/项目名而跳过，
   时间开头的条目头与过短标签同样跳过；命中“数字 + 单位/百分比”给出 `quantified`；
   不以动作动词开头给出 `action_verb`；动词开头但无量化给出补量化 `suggestion`。
2. **区块级**：教育经历无起止年份 → `suggestion`；技能词 < 3（或缺失）→ `suggestion`；
   缺少“教育背景”或“实习/项目经历”区块 → `suggestion`。

> 说明：诊断与 `/parse` 的 `warnings` 语义不同——`warnings` 表示解析不确定，
> `diagnoses` 是内容质量改进建议，两者可同时存在。

## 示例

`sample_data/resume_basic.txt` 为脱敏开发样例，正式 3 份样例随 B5 补充；
`sample_data/resume_weak.txt`（B4）为四类问题齐全的弱简历样例，用于演示诊断输出。
