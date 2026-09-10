/**
 * 演示用脱敏简历样例（B3/B6）。
 * 文本来自 sample_data/ 下的样例文件，仅用于演示解析与诊断，不含真实个人信息。
 */
export interface ResumeSample {
  id: string;
  label: string;
  description: string;
  text: string;
}

const STRONG: ResumeSample = {
  id: 'strong',
  label: '良好示例',
  description: '区块完整、技能丰富、含量化成果',
  text: [
    '李明',
    '邮箱：liming.dev@example.com',
    '电话：13800138000',
    '',
    '教育背景',
    '2021.09 - 2025.06   XX大学  计算机科学与技术  本科',
    '主修课程：数据结构、数据库原理、操作系统',
    '',
    '实习经历',
    '2024.06 - 2024.09  XX科技有限公司  后端开发实习生',
    '负责订单模块接口开发与联调，使用 Python/FastAPI',
    '修复线上缺陷 12 个，接口响应时间平均下降 30%',
    '',
    '项目经历',
    '2024.03 - 2024.05   简历诊断 Web 应用（课程项目）',
    '使用 React + FastAPI 实现前后端分离架构',
    '独立完成 SQLite 数据表设计与查询优化',
    '',
    '专业技能',
    '编程语言：Python、SQL、JavaScript',
    '后端框架：FastAPI、Django',
    '数据库：SQLite、MySQL',
    '工具：Git、Docker、Linux',
  ].join('\n'),
};

const WEAK: ResumeSample = {
  id: 'weak',
  label: '薄弱示例',
  description: '缺少量化结果、动词开头弱、技能覆盖窄',
  text: [
    '赵强',
    '邮箱：zhaoqiang@example.com',
    '电话：13612345678',
    '',
    '教育背景',
    'XX大学  计算机科学与技术  本科',
    '',
    '实习经历',
    '2023.07 - 2023.10  XX数据科技有限公司  后端实习生',
    '数据平台接口开发与联调工作',
    '修复线上系统若干历史遗留问题并完成回归验证',
    '',
    '专业技能',
    'Java',
  ].join('\n'),
};

const MISSING_SECTIONS: ResumeSample = {
  id: 'missing',
  label: '缺区块示例',
  description: '无教育背景与项目区块，技能词少于 3 项',
  text: [
    '王五',
    '电话：13912345678',
    '',
    '实习经历',
    '2024.06-2024.09  某互联网公司  数据分析实习生',
    '负责搭建用户行为指标体系，参与设计 6 张核心报表',
    '使用 Python、SQL 完成 ETL 与异常归因分析，交付周期缩短约 25%',
  ].join('\n'),
};

export const RESUME_SAMPLES: ResumeSample[] = [STRONG, WEAK, MISSING_SECTIONS];
