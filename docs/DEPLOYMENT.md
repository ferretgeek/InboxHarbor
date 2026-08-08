# Deployment

## Local use (recommended)

```bash
python -m inbox_harbor
```

The default `http://127.0.0.1:4174` listener accepts loopback traffic only.

## Remote Linux through an SSH tunnel

Keep InboxHarbor on the server loopback interface:

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

`GET /api/health` contains no account data. InboxHarbor has no database or migrations, so rollback means restarting the prior image or source release.
