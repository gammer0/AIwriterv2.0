# AI编剧 v2.0

多 agent 工作流：把用户创意文本转成“最终剧本文本 + 多分镜提示词 YAML”，提供 Web 页面与 API。

## 功能概览

- Web 页面：输入文本 → 输出最终剧本文本 → 一键下载 `storyboard.yaml`
- API：`POST /api/generate` 返回结构化分镜 + YAML 字符串
- 可选对接中转 LLM：通过 `.env` 配置 `LLM_RELAY_BASE_URL/LLM_RELAY_API_KEY/LLM_MODEL`

## 本地运行（Windows / PowerShell）

```powershell
pip install -r requirements.txt

Copy-Item .env.example .env
uvicorn app.main:app --reload
```

打开：`http://127.0.0.1:8000/`


## API

### `POST /api/generate`

请求 JSON：

```json
{
  "text": "你的创意文本",
  "iterations": 2
}
```

响应要点：
- `meta.agents.creative_loop.final_text`：最终剧本文本
- `meta.agents.storyboard_yaml`：可下载的 YAML 字符串


## 脚本一键生成结果

直接在项目根目录运行（会写出 `storyboard.yaml`）：

```powershell
python scripts\\generate_result.py --text "你的创意文本" --iterations 2 --yaml-out storyboard.yaml
```
## Docker 运行

### 方式一：docker build/run

```bash
docker build -t ai-bianju:v2 .
docker run --rm -p 8000:8000 --env-file .env ai-bianju:v2
```

打开：`http://127.0.0.1:8000/`

### 方式二：docker compose

```bash
docker compose up --build
```

## 环境变量（.env）

从 `.env.example` 复制一份 `.env` 后修改：

- `LLM_RELAY_BASE_URL`：中转 API 基地址（如 `https://example.com/v1`）
- `LLM_RELAY_API_KEY`：密钥
- `LLM_MODEL`：模型名（支持带引号）
- `DISABLE_LLM`：`1`/`true` 则禁用真实 LLM 调用（离线 fallback），默认 `0`
