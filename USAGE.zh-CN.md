# 使用与分享说明

这是一个可安装插件，内含 Skill、本地交接程序和可选的只读工作区 MCP。
它把分析与复核交给普通 ChatGPT，Codex 负责当前项目的修改、测试与交付。
发布状态：0.2.7 候选版。当前验收证据见 VALIDATION.md，不能把未验证的平台/账号写成已支持。

## 自动选择：优先复用

你不需要每次决定 Lite 还是 Full。Skill 会识别当前 Codex checkout，检查这个项目自己的
连接状态，并按任务范围自动选择：

- 已经授权且健康的 Full 一律直接复用，不再新建连接器、Tunnel、ChatGPT 项目或聊天。
- 需要理解系统、搜索依赖、遍历仓库、检查 diff 或测试记录时，优先使用 Full。
- 只涉及少量已知文件而 Full 尚不可用时，自动使用 Lite 冻结快照，不要求你先配置 MCP。
- 完全不依赖本地文件时，只发送问题。

快照是 Codex 先选出一小组文件，把当时内容冻结后交给 ChatGPT；内容稳定、依赖少，但
ChatGPT 看不到未选文件，也不能自行追查。Full 是 ChatGPT 通过只读 MCP 自己列目录、搜索并
按需读当前文件；更适合仓库级分析和实施后的独立复核。两者不是谁永远更强：仓库级任务
Full 更好，边界明确的小任务快照更简单。

路由器同时检查授权令牌和已保存的验证会话；只有本地服务、Tunnel 或 OAuth 正常，但尚未
从 ChatGPT 实际通过 `workspace_info` 和文件读取验证的项目，不会被误判为“Full 已连接”。

## Lite 的必要条件

必要条件：Python 3.12+、能执行本地工具的 Codex、自己的普通 ChatGPT 聊天，以及原生会话工具或可操作的已登录浏览器。
当前验证平台为 macOS；Linux/WSL2 是兼容目标，尚需各自验收；原生 Windows 未支持。
Lite 无需 Node、MCP、Tunnel、开发者模式或 API Key。

安装后新开 Codex 任务，首次绑定自己现有的普通聊天。可以按项目分别绑定，也可串行复用同一个聊天。
绑定需要核对「聊天」模式和界面模型。以后直接说：

> 使用 $chatgpt-codex-bridge。在本项目下，让普通 ChatGPT 分析【问题】，收回方案后由你实施并测试。

工作区自动取当前 Codex 项目/check­out，包括 worktree。同名项目以真实路径区分。
不需要本地文件时发纯问题；需要少量源码时发明确范围的冻结快照。
快照会把选中的文本发给 ChatGPT，因此发布插件本身去个人化，不等于任务数据不会出机。
切换 ChatGPT 账号后，旧账号会话不会继续假装可用。Skill 会在当前账号选择一个已有空闲聊天，
通过一次真实收发自动重绑；如果原生工具看不到模型和「聊天/工作」模式，就明确保存为未知，
不会要求用户重复建同名聊天，也不会伪造模型信息。

## 完整版 Full：默认无需域名

在 Lite 基础上增加 Node.js 20+/npm、cloudflared，以及普通 ChatGPT 可用的自定义 MCP/OAuth 连接。
Full 直接使用仓库中原样锁定的 GitHub 上游实现，不修改它的 MCP、OAuth、Tunnel、配对、
诊断、修复和会话管理逻辑。安装依赖并登记当前项目后，按上游顺序运行
`full.py --project PROJECT -- sandbox-allow --json` 和
`full.py --project PROJECT -- setup --json`。前者会按上游设计修改 Codex 的沙箱允许目录；
后者启动只读服务、创建默认 Quick Tunnel 并生成配对码。无需 Cloudflare 账号、个人域名或
OpenAI API Key。用户在 ChatGPT 添加返回的 OAuth 连接并输入配对码。每个项目独立认证，
读到的工作区必须与 Codex 实施目录一致。

Full 能按需读实时文件、检索代码、检查 Git diff、读取 Codex 实际测试输出。
消息仍可走原生会话；原生不可用时用浏览器。MCP 本身不负责发送问题或读取聊天回复。
流程：计划 → Codex 实施/测试 → 保存真实记录 → ChatGPT 独立复核 → 必要时修复，最多三轮。
Full 不需要 OpenAI Platform API Key，但账号需要具备并允许相应的 MCP 功能；插件不能替账号开通权限。
本地服务通过、网页显示已连接，都不等于远端验收完成；必须实际读到正确项目内容。
首次完成授权和真实文件读取后，后续直接复用。只有登录、验证码、双重验证或 OAuth 同意
这类平台明确要求账号本人完成的步骤才交给用户；本地安装、启动、诊断和恢复由 Skill 自动处理。

## 长期使用

- 超时保留任务，后续通过 pending 继续；发送结果不明确时先查原聊天，避免重复派单。
- 当前版本锁定上游提交和依赖，70 个上游跟踪文件保持逐字节一致。更新是显式操作，保留旧版和外置状态以便回滚。
- 临时 Tunnel 地址可能在重启后变化；届时只修复该项目的 ChatGPT 连接器。固定域名是高级可选项，不是完整功能前置条件。
- 不将 ChatGPT Work 当作普通 Chat，也不承诺固定额度节省比例。
- 登录、验证码和授权交给账号所有者完成，不保存其密码或复制浏览器登录状态。

## 两台 Mac 安装与更新

把 GitHub 仓库作为唯一的版本来源；每台 Mac 分别克隆到**不受群晖等文件同步软件管理**的目录。
不要在两台 Mac 间同步 `.git`、插件缓存、`~/.local/share/chatgpt-codex-bridge` 或浏览器登录状态。
首次安装，在各自克隆目录执行：

```bash
python3 scripts/setup.py --mode lite
python3 scripts/install_plugin.py
codex plugin list
```

需要 Full 的 Mac 首次安装时把第二条改为 `python3 scripts/install_plugin.py --mode full`；
以后默认的 `auto` 会保留已有 Full 构建。切换到 Lite 必须明确加 `--mode lite`。

以后在任一 Mac 修改功能：先在该机运行相关测试，提交并推送 Git；另一台 Mac 在自己的克隆
目录先确认没有未提交改动，再执行 `git pull --ff-only` 和 `python3 scripts/install_plugin.py`。
安装后新开 Codex 任务，旧任务可能仍持有旧版 Skill 上下文。两台 Mac 同时修改时，先分别提交，
用正常的 Git 合并或变基处理冲突；不要让文件同步软件替 Git 合并源码。

`codex plugin list` 只能确认本机插件已安装，不能证明普通 ChatGPT 发送、回复或 Full MCP 已连接。
首次在第二台 Mac 使用时，还需绑定该机可用的聊天并做一次真实收发验证；Full 的本地依赖、
连接器和账号授权也要在第二台 Mac 分别配置与验证。首次未验收前不要宣称跨机已跑通。

## 分享给同事或发到 X

分享 release 里的 ZIP、校验文件、README 和本页；不要分享本机状态目录、对话验收记录或密钥。
ZIP 内已有仓库 marketplace，可供同事本地添加；开发源码也可放在私有 GitHub 仓库协作。
安装者需要自己的账号与聊天，一次配置后即可使用。不要复制作者的聊天链接作为默认目标。
在不同机器完成实际安装/派单/收回/实施验收之后，再扩大支持平台。
当前没有自动公开发布到 GitHub/X，也没有提交公共插件目录。

建议对外描述：普通 ChatGPT 做分析和审查，Codex 做本地实施与验证；提供低依赖 Lite 和可选实时只读 MCP。
不要宣传“额外获得固定百分比 Token”“所有平台开箱即用”或“零依赖”。
