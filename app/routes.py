from fastapi import APIRouter

from schemas.inputs import GenerateRequest
from schemas.outputs import GenerateResponse
from workflows.pipeline import run_workflow


router = APIRouter(prefix="/api")


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    result = run_workflow(req.text)
    return GenerateResponse(**result)
