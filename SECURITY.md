# Security Policy

## Supported version

Security fixes are provided for the latest release and the `main` branch.

## Report privately

Use GitHub **Private vulnerability reporting**. Do not open a public issue containing real email addresses, Microsoft application IDs, refresh/access tokens, messages, verification codes, tenant identities, deployment hostnames, access keys, screenshots, logs, or account files. Reproduce with synthetic data only.

## Security boundary

InboxHarbor keeps submitted credentials in request memory only, suppresses HTTP request logs, fixes network destinations to Microsoft login and Outlook IMAP hosts, and returns sanitized errors. It cannot protect a compromised browser, extension, operating system, reverse proxy, Microsoft tenant, or exported file.

The default listener is loopback-only. A non-loopback listener requires an application access key and Host allowlist, but that does not replace HTTPS. For a remote server, keep the published port on loopback and use an SSH tunnel whenever possible.

## 中文说明

请通过仓库的私密漏洞报告功能提交安全问题。报告中不得包含真实账号、令牌、邮件、验证码、服务器地址或身份截图；请只使用合成数据。仅从文件中删除已公开秘密并不构成修复，相关秘密仍需撤销或轮换，并清理 Git 历史与发布资产。
