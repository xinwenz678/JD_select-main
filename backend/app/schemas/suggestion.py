from typing import Literal
from pydantic import BaseModel, Field, field_validator

class StarSuggestionRequest(BaseModel):
    experience: str = Field(..., min_length=1, max_length=10_000)
    jd_text: str = Field(..., min_length=1, max_length=50_000)

    @field_validator("experience", "jd_text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("内容不能为空")
        return value

class StarParts(BaseModel):
    situation: str
    task: str
    action: str
    result: str

class StarSuggestionResponse(BaseModel):
    original: str
    star: StarParts
    optimized_draft: str
    jd_keywords: list[str]
    metric_prompts: list[str]
    source: Literal["rule-fallback", "llm"] = "rule-fallback"
    notice: str = "建议稿仅供参考；请核实并补充真实事实与数字后再采用。"