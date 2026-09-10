# 样例数据

`analysis-record.example.json` 是 A3 持久化接口的合成验收输入，分数为示例值，不是算法输出。调用步骤见 `docs/api.md`。

脱敏简历样例（成员 B 提供，任务 B5/B4），供解析器/诊断器开发、测试和联调使用。

| 文件 | 形态 | 解析预期 |
|---|---|---|
| `resume_basic.txt` | 中文、信息齐全、四区块 | 姓名/邮箱/电话 + education/experience/projects/skills，10 个技能词，无 warnings；诊断：4 条行级建议 |
| `resume_en.txt` | 英文、紧凑排版 | 英文区块标题识别、技能含 `C++`/`Spring Boot` 等多词技能 |
| `resume_missing_sections.txt` | 缺教育背景、无独立技能区 | 命中 education/skills 两条缺失 warnings，技能词不会从经历正文中扫出（见契约第 2 问）；诊断含缺教育背景建议 |
| `resume_weak.txt` | 中文、四类问题齐全（无动词/无量化/教育无年份/技能仅 1 项） | 解析正常；诊断：action_verb×1 + suggestion×3，用于演示 B4 输出 |
| `resume_optimized.txt` | 中文，`resume_weak.txt` 同人（赵强）优化版 | 4 区块 11 技能；诊断 quantified×5、suggestion×0，与 weak 版构成 B6 原始/优化对比 |

对比演示脚本见 `docs/demo-resume-compare.md`（B6）。

简历样例由 B 提供；JD 样例和人工标注结果由 C 提供。

