# InboxHarbor 项目规则

- 先阅读工作区根 `AGENTS.md` 与本项目 `README.md`。
- 产品定位是隐私优先的 Microsoft Outlook 批量收件工作台；只允许 OAuth2/XOAUTH2，禁止恢复密码认证、任意邮箱主机或原始上游错误回显。
- 邮箱、client ID、refresh token、access token、邮件正文与验证码不得进入磁盘、日志、URL、截图、测试夹具或公开文档。仅主题名可写入 `localStorage`，远程访问密钥也不得持久化。
- 后端默认只监听回环地址。非回环监听必须同时启用至少 32 字符的访问密钥与明确的 Host 白名单；生产流量必须经过 HTTPS。
- 不得削弱请求大小、账号数量、并发、超时、邮件数量、单封邮件大小、同源、CSP、固定 Microsoft 端点或速率限制。
- UI 必须同步维护晴空、青玉、暮霞与深灰四套全局主题；Graphite 背景保持深灰 `#17191d`。桌面与移动端均需实际渲染。
- 公开改动必须同步双语 README、真实界面截图、社交预览、`docs/发布审计.md`、工作区根 `README.md` 与 GitHub 个人主页仓库。
