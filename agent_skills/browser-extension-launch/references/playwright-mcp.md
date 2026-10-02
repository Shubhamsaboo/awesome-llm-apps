# Playwright MCP：真实插件端到端验收

## 必需路径和环境选择

本编排默认必须使用 **Microsoft Playwright MCP** 对实际插件构建做端到端验证。先发现并读取当前可调用工具和服务信息，再核实浏览器、插件加载与原生入口能力。仅有 Playwright npm 包、浏览器截图、普通页面自动化或桥接扩展，不代表此关卡已具备全部能力。

1. 已有 Playwright MCP 且能力足够：沿用已经授权的独立测试环境，准备当前构建和原始操作记录。
2. 缺少服务/浏览器、启动失败、不能加载插件或不能触发必需原生入口：解释具体缺口，询问用户是否安装、启用或修复 Playwright MCP，或采用能够覆盖缺口的受控替代。
3. 等待用户明确选择。可推荐经核实具有扩展操作能力的 Chrome DevTools MCP、其他浏览器 MCP 或受控浏览器，并说明可覆盖的操作与限制。不得静默切换服务、默认使用用户日常浏览器，或改用人工清单来宣告完成。
4. 取得选择后记录实际用户原话、来源和时间，沿用该选择及授权。不得为同一环境内的例行加载、重载和检查反复询问；换服务、换到日常浏览器等超出选择范围的变化需要重新确认。
5. 用户拒绝安装且未选择可用替代时，保持 `blocked` 和未验收状态，可继续不依赖该环境的准备工作。

此说明仅规定后续插件项目的执行方式。更新编排 skill 时不要因此自行启动浏览器、验证历史例子或改动用户现有全局 MCP 服务。

## 已核实的来源

- 维护者：[Microsoft / playwright-mcp](https://github.com/microsoft/playwright-mcp)。核实日期：2026-09-11；源码提交 `8a13ef8e9f7385a0f89477922127f31cbfde9761`。
- 已发布包：`@playwright/mcp@0.0.80`，Apache-2.0，Node.js ≥18。优先复用现有兼容的 Node 20 或更高版本，不另行降级。
- 该版本依赖 `playwright` 和 `playwright-core` 的 `1.63.0-alpha-2026-08-31`。浏览器二进制必须与实际安装的 Playwright 版本匹配；具体安装操作在用户选择准备环境后按该版本官方说明执行。
- 0.0.80 是本次核实的固定参考，不代表对任何宿主都完成了兼容测试。保留已可用的版本；升级前核实差异并记录实际版本。

依据：[固定版本 package.json](https://github.com/microsoft/playwright-mcp/blob/8a13ef8e9f7385a0f89477922127f31cbfde9761/package.json)、[许可证](https://github.com/microsoft/playwright-mcp/blob/8a13ef8e9f7385a0f89477922127f31cbfde9761/LICENSE)。

## 区分服务、库和桥接扩展

| 能力 | 作用 | 验收边界 |
| --- | --- | --- |
| Playwright MCP | AI 通过当前服务的真实工具操作浏览器并观察页面 | 当前官方清单没有通用的“安装任意插件”工具；不能虚构工具名。若某版本提供 `browser_install`，也须读工具说明，它不能据名字被当成插件安装器 |
| Playwright 库 | 使用 Chromium 持久上下文和启动参数加载未打包扩展 | 库脚本不等于 MCP 验收；可用于已授权环境准备或补充验证，不能静默取代默认 MCP |
| Playwright Bridge / Extension | `--extension` 连接已有 Chrome/Edge 页面及其登录状态 | 它是连接器，不是待测插件安装器；连接成功不证明 popup、侧栏或工具栏入口可操作 |

官方扩展测试文档要求使用持久上下文；Chrome/Edge 已移除相关命令行侧载参数，采用此加载方式时应使用 Playwright 随附的 Chromium。Chromium 支持有头或受支持的无头扩展测试，不能写成“任何插件都不支持无头”。本编排优先有头独立环境，以便检查真实入口和收集证据；仍需核实 MCP 是否能够操作具体入口。

依据：[官方扩展测试文档](https://playwright.dev/docs/chrome-extensions)、[Playwright MCP 配置](https://github.com/microsoft/playwright-mcp/blob/8a13ef8e9f7385a0f89477922127f31cbfde9761/README.md)、[官方桥接扩展说明](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md)。

## 实际加载方案

下面是根据官方 MCP `browser.launchOptions` 转发配置与 Playwright 扩展测试文档组合出的配置示意，**本次仅核实文档和来源，未实机验证该组合**。执行者须对实际宿主完成能力预检，不能把配置示意当成功记录。

用户选择准备该环境后，在待测项目中生成专用配置，填入最终解包产物的绝对路径。不要覆盖既有全局服务；优先使用宿主支持的项目级服务或另命名的专用服务，并按宿主真实配置能力执行。配置文件保存于项目记录目录，浏览器 profile 必须独立且不能被并行会话共享。

```json
{
  "browser": {
    "browserName": "chromium",
    "isolated": false,
    "userDataDir": "/ABS/PROJECT/.extension-launch/browser-profile",
    "launchOptions": {
      "channel": "chromium",
      "headless": false,
      "args": [
        "--disable-extensions-except=/ABS/PROJECT/FINAL_UNPACKED_EXTENSION",
        "--load-extension=/ABS/PROJECT/FINAL_UNPACKED_EXTENSION"
      ]
    }
  },
  "saveSession": true,
  "outputDir": "/ABS/PROJECT/.extension-launch/evidence/playwright"
}
```

参考服务启动参数如下。占位路径必须替换，不要原样执行；执行前确认 Node、相匹配的 Chromium、宿主服务重载方式及用户选择均已就绪。

```text
npx -y @playwright/mcp@0.0.80 --config /ABS/PROJECT/playwright-mcp.json
```

这里通过浏览器启动配置加载待测产物，随后通过 MCP 工具执行测试；不声称 MCP 存在专用插件安装工具。不要同时设置 `--extension` 来完成侧载，桥接模式会忽略上述 `browser` 配置。ZIP 须先解压为当前候选目录，并校验指纹；不要拿开发服务器的页面代替实际构建。

加载后必须观察到正确的扩展 ID、版本和当前构建来源。Manifest V3 有 service worker 时，可用实际上下文的 worker URL 辅助确定 ID；没有 worker 的插件应通过真实扩展管理信息取得 ID，不能为了取 ID 改动插件。只声明了参数、浏览器启动成功或打开了空白页都不算安装通过。

## 从真实入口验证完整路径

按 [真实验收契约](acceptance.md) 记录候选 SHA-256，以及至少五个必需场景：`install`、`native_entry`、`primary_flow`、`reopen`、`repeat_use`。最后一项按产品闭环从正常用户路径连续完成两轮，记录继续与退出/恢复，不通过脚本调用内部处理器替代再次操作。

使用当前 MCP 的真实工具逐步执行：加载并核对插件 → 从实际工具栏、原生侧栏、菜单或已定义的命令入口触发 → 完成核心操作 → 观察真实产出 → 关闭并重开适用入口 → 核对状态。保存原始工具结果、截图、导出内容或可复查的其他证据。

MCP 能操作网页不等于能点击浏览器工具栏。直接导航到 `chrome-extension://<id>/popup.html` 可作扩展页面辅助检查，不能替代工具栏 popup 的 `native_entry`。模拟 Chrome API、注入假的 `chrome` 对象、直接调用业务函数或直接写入存储，都不能证明用户完成了真实流程。

遇到原生入口能力不足，返回环境选择步骤。只有已说明且确实无法自动化的原生环节才安排用户辅助操作，并保留 `blocked` 直到取得可核对的真实结果；AI 随后接回受控验证。人工辅助不免除自动化服务、用户选择和核心结果证据。

## 服务选择证据

默认环境记录 `environment.automation_provider: "playwright-mcp"`。用户明确选替代时，服务值限于 `chrome-devtools-mcp`、`browser-mcp` 或 `controlled-browser`，同时提供：

```json
{
  "browser_choice": {
    "default_provider": "playwright-mcp",
    "selected_provider": "chrome-devtools-mcp",
    "reason": "填写实际核实的能力缺口与替代覆盖方式",
    "user_decision": {
      "status": "approved",
      "evidence_path": "browser-choice/user-decision.md"
    }
  }
}
```

这是字段示意，不能预填用户已批准。`selected_provider` 必须与实际环境一致；选择证据必须是验收 JSON 同目录范围内的非空原始记录，保留用户实际选择及可追溯来源，不能是 AI 写出的同意，也不能指向验收 JSON 本身。

场景方式仍使用 `real_browser_tool` 或有真实见证记录的 `witnessed_manual`。人工辅助不是第四种服务，也不是绕过选择记录的办法。任何必需场景失败、未测、候选哈希变化或门禁拒绝，都不能宣布验收完成。
