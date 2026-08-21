![Outlook 批量收件台](docs/images/social-preview.png)

# Outlook 批量收件台

中文 · [English](README_EN.md)

[![CI](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/ci.yml/badge.svg)](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/codeql.yml/badge.svg)](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/codeql.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-315b70?logo=python&logoColor=white)](https://www.python.org/)
[![零依赖](https://img.shields.io/badge/%E8%BF%90%E8%A1%8C%E4%BE%9D%E8%B5%96-0-2f7d68)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/License-MIT-e57958.svg)](LICENSE)

> 一次查看最多 50 个 Outlook 邮箱的最新邮件和验证码。只用 OAuth，不要密码。

## 为什么会需要它

如果你手上有一批 Microsoft 邮箱（测试账号、注册用的小号、团队共用的功能邮箱），要从里面拿验证码，一个个登录网页版是一件很消耗人的事：登录、等加载、找信、复制、退出、下一个。

这个工具把这件事变成一次操作：一批账号一起读，最近的邮件和识别出来的验证码列在同一个页面上。

它**只接受 OAuth2 授权，不接受邮箱密码**；凭据只在这一次请求的内存里用，用完就没了。界面上账号默认脱敏、邮件详情默认遮挡——因为一屏几十个真实邮箱地址本身就是风险。

[部署指南](docs/部署指南.md) · [安全模型](docs/安全模型.md) · [发布审计](docs/发布审计.md) · [报告问题](https://github.com/ferretgeek/outlook-batch-inbox/issues)

## 界面

![工作台](docs/images/dashboard.png)

![入口与隐私边界设计](docs/images/intro.png)

## 它能做什么

- **批量读取** — 单次最多 50 个邮箱，受控并发兼顾速度和稳定。
- **只用现代认证** — 仅 Microsoft OAuth2 / XOAUTH2，**不接受邮箱密码**。
- **凭据不落地** — 账号与令牌只在本次请求的内存中使用，不写磁盘、不进日志。
- **读取范围克制** — 固定连接 Microsoft 官方主机，只读收件箱，并限制邮件数量、大小和超时。
- **默认遮罩** — 账号默认脱敏、邮件详情默认遮挡；最小化导出不含发件人、主题、正文或验证码值。
- **界面能用** — 晴空、青玉、暮霞三套浅色主题与深灰暗色，桌面和手机都是完整可用。
- **两种部署** — 本机一条命令启动；服务器推荐回环监听 + SSH 隧道，也支持带访问密钥的 HTTPS 反代。

## 本地启动

需要 Python 3.10 或更高版本，**没有第三方运行依赖**。

```powershell
python -m inbox_harbor
```

打开 `http://127.0.0.1:4174`。可以先点"打开合成演示"——它不连接任何邮箱，纯看界面。

账号一行一条，四段用 `----` 分隔：

```text
lina@example.com----12345678-1234-4234-9234-1234567890ab----REPLACE_WITH_REFRESH_TOKEN----consumers
```

依次是邮箱、Microsoft Entra 应用 `client_id`、`refresh_token`，以及可选的 `tenant`。**项目不接收密码**；上面示例全部是合成占位数据。

获取 OAuth 凭据的完整步骤见[认证准备](docs/认证准备.md)。

## 技术上值得一提的地方

**这个项目是重做过的，原因值得说清楚。** 最早的私人脚本会先尝试密码登录、允许连接任意邮箱主机，并且可能把邮件正文或上游错误直接写进终端和 JSON 文件。作为私人脚本尚可，作为公开项目不行。所以重做时做了四件事：**网络目的地固定为 Microsoft、彻底取消密码路径、收紧重试与工作量边界、把界面 / 部署 / 验证补成能长期维护的成品。**

**目的地是写死的。** 只连 `outlook.office365.com:993`，走 TLS 和 XOAUTH2。一个能拿着你的 refresh token 去连接任意主机的工具，本身就是钓鱼工具。

**错误响应不回显上游正文。** Microsoft 返回的原始错误可能包含租户信息和令牌片段，所以错误一律归一化后再返回；HTTP 日志直接关闭。

**验证码匹配是线性的。** 验证码和上下文通过合并窗口做线性匹配，不用回溯正则——避免在畸形邮件上触发灾难性回溯。

**有界服务。** 内置 HTTP 服务采用 10 秒 deadline 与 64 线程上限。

**`localStorage` 里只有主题名。** 其他任何东西都不写。

### 官方依据

实现按 Microsoft 当前公开规范：

- [Outlook.com POP、IMAP 与 SMTP 设置](https://support.microsoft.com/en-us/outlook/pop-imap-and-smtp-settings-for-outlook-com)
- [使用 OAuth 连接 IMAP、POP 或 SMTP](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)
- [Microsoft identity platform OAuth 2.0](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)

## 它不做什么

- 不接受邮箱密码，不做密码登录。
- 不发信、不删信、不修改邮箱任何内容（只读收件箱）。
- 不采集账号、不代你申请凭据、不绕过 Microsoft 的授权、风控或服务条款。
- 不持久化账号、client ID、令牌、邮件正文或验证码。

## 隐私边界

它不持久化账号、client ID、refresh / access token、邮件正文或验证码；HTTP 日志关闭，错误响应不回显 Microsoft 原始正文。浏览器主题是唯一写入 `localStorage` 的内容。

**它保护不了什么：** 已经被恶意浏览器扩展、操作系统、反向代理或 Microsoft 租户本身获取的内容。远程使用必须启用 HTTPS；最稳妥的服务器方式是只监听远端回环地址，再通过 SSH 隧道访问。

完整威胁模型见[安全模型](docs/安全模型.md)。

## 开发验证

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/core.test.js
ruff check inbox_harbor tests
bandit -q -lll -r inbox_harbor
python -m pip_audit -r requirements.txt
```

发布前另外执行 Gitleaks、detect-secrets、完整 Git 历史扫描、截图 / OCR / 元数据检查、Docker 构建与公开克隆复验。

## 更多文档

[部署指南](docs/部署指南.md) · [认证准备](docs/认证准备.md) · [安全模型](docs/安全模型.md) · [发布审计](docs/发布审计.md) · [版本变更](CHANGELOG.md) · [参与开发](CONTRIBUTING.md) · [安全策略](SECURITY.md)

## 许可与声明

[MIT](LICENSE) © 2026 ferretgeek

这是独立项目，与 Microsoft 没有隶属、授权或背书关系。请只用它访问你拥有或已获明确授权管理的邮箱。
