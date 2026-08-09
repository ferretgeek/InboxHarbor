![信港界面预览](docs/images/social-preview.png)

# 信港 / InboxHarbor — Outlook 批量收件台

[![CI](https://github.com/ferretgeek/InboxHarbor/actions/workflows/ci.yml/badge.svg)](https://github.com/ferretgeek/InboxHarbor/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ferretgeek/InboxHarbor/actions/workflows/codeql.yml/badge.svg)](https://github.com/ferretgeek/InboxHarbor/actions/workflows/codeql.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-315b70?logo=python&logoColor=white)](https://www.python.org/)
[![Runtime dependencies](https://img.shields.io/badge/runtime_dependencies-0-2f7d68)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/License-MIT-e57958.svg)](LICENSE)

> 让散落的收件箱，在一处安静的港湾靠岸。

信港是一座面向 Microsoft Outlook / Microsoft 365 的批量收件工作台。它用 OAuth2 只读查看最近邮件、提取验证码，并把真实账号与来信默认藏在一层轻柔的遮罩之后。

[English](README_EN.md) · [部署指南](docs/部署指南.md) · [安全模型](docs/安全模型.md) · [发布审计](docs/发布审计.md) · [报告问题](https://github.com/ferretgeek/InboxHarbor/issues)

## 一眼看懂

- **批量靠岸**：单次读取最多 50 个邮箱，以受控并发保持速度与稳定。
- **现代认证**：仅使用 Microsoft OAuth2 / XOAUTH2，不接受邮箱密码。
- **短暂停泊**：账号与令牌只在本次请求内存中使用，不写磁盘、不进日志。
- **克制读取**：固定 Microsoft 官方主机，只读收件箱，并限制邮件数、大小与超时。
- **安全展示**：账号默认脱敏、邮件详情默认遮挡；最小化导出不含发件人、主题、正文或验证码值。
- **可辨认的界面**：晴空、青玉、暮霞三套浅色主题与深灰暗色主题，桌面和手机都能使用。
- **两种部署**：本机一条命令启动；服务器推荐回环监听 + SSH 隧道，也支持带访问密钥的 HTTPS 反代。

![信港工作台](docs/images/dashboard.png)

![信港入口与隐私边界设计](docs/images/intro.png)

## 本地启动

需要 Python 3.10 或更高版本，无运行时第三方依赖。

```powershell
python -m inbox_harbor
```

打开 `http://127.0.0.1:4174`。可先点“打开合成演示”，它不会连接任何邮箱。

账号格式为一行一条：

```text
lina@example.com----12345678-1234-4234-9234-1234567890ab----REPLACE_WITH_REFRESH_TOKEN----consumers
```

四段依次是邮箱、Microsoft Entra 应用 `client_id`、`refresh_token` 与可选 `tenant`。项目不接收密码；示例全部为合成占位数据。获取 OAuth 凭据前，请阅读[认证准备](docs/认证准备.md)。

## 为什么重做

原始私人脚本会先尝试密码登录、允许任意邮箱主机，并可能把邮件正文或上游错误写进终端与 JSON。这些行为对公开项目并不安全。信港把网络目的地固定为 Microsoft，取消密码路径，收紧重试与工作量边界，并把界面、部署和验证补成一个可以长期维护的成品。

## 隐私边界

信港不会持久化账号、client ID、refresh/access token、邮件正文或验证码；HTTP 日志被关闭，错误响应不会回显 Microsoft 原始正文。浏览器主题是唯一写入 `localStorage` 的内容。

它无法保护已经被恶意扩展、操作系统、反向代理或 Microsoft 租户获取的内容。远程使用必须启用 HTTPS；最稳妥的服务器方式是仅监听远端回环地址，再通过 SSH 隧道访问。完整威胁模型见[安全模型](docs/安全模型.md)。

## 官方依据

实现按 Microsoft 当前公开规范使用 `outlook.office365.com:993`、TLS 与 XOAUTH2：

- [Outlook.com POP、IMAP 与 SMTP 设置](https://support.microsoft.com/en-us/outlook/pop-imap-and-smtp-settings-for-outlook-com)
- [使用 OAuth 连接 IMAP、POP 或 SMTP](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)
- [Microsoft identity platform OAuth 2.0](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)

InboxHarbor 与 Microsoft 无隶属或背书关系。

## 开发验证

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/core.test.js
ruff check inbox_harbor tests
bandit -q -lll -r inbox_harbor
python -m pip_audit -r requirements.txt
```

发布前还会执行 Gitleaks、detect-secrets、完整 Git 历史扫描、截图/OCR/元数据检查、Docker 构建与公开克隆复验。

## 许可证

[MIT](LICENSE) © 2026 ferretgeek
