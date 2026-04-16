from fastapi import APIRouter, HTTPException

from schemas.inputs import GenerateRequest
from schemas.outputs import GenerateResponse
from workflows.pipeline import run_workflow
from app.settings import get_settings
from llm.client import LLMClient
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api")


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    result = run_workflow(req.text)
    return GenerateResponse(**result)


class LLMTestRequest(BaseModel):
    text: str = Field(..., description="要发送给 LLM 的用户消息")
    system: str | None = Field(default=None, description="可选 system 提示词")


class LLMTestResponse(BaseModel):
    model: str | None
    text: str
    raw: dict


@router.post("/llm/test", response_model=LLMTestResponse)
def llm_test(req: LLMTestRequest) -> LLMTestResponse:
    s = get_settings()
    if not s.llm_relay_base_url:
        raise HTTPException(status_code=400, detail="LLM_RELAY_BASE_URL is empty")
    client = LLMClient.build(
        base_url=s.llm_relay_base_url,
        api_key=s.llm_relay_api_key,
        model=s.llm_model,
        timeout_s=60.0,
    )
    try:
        resp = client.chat(req.text, system=req.system)
        return LLMTestResponse(model=client.default_model, text=resp.text, raw=resp.raw or {})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Relay call failed: {e}") from e
