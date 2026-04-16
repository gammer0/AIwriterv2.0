from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text: str = Field(default="", description="用户输入的创意文本/长文本")
    iterations: int = Field(default=1, ge=1, le=10, description="创作-优化迭代次数（>=1）")
