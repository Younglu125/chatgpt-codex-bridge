# ChatGPT Codex Bridge · CCB

**继续用 Codex 干活，在值得讨论的地方，让普通 ChatGPT 加入。**

[English](README.md) | 简体中文

[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![预览版](https://img.shields.io/badge/status-preview-orange.svg)](VALIDATION.md)

CCB 是独立社区 Codex 插件：普通 ChatGPT 按需参与重要分析、决策和独立复核，
Codex 负责本地修改和测试。使用你自己的账号，无需 OpenAI API Key，不调用 ChatGPT Work。

## 项目背景：为什么做这个

在 Codex 中读代码、改文件和运行测试很方便；讨论复杂方案或独立复核时，
也希望让自己日常使用的普通 ChatGPT 参与。手动在两个会话之间复制材料、说明项目背景、
追踪回复和把结论带回工作区，容易遗漏上下文，也会打断执行节奏。

CCB 的目的不是替换 Codex，也不是每一步都再调用一个模型，而是把这段交接组织起来：
用简单的会话开关选择协作，在有价值的分析与复核节点提供必要证据，再由 Codex 继续执行。
同时探索减少部分 Codex 分析负担的可能性；这不等于已验证节省额度或缩短总耗时，
ChatGPT 分析本身可能需要较长等待。

本项目是社区方案的整合与扩展，不是所有底层能力从零自研。具体来源和贡献边界见下节。

## 借鉴、集成与致谢

感谢 [XiaoDuoYa/codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt)。
它是 CCB Full 模式的直接上游：本仓库内置其锁定版本，复用只读工作区 MCP、
OAuth/配对、隧道及执行证据等能力，不需要同事另外克隆上游仓库。

| 来源 | CCB 如何使用 | 贡献边界 |
|---|---|---|
| `codex-with-chatgpt`（MIT） | 内置并调用锁定源码；提交与校验清单见 [UPSTREAM.json](UPSTREAM.json) | Full 后端是上游成果，不作为 CCB 原创 |
| OpenAI Codex 插件规范及官方 plugin-creator 辅助工具 | 用于插件封装和便捷安装；见[官方说明](https://developers.openai.com/plugins/build/plugins) | 属于宿主平台能力和安装依赖，不是 CCB 自研聊天服务 |
| CCB 集成层 | 会话级按需协作、Lite 快照、项目与聊天绑定、交接记录与恢复、插件打包及隐私检查 | 本项目在上述能力上增加的工作流与工具 |

当前直接内置的第三方项目是上述 `codex-with-chatgpt`，不是多个仓库代码的无差别拼装。
保留其源码、MIT 许可证和作者归属；更多依赖以各自清单及许可证为准。
详见 [第三方声明](THIRD_PARTY_NOTICES.md)。不表示上游作者或 OpenAI 对本项目背书。

## 怎么用

| 你说的话 | 工具如何处理 |
|---|---|
| 修复这个小问题 | 默认 Codex 直接处理 |
| CCB，帮我分析重构方案 | 开启当前会话协作，咨询 ChatGPT |
| 按方案实现并测试 | Codex 执行，不必重复 CCB |
| 重新考虑架构取舍 | 根据价值与等待成本，考虑再次咨询 ChatGPT |
| 这一步你自己做 | 本次 Codex 完成，协作开关保留 |
| 这次必须让 GPT 帮忙 | 本次明确调用，不可用时如实说明 |
| 退出 CCB | 恢复 Codex 直接处理 |

支持有意使用 `CCB`、`ccb`、`$CCB`、`$ccb` 开启协作，阶段词不是必填。
后续继承会话偏好；新会话默认关闭；引用、代码、否定表达和维护插件不算开启。

这是 **Skill 驱动的工作流**，不是全局消息拦截器。Codex 理解意图后调用状态程序。
简写没有注册名为 CCB 的独立技能；客户端不能解析时，使用完整的
`$chatgpt-codex-bridge`。不能承诺每个客户端都识别所有自然语言表达。

## 为什么使用 CCB

- 按需交接：查询状态、改文件、跑测试和明确的小修复留给 Codex。
- Lite 冻结快照和 Full 实时只读工作区两条路径。
- 按项目保存任务和真实回复，支持中断恢复、避免重复发送。
- 会话开关、项目路径和 ChatGPT 目标分别管理。
- Full 必须真实读取正确工作区和文件，不能把服务启动当成连通。
- 发布包不包含个人凭据和运行状态。

**净 token 节省、额度归属和速度提升尚未量化。**
一次交接会增加等待，应在分析价值高于成本时使用。

## Lite 与 Full

| 模式 | ChatGPT 看到什么 | 条件 |
|---|---|---|
| Lite / prompt | 问题文字 | Python 3.12+、Codex、普通 ChatGPT、原生或浏览器收发工具 |
| Lite / snapshot | 少量经过筛选的冻结文件 | Lite 条件及分享文件的授权 |
| Full / live | 按需文件读取、搜索、Git diff、已记录的执行结果 | 另需 Node.js 20+/npm、cloudflared、自定义 MCP/OAuth 授权 |

还有可选冻结快照 MCP，需 Python MCP 依赖和独立 HTTPS/OAuth 配置。
Full 使用锁定的 [codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt) 后端；
CCB 增加打包、证据交接和按需会话协调，保留上游源码和许可。
详见 [第三方声明](THIRD_PARTY_NOTICES.md)。

原生工具或浏览器负责消息收发，MCP 负责文件访问。聊天收发成功不等于 Full 已验证。
健康的项目连接直接复用。

## 安装

**0.2.9 预览版。** macOS 已做本机验收；Linux/WSL2 是兼容目标，尚需独立验收。
CCB 的 POSIX 快照与锁实现不支持原生 Windows。

克隆本仓库（需要访问权限），或将发布包解压到长期保留的目录。
更新前检查现有改动，使用 `git pull --ff-only`，分叉时正常解决冲突。

### 给同事：完整程序包还是 GitHub？

两者是同一套程序的不同分发方式，**完整程序包不等于 Full 已配置好**。
包内包含 Lite 和 Full 所需源码及锁定的上游代码，但不是携带全部依赖的离线安装器，
不包含账号、授权、隧道运行状态或预装依赖。每个人仍须使用自己的账号并完成本机验证。

- **首次少量同事试用：**可直接提供经检查的发布 ZIP，适合没有仓库权限或不常用 Git 的人。
  解压根目录有 `INSTALL.md`；实际插件源码在 `plugins/chatgpt-codex-bridge/`。
- **持续使用或参与维护：**推荐从 GitHub 克隆，便于查看版本、更新和提交问题。
  私有仓库必须先获得访问权限；拿到链接不等于可以下载。本仓库的源码 ZIP 与
  `scripts/release.py` 生成的 marketplace ZIP 结构不同，不要混用目录说明。

GitHub 首次安装（目标目录已存在时先检查，不覆盖、不重新初始化 Git）：

```bash
git clone https://github.com/Younglu125/chatgpt-codex-bridge.git
cd chatgpt-codex-bridge
```

以下命令在插件源码根目录执行。使用发布 ZIP 时，先进入其
`plugins/chatgpt-codex-bridge/`，不是最外层目录。

```bash
python3 --version                         # 需要 3.12+
python3 scripts/install_plugin.py         # 首次 Lite；更新保留已有 Full
python3 scripts/install_plugin.py --mode full  # 需要 Full 时
```

便捷安装器需要 PATH 中有 Codex CLI，并存在官方 plugin-creator 辅助脚本。
不满足时，使用发布 ZIP 内的 marketplace：
`codex plugin marketplace add <解压目录>`，再从该 marketplace 安装 CCB。
参见 [官方插件说明](https://developers.openai.com/plugins/build/plugins)。

**安装或更新后新开 Codex 任务。** 在实际项目中说：

> CCB，分析这个项目并建议下一步。

Full 首次由 Skill 识别 checkout、配置项目服务、引导连接器和 OAuth。
你处理必要登录、验证码、双重验证和授权。每个项目/每台 Mac 独立配置并真实验证文件读取。
临时隧道重启可能换地址，固定域名可选。不要复制其他机器的凭据和运行状态。

验收分两步：先真实发送一次分析请求并读回完整回复，再对需要 Full 的项目验证连接器
实际读取正确工作区和文件。仅安装成功、服务启动或看到连接器名称均不代表 Full 连通。
日常 Git 更新使用 `git status` → `git pull --ff-only` → 安装脚本 → 新开任务；
有本地改动或分叉时先保留并处理。曾使用历史清理前版本的维护者另见
[一次性历史迁移说明](OTHER_MAC_UPDATE.zh-CN.md)，不能直接合并旧历史。

## 日常恢复

```bash
python3 scripts/doctor.py
python3 bridge.py auto-project --root .
python3 bridge.py pending --project PROJECT
python3 scripts/route.py --project PROJECT --scope repository
python3 scripts/session.py --thread CODEX_CONVERSATION_ID
python3 scripts/full.py --project PROJECT -- status --json
```

Full 只读；修改由 Codex 根据授权执行。只要求分析就停在分析。
复核集中在重要阶段，不必每次编辑或测试都转交。明确要求 GPT 时优先遵从。

## 隐私与分享

运行状态位于 `~/.local/share/chatgpt-codex-bridge` 或 `BRIDGE_STATE_DIR`，
不随插件发布。不要分享该目录、日志、配对码、凭据或个人聊天链接。

Lite 会把选中文件发给 ChatGPT；Full 也会把实际读取的内容发给 ChatGPT。
**只读不代表数据不离开本机。** 过滤脱敏不是绝对保证，应检查分享范围。

```bash
python3 scripts/audit_share.py . --tracked --history
python3 scripts/release.py --output release
```

扫描器报告常见敏感类型，不输出匹配值；图片需目检，Git 历史需单独检查。
发布包没有 .git，不代表旧提交作者信息已删除。
详见 [分享审查](SHARING_REVIEW.md)、[发布清单](RELEASE.md)、[验收记录](VALIDATION.md)。

## 使用效果与开发

[演示截图及 X 文案](marketing/README.md) 来自真实本地程序输出，
明确标记为 CLI 演示，不伪装成 ChatGPT 对话或新一轮 Full 验证。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest==9.1.1 mcp==1.30.0
.venv/bin/python -m pytest -q
```

先测试再提交，上游只做显式升级。另一台机器更新前保留改动，拉取安装后新开任务。

[详细操作](USAGE.zh-CN.md) · [工作流](WORKFLOW.md)

MIT 许可。独立社区项目，不是 OpenAI 官方产品。
