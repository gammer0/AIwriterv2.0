from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.routes import router


app = FastAPI(title="AI编剧v2.0", version="0.1.0")
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>AI编剧v2.0</title>
        <style>
          body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;
               margin:40px;max-width:900px;line-height:1.6}
          textarea{width:100%;min-height:180px;padding:12px;font-size:14px}
          button{padding:10px 14px;font-size:14px;cursor:pointer}
          pre{white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:8px}
          .row{display:flex;gap:12px;align-items:center}
        </style>
      </head>
      <body>
        <h1>AI编剧 v2.0</h1>
        <p>Web 入口：将创意文本经多 agent 工作流生成多分镜提示词（当前为骨架实现）。</p>
        <div>
          <label for="t">输入文本</label>
          <textarea id="t" placeholder="粘贴你的创意文本..."></textarea>
        </div>
        <div class="row" style="margin-top:12px">
          <button onclick="run()">生成</button>
          <a href="/docs">API 文档</a>
        </div>
        <h3>输出</h3>
        <pre id="out"></pre>
        <script>
          async function run(){
            const text = document.getElementById('t').value || '';
            const res = await fetch('/api/generate', {
              method:'POST',
              headers:{'Content-Type':'application/json'},
              body: JSON.stringify({ text })
            });
            const data = await res.json();
            document.getElementById('out').textContent = JSON.stringify(data, null, 2);
          }
        </script>
      </body>
    </html>
    """
