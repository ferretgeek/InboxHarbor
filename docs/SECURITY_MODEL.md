# Security and privacy model

InboxHarbor protects mailbox identities, Microsoft client IDs, refresh/access tokens, messages, verification codes, and remote access keys from application persistence, URLs, request logs, reflected upstream errors, screenshots, and fixtures.

Controls include fixed Microsoft login and IMAP hosts, TLS 1.2+, OAuth2/XOAUTH2 only, read-only inbox selection, partial message fetches, bounded inputs and work, no HTTP request logs, same-origin and Host validation, DNS-rebinding protection, strict response headers, rate limiting, loopback defaults, and mandatory access-key protection for non-loopback listeners. The browser renders all message data as text, clears credential input after request construction, veils details by default, and exports only dates and counts—not sender, subject, body, or code values.

InboxHarbor deliberately has no credential vault, password or app-password flow, custom IMAP/OAuth destinations, analytics, telemetry, remote fonts, or remote scripts.

It cannot defend against a compromised browser extension, operating system, reverse proxy, screen recorder, crash dump, swap file, or Microsoft account. Extracted verification codes are heuristic and require human confirmation. HTTPS remains mandatory for any remote path.
