![Outlook batch inbox](docs/images/social-preview.png)

# Outlook batch inbox

[中文](README.md) · English

[![CI](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/ci.yml/badge.svg)](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/codeql.yml/badge.svg)](https://github.com/ferretgeek/outlook-batch-inbox/actions/workflows/codeql.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-315b70?logo=python&logoColor=white)](https://www.python.org/)
[![Runtime dependencies](https://img.shields.io/badge/runtime_dependencies-0-2f7d68)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/License-MIT-e57958.svg)](LICENSE)

> Read recent mail and verification codes from up to 50 Outlook mailboxes at once. OAuth only, never passwords.

## Why this exists

If you manage a set of Microsoft mailboxes — test accounts, sign-up accounts, shared functional addresses — pulling verification codes out of them one web session at a time is genuinely draining: sign in, wait, find the message, copy, sign out, next.

This turns that into one operation: read a whole batch at once, with recent messages and detected codes listed on a single page.

It accepts **OAuth2 authorization only, never a mailbox password**, and credentials live only in memory for the duration of one request. Accounts are masked by default and message details are veiled — because a screen full of real addresses is itself a risk.

[Deployment](docs/DEPLOYMENT.md) · [Security model](docs/SECURITY_MODEL.md) · [Authentication setup](docs/AUTHENTICATION.md) · [Report an issue](https://github.com/ferretgeek/outlook-batch-inbox/issues)

## Interface

![Workbench](docs/images/dashboard.png)

![Entry point and privacy boundaries](docs/images/intro.png)

## What it does

- **Batch reads** — up to 50 mailboxes per run, with controlled concurrency balancing speed and stability.
- **Modern auth only** — Microsoft OAuth2 / XOAUTH2, and **no mailbox passwords accepted.**
- **Credentials never land** — accounts and tokens exist only in memory for the current request; never written to disk or logs.
- **Restrained reads** — a fixed Microsoft host, inbox read-only, with limits on message count, size, and timeout.
- **Masked by default** — accounts redacted, message details veiled, and the minimal export excludes sender, subject, body, and code values.
- **A usable interface** — Clear Sky, Jade, and Dusk light themes plus deep-gray dark mode, fully usable on desktop and phone.
- **Two deployment modes** — one command locally; on a server, loopback bind plus an SSH tunnel, or an HTTPS reverse proxy with an access key.

## Running locally

Requires Python 3.10 or later, with **no third-party runtime dependencies.**

```powershell
python -m inbox_harbor
```

Open `http://127.0.0.1:4174`. Try "open synthetic demo" first — it connects to no mailbox at all and just shows the interface.

Accounts are one per line, four fields separated by `----`:

```text
lina@example.com----12345678-1234-4234-9234-1234567890ab----REPLACE_WITH_REFRESH_TOKEN----consumers
```

That's the address, the Microsoft Entra application `client_id`, the `refresh_token`, and an optional `tenant`. **No passwords are accepted**; every value above is synthetic placeholder data.

Full steps for obtaining OAuth credentials are in [authentication setup](docs/AUTHENTICATION.md).

## Worth noting technically

**This project was rebuilt, and the reason is worth stating.** The original private script tried password sign-in first, allowed connecting to arbitrary mail hosts, and could write message bodies or upstream errors straight into the terminal and JSON files. Tolerable as a private script; not acceptable in public. So the rebuild did four things: **pinned the network destination to Microsoft, removed the password path entirely, tightened retry and workload bounds, and finished the interface, deployment, and verification into something maintainable.**

**The destination is hard-coded.** It connects only to `outlook.office365.com:993` over TLS with XOAUTH2. A tool that will take your refresh token and connect to an arbitrary host is a phishing tool.

**Error responses never echo upstream bodies.** Raw Microsoft errors can contain tenant details and token fragments, so errors are normalized before they're returned, and HTTP logging is off.

**Code matching is linear.** Verification codes and their context are matched linearly over a merge window rather than with backtracking regexes, which avoids catastrophic backtracking on malformed mail.

**Bounded service.** The built-in HTTP server uses a 10-second deadline and a 64-thread cap.

**`localStorage` holds only the theme name.** Nothing else is written.

### Official references

The implementation follows Microsoft's current public specifications:

- [POP, IMAP, and SMTP settings for Outlook.com](https://support.microsoft.com/en-us/outlook/pop-imap-and-smtp-settings-for-outlook-com)
- [Authenticate an IMAP, POP, or SMTP application using OAuth](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)
- [Microsoft identity platform OAuth 2.0](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow)

## What it doesn't do

- No mailbox passwords, no password sign-in.
- No sending, deleting, or modifying anything (inbox read-only).
- It doesn't harvest accounts, obtain credentials on your behalf, or bypass Microsoft's authorization, risk controls, or terms.
- It doesn't persist accounts, client IDs, tokens, message bodies, or codes.

## Privacy boundaries

Nothing is persisted: accounts, client IDs, refresh/access tokens, message bodies, and codes all stay in memory. HTTP logging is disabled and error responses never echo raw Microsoft bodies. The browser theme is the only thing written to `localStorage`.

**What it can't protect:** anything already obtained by a malicious browser extension, the operating system, a reverse proxy, or the Microsoft tenant itself. Remote use requires HTTPS; the safest server setup is binding the remote loopback address only and reaching it through an SSH tunnel.

The full threat model is in [security model](docs/SECURITY_MODEL.md).

## Development checks

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/core.test.js
ruff check inbox_harbor tests
bandit -q -lll -r inbox_harbor
python -m pip_audit -r requirements.txt
```

Before a release, Gitleaks, detect-secrets, a full Git history scan, screenshot/OCR/metadata checks, a Docker build, and a public-clone re-verification all run as well.

## More documentation

[Deployment](docs/DEPLOYMENT.md) · [Authentication setup](docs/AUTHENTICATION.md) · [Security model](docs/SECURITY_MODEL.md) · [Release audit](docs/发布审计.md) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md)

## License and disclaimer

[MIT](LICENSE) © 2026 ferretgeek

Independent project with no affiliation with, authorization from, or endorsement by Microsoft. Use it only with mailboxes you own or are explicitly authorized to administer.
