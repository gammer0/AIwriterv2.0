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
          input[type="text"], input[type="number"]{padding:8px;font-size:14px}
          button{padding:10px 14px;font-size:14px;cursor:pointer}
          pre{white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:8px}
          .row{display:flex;gap:12px;align-items:center}
          .row2{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
          .muted{color:#666;font-size:13px}
        </style>
      </head>
      <body>
        <h1>AI编剧 v2.0</h1>
        <p>将创意文本经多 agent 工作流生成“剧本文本 + 多分镜提示词 YAML”。</p>
        <div>
          <label for="t">输入文本</label>
          <textarea id="t" placeholder="粘贴你的创意文本..."></textarea>
        </div>
        <div class="row2" style="margin-top:12px">
          <label>迭代次数
            <input id="iters" type="number" min="1" max="10" value="2" />
          </label>
          <button onclick="run()">生成</button>
          <button id="btnDownload" onclick="downloadYaml()" disabled>下载 YAML</button>
        </div>
        <p class="muted" id="status"></p>

        <h3>剧本（最终文本）</h3>
        <textarea id="script" readonly placeholder="生成后显示最终剧本文本..."></textarea>

        <h3>YAML（多分镜提示词）</h3>
        <pre id="yaml" style="min-height:120px"></pre>

        <h3>调试输出</h3>
        <pre id="out"></pre>
        <script>
          let lastYaml = '';

          async function run(){
            const text = document.getElementById('t').value || '';
            const iterations = Number(document.getElementById('iters').value || 1);

            document.getElementById('status').textContent = '生成中...';
            document.getElementById('btnDownload').disabled = true;
            document.getElementById('script').value = '';
            document.getElementById('yaml').textContent = '';
            lastYaml = '';

            const res = await fetch('/api/generate', {
              method:'POST',
              headers:{'Content-Type':'application/json'},
              body: JSON.stringify({
                text,
                iterations: Number.isFinite(iterations) ? iterations : 1
              })
            });
            const data = await res.json().catch(() => ({}));

            if(!res.ok){
              document.getElementById('status').textContent = '生成失败：' + (data.detail || res.status);
              document.getElementById('out').textContent = JSON.stringify(data, null, 2);
              return;
            }

            const loop = (((data || {}).meta || {}).agents || {}).creative_loop || {};
            const finalText = loop.final_text || '';
            document.getElementById('script').value = finalText;

            const agents = (((data || {}).meta || {}).agents || {});
            const yaml = agents.storyboard_yaml || '';
            lastYaml = yaml;
            document.getElementById('yaml').textContent = yaml;
            document.getElementById('btnDownload').disabled = !yaml;
            document.getElementById('status').textContent = '完成。';

            document.getElementById('out').textContent = JSON.stringify(data, null, 2);
          }

          function downloadYaml(){
            if(!lastYaml) return;
            const filename = 'storyboard.yaml';
            const blob = new Blob([lastYaml], {type: 'application/x-yaml;charset=utf-8'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
          }
        </script>
      </body>
    </html>
    """
