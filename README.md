# AI编剧v2.0

用于多分镜长视频 AI 生成的创意提示词增强系统（多 agent 工作流）。

## 运行（Web）

1) 安装依赖

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2) 配置环境变量

```powershell
Copy-Item .env.example .env
```

3) 启动服务

```powershell
uvicorn app.main:app --reload
```

打开：
- `http://127.0.0.1:8000`（简单页面）
- `http://127.0.0.1:8000/docs`（Swagger）
