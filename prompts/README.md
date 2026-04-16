本目录用于存放各 agent 的「任务定义提示词」文件（角色/任务描述/任务技巧/输入描述/输出描述/输出格式）。

约定：
- 若文件内包含 `BEGIN_SYSTEM_PROMPT` / `END_SYSTEM_PROMPT`，程序会读取其中内容作为 system prompt。
- 为保证可解析性，相关 agent 会要求模型只输出一个 JSON 对象（不输出 Markdown/代码块/解释文字）。
