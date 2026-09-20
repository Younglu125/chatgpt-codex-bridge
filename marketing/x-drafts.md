# X drafts / X 文案草稿

Status: prepared for review, not posted. Add the repository URL only after public access is ready.
The two attached images are real local CLI demonstration reports, not GPT chat screenshots.

## 中文短帖

CCB：默认 Codex 干活，说一句「CCB」，让普通 ChatGPT 按需参与方案讨论与复核。编辑、测试仍由 Codex 完成。

Lite 快照 / Full 只读 MCP，无需 API Key。预览版，节省量未测。配图为本地 CLI 实测。

## 中文串帖（逐条发布，发布前检查账号字数限制）

1/ 我想让普通 ChatGPT 参与 Codex 工作，但不想每一步都增加一次等待。
所以做了 CCB：新会话默认 Codex；说一次 CCB，开启当前会话的按需协作。

2/ 开启后，Codex 仍负责编辑和测试。讨论复杂方案、调整重大决策、需要独立复核时，再请 ChatGPT 加入。
也可以说「这次必须让 GPT 帮忙」「这一步你自己做」或「退出 CCB」。

3/ Lite 发送少量选定文件的冻结快照；Full 通过只读 MCP 按需读工作区。
消息收发可以走原生接口或浏览器。只读不代表数据不出机，选中文件内容仍会进入你授权的 ChatGPT。

4/ Full 复用了 codex-with-chatgpt 的锁定后端；CCB 增加会话开关、项目证据交接、恢复和插件打包。
没有 API Key，也不承诺固定比例的 token 节省。交接有成本，整体效率优先。

5/ 当前是预览版：macOS 已验收，其他平台覆盖仍有限。中英文文档、源码、发布检查和真实本地演示已准备好。
配图展示参与选择与会话隔离，不是伪造的 ChatGPT 对话。仓库开放后补链接。

## English short post

CCB keeps routine work with Codex and brings ordinary ChatGPT into planning, big decisions and review when useful. Say CCB once to enable collaboration for a conversation. Lite snapshots or read-only MCP; no API key. Preview; savings unmeasured. Images: local CLI demo.

## Suggested alt text

Image 1: Real local CCB helper output: collaboration enabled, substantial analysis selects ChatGPT,
routine tests select Codex, explicit GPT request selects ChatGPT. No messages dispatched.

Image 2: Real local helper output: session A remains enabled during a local override; session B
defaults off; a later review in A selects ChatGPT; exiting A restores Codex. No messages dispatched.
