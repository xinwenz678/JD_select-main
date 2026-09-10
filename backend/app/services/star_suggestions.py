import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.services.jd_parser import parse_jd


NOTICE = "建议稿仅供参考；请核实并补充真实事实与数字后再采用。"


def _rule_fallback(experience: str, jd_text: str) -> dict:
    original = experience.strip()
    jd = parse_jd(jd_text.strip())
    keywords = list(jd.get("all_skills", []))[:6]
    first_sentence = re.split(r"[。！？\n]", original)[0].strip() or original
    keyword_text = "、".join(keywords) if keywords else "岗位相关能力"
    parts = {
        "situation": f"说明项目/岗位背景，以及需要解决的具体问题（基于原文：{first_sentence}）。",
        "task": "明确你本人承担的目标、职责和交付边界。",
        "action": f"按真实过程说明采取的行动；若确实使用过，可突出 {keyword_text}。",
        "result": "补充可核实的结果，例如数量、耗时、准确率、效率或业务影响；没有数据时不要编造。",
    }
    return {
        "original": original, "star": parts, "optimized_draft": " ".join(parts.values()),
        "jd_keywords": keywords,
        "metric_prompts": ["处理规模（条/人/请求量）", "效率变化（时间或百分比）", "质量变化（准确率/缺陷数）"],
        "source": "rule-fallback",
    }


def _extract_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("模型响应不是 JSON 对象")
    return value


def _request_llm(experience: str, jd_text: str, settings: Settings) -> dict:
    """调用 OpenAI 兼容 chat/completions；异常由上层统一降级。"""
    endpoint = settings.llm_base_url.rstrip("/") + "/chat/completions"
    prompt = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是简历写作助手。只能使用用户提供的真实事实，不得补造数字、职责或技能。"
                    "返回 JSON，字段必须为 star（含 situation/task/action/result 四个非空字符串）、"
                    "optimized_draft、jd_keywords（字符串数组）、metric_prompts（字符串数组）。"
                ),
            },
            {
                "role": "user",
                "content": f"经历原文：\n{experience}\n\n岗位 JD：\n{jd_text}",
            },
        ],
    }
    request = Request(
        endpoint,
        data=json.dumps(prompt, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    value = _extract_json(content)
    star = value.get("star")
    if not isinstance(star, dict) or any(not isinstance(star.get(key), str) or not star[key].strip() for key in ("situation", "task", "action", "result")):
        raise ValueError("模型 STAR 字段不完整")
    optimized = value.get("optimized_draft")
    if not isinstance(optimized, str) or not optimized.strip():
        optimized = " ".join(star[key].strip() for key in ("situation", "task", "action", "result"))
    keywords = value.get("jd_keywords", [])
    prompts = value.get("metric_prompts", [])
    if not isinstance(keywords, list) or not all(isinstance(item, str) for item in keywords):
        raise ValueError("模型关键词格式错误")
    if not isinstance(prompts, list) or not all(isinstance(item, str) for item in prompts):
        raise ValueError("模型量化提示格式错误")
    return {
        "original": experience.strip(),
        "star": {key: star[key].strip() for key in ("situation", "task", "action", "result")},
        "optimized_draft": optimized.strip(),
        "jd_keywords": [item.strip() for item in keywords if item.strip()][:10],
        "metric_prompts": [item.strip() for item in prompts if item.strip()][:10],
        "source": "llm",
        "notice": NOTICE,
    }


def build_star_suggestion(experience: str, jd_text: str, settings: Settings | None = None) -> dict:
    """优先使用已配置的兼容模型；无配置、超时或响应异常时稳定回退本地规则。"""
    fallback = _rule_fallback(experience, jd_text)
    fallback["notice"] = NOTICE
    if not settings or not all((settings.llm_api_key, settings.llm_base_url, settings.llm_model)):
        return fallback
    try:
        return _request_llm(experience.strip(), jd_text.strip(), settings)
    except (HTTPError, URLError, TimeoutError, OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return fallback
