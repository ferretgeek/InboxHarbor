# Deployment

## Local use (recommended)

```bash
python -m inbox_harbor
```

The default `http://127.0.0.1:4174` listener accepts loopback traffic only.

## Remote Linux through an SSH tunnel

Keep the service on the server loopback interface:

```bash
python -m inbox_harbor --host 127.0.0.1 --port 4174
ssh -L 4174:127.0.0.1:4174 your-user@your-server
```

Open `http://127.0.0.1:4174` on your own computer. The application port never needs to become public.

## Docker Compose

The included Compose service binds the host port to loopback and uses a read-only filesystem, no Linux capabilities, no-new-privileges, and bounded CPU, memory, and process counts.

```bash
export INBOXHARBOR_ACCESS_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build -d
```

Never commit or screenshot the generated access key.

## Public hostname

If a public hostname is unavoidable, set a random `INBOXHARBOR_ACCESS_TOKEN` of at least 32 characters, set the exact hostname in `INBOXHARBOR_ALLOWED_HOSTS`, and place the application behind an HTTPS reverse proxy. Disable request-body, authentication-header, and session-recording logs. The key field in the UI remains in page memory and is not stored.

`GET /api/health` contains no account data. The service has no database or migrations, so rollback means restarting the prior image or source release.

## Architecture, upgrade, and backup

The browser sends credentials and scan options to the same-origin Python service for one bounded request. The service connects only to fixed Microsoft OAuth/IMAP hosts, returns reduced read-only results, and does not persist credentials, messages, codes, or scan history. The access key remains deployment configuration; the UI keeps it in page memory only.

Upgrade by retaining the previous source/image and private secret configuration, starting the candidate on another loopback port, checking `/api/health`, then completing one synthetic or low-risk read-only scan before switching. Rollback restores the previous source/image.

There is no application database to back up. Back up only the private service/proxy configuration with encrypted infrastructure tooling. Mail remains at Microsoft; do not create ad-hoc exports of messages or credentials as an application backup.

## Uninstall and troubleshooting

- Stop/disable the process or run `docker compose down`; remove the image/virtual environment after the rollback window.
- Remove access tokens from the secret store and clear browser site data; no application database remains.
- `401`: re-enter the deployment access token; the browser intentionally does not persist it.
- Host/Origin rejection: use the configured same-origin hostname and keep the protections enabled.
- OAuth/IMAP failure: verify the tenant/client configuration, consent, TLS-capable network, and Microsoft account state without logging token or message values.
- Empty results: confirm the selected folder and time range; the application reads only the bounded inbox scope described in the security model.
- Remote failures: first reproduce through the SSH tunnel. Do not solve them by binding publicly or disabling HTTPS/authentication.

Before sharing diagnostics, remove email addresses, tenant/client IDs, tokens, message metadata, codes, endpoints tied to your deployment, and local paths.
