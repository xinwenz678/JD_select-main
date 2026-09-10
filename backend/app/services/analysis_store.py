"""分析记录持久化 —— C4 最小占位实现（标准库 sqlite3），待 A3 SQLAlchemy 层替换。

背景：C4 要保证 /api/matches 端到端可演示（保存记录并返回 id），
而 A3（SQLAlchemy 数据模型 + CRUD）尚未合入 main。故先提供本适配器：

    - 使用 Python 标准库 sqlite3 + settings.database_url（默认 sqlite:///./jd_select.db），
      不引入 SQLAlchemy，不与 A 的 A3 领域冲突；
    - 表结构完全对齐契约 analysis_records 字段；
    - 对外只暴露三个函数，签名固定：
          save_record(record: dict) -> str          # 保存，返回新记录 id
          list_records(limit: int = 10) -> list[dict]  # 最近列表（摘要）
          get_record(record_id: str) -> dict | None    # 详情（含原文与 result_json）
    - A3 合入后，由 A 以 SQLAlchemy 实现替换本文件内部逻辑即可，调用方（api/matches.py）
      无需改动。

隐私约束：本模块不打印、不记录完整简历/JD 文本，仅按需写入数据库文件
（*.db 已被 .gitignore 忽略，不会进入版本库）。
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

# 允许本文件被 scripts/ 下的脚本以绝对路径直接运行
if __package__ in (None, ""):
    import sys
    _BACKEND_DIR = Path(__file__).resolve().parents[2]  # services -> app -> backend
    if str(_BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(_BACKEND_DIR))

from app.core.config import settings  # noqa: E402

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_records (
    id TEXT PRIMARY KEY,
    job_title TEXT,
    resume_text TEXT,
    jd_text TEXT,
    score INTEGER,
    result_json TEXT,
    algorithm_version TEXT,
    created_at TEXT
);
"""


def _db_path() -> Path:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        return Path(url[len("sqlite:///"):])
    raise ValueError(f"analysis_store 当前仅支持 sqlite，database_url={url!r}")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def save_record(record: dict) -> str:
    """保存一条分析记录，返回新生成的 uuid id。

    record 字段：job_title / resume_text / jd_text / score / result(dict) / algorithm_version
    """
    record_id = str(uuid.uuid4())
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO analysis_records "
            "(id, job_title, resume_text, jd_text, score, result_json, algorithm_version, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record_id,
                record.get("job_title", ""),
                record.get("resume_text", ""),
                record.get("jd_text", ""),
                int(record.get("score", 0)),
                json.dumps(record.get("result", {}), ensure_ascii=False),
                record.get("algorithm_version", ""),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    return record_id


def list_records(limit: int = 10) -> list[dict]:
    """最近 limit 条记录的摘要列表（不含简历/JD 原文与 result_json）。"""
    limit = max(1, min(int(limit), 100))
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, job_title, score, algorithm_version, created_at "
            "FROM analysis_records "
            "ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": row[0],
            "job_title": row[1],
            "score": row[2],
            "algorithm_version": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def get_record(record_id: str) -> dict | None:
    """按 id 读取记录详情（含原文与 result），不存在返回 None。"""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT id, job_title, resume_text, jd_text, score, result_json, algorithm_version, created_at "
            "FROM analysis_records WHERE id = ?",
            (record_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "job_title": row[1],
        "resume_text": row[2],
        "jd_text": row[3],
        "score": row[4],
        "result": json.loads(row[5] or "{}"),
        "algorithm_version": row[6],
        "created_at": row[7],
    }


if __name__ == "__main__":
    # 自测：保存一条 -> 列表 -> 详情 -> 不存在 id
    rid = save_record({
        "job_title": "自测岗位",
        "resume_text": "示例简历",
        "jd_text": "示例 JD",
        "score": 66,
        "result": {"matched_skills": ["Python"], "missing_skills": ["FastAPI"]},
        "algorithm_version": "rule-v1",
    })
    print("saved id:", rid)
    print("list:", json.dumps(list_records(3), ensure_ascii=False))
    got = get_record(rid)
    print("detail score:", got["score"], "| result:", got["result"])
    print("missing id:", get_record("not-exist"))
