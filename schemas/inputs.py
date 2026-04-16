from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text: str = Field(default="", description="用户输入的创意文本/长文本")
