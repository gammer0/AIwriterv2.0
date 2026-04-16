from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text: str = Field(default="", description="用户输入的创意文本/长文本")
    iterations: int = Field(default=1, ge=1, le=10, description="创作-优化迭代次数（>=1）")
    yaml_out: str | None = Field(default="../storyboard.yaml", description="可选：将 storyboard YAML 写入该相对路径（如 outputs/storyboard.yaml）")
