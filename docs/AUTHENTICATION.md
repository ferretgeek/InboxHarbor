# Microsoft OAuth2 setup

This project ships no developer identity and accepts no mailbox passwords. Register an application in your own Microsoft Entra tenant, grant only delegated `IMAP.AccessAsUser.All` plus `offline_access`, and acquire a refresh token through a Microsoft-supported authorization-code or device-code flow. Prefer MSAL rather than an unknown token generator.

For consumer Outlook.com accounts, the `consumers` tenant is usually appropriate. IMAP may need to be enabled in Outlook.com settings.

Primary references:

- [OAuth for IMAP, POP, and SMTP](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)
- [Device authorization flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code)
- [Outlook.com IMAP settings](https://support.microsoft.com/en-us/outlook/pop-imap-and-smtp-settings-for-outlook-com)

A refresh token represents durable access. Never put it in Git, chat, screenshots, logs, or cloud clipboards. If one reaches a public repository, revoke or rotate it and remove every reachable copy from Git history and release assets.
