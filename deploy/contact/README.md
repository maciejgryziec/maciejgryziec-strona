# Direct contact delivery for maciejgryziec.pl

Private Python WSGI service behind the site's nginx. The static site stays in the existing Coolify application; this sidecar runs on the same VPS. Nothing here belongs in the public static image (the root `.dockerignore` excludes `deploy/`).

## Deployment

The deployed directory is `/opt/maciejgryziec-contact`. `compose.yaml` creates `maciejgryziec-contact` on the existing `coolify` Docker network. Its host port is loopback-only, `127.0.0.1:18181`, and the process runs as UID 10001 with a read-only root filesystem, resource limits, no capabilities and no-new-privileges. `/data` stores only anti-abuse and idempotency metadata. `/run/contact` is a private read-only mount.

The website forwards ONLY `/api/contact` and `/api/contact/session` to the sidecar. Its nginx overwrites the client-IP header after resolving the trusted Coolify proxy chain. An unrelated website cannot use CORS to submit the form. Static files remain read-only GET/HEAD resources.

## Activation by the mailbox owner

The service starts with `ready:false`. It cannot send email until its owner configures SMTP and the test succeeds. The public form retains its existing working email-draft action while direct sending is unavailable. It does not claim a message has been sent.

Run manually in an interactive terminal:

```sh
ssh -t moj-vps 'sudo python3 /opt/maciejgryziec-contact/configure_smtp.py'
```

Enter the existing mailbox password at the hidden prompt. Never put it in tool arguments, shell arguments, git, a chat message or a screenshot. The script does not retrieve browser/Keychain passwords, change the OVH password or create another mailbox. It authenticates to `smtp.mail.ovh.net:465` with TLS and sends ONE labelled test to `kontakt@maciejgryziec.pl`. Only after SMTP acceptance does it atomically save a mode-0600 configuration owned by the service UID. The website switches to **Wyślij** when reloaded and `/api/contact/session` confirms readiness. Inbox receipt must still be checked by the mailbox owner; SMTP acceptance alone is not evidence of inbox placement.

Do not recreate accounts, reset the user's mailbox password, use denied Gmail access, purchase a mail service or change DNS to work around missing credentials.

## Sending and failure handling

- Fixed sender and recipient: `kontakt@maciejgryziec.pl`. The visitor's validated email is only `Reply-To`.
- Plain text body. No attachments, visitor-configured recipients, automatic replies or fetched URLs.
- JSON-only POST, exact Origin plus a custom header, signed IP-bound expiring token, hidden bot field, minimum token age and length limits.
- 3 attempts per 10 minutes and 12 per day per pseudonymous client; 60 per day globally. Request IDs prevent duplicate delivery, including concurrent clicks.
- An ambiguous SMTP disconnect is not retried automatically and is not reported as sent. A client network retry uses the same idempotency ID for unchanged content.
- Form contents remain in memory while forwarding; they are not written to the application database or logs. SQLite holds a request ID, keyed fingerprints, time and status. Records are removed after 48 hours, token counters after one hour, including periodic health checks.
- The backend checks configuration per request, so activation does not require a new deployment. No password is included in the static site or Docker environment metadata.

## Verification

```sh
cd deploy/contact
python3 -m unittest -v test_app
cd ../..
python3 narzedzia/audyt-formularza.py
```

The browser test mocks `/api/contact` and sends NO real email. Cover success, duplicate submission, unavailable SMTP, validation, cross-origin requests, header injection, replay, rate limits, ambiguous delivery, no body storage and mobile form behavior. Real SMTP/receipt testing is separate and must not be labelled complete without evidence.

## Sources

- OVH SMTP settings: https://docs.ovhcloud.com/en/guides/web-cloud/email-and-collaborative-solutions/zimbra/mail-apps
- OWASP CSRF prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP logging: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Gunicorn release: https://pypi.org/project/gunicorn/26.2.0/

## Rollback

Removing the nginx API proxy or returning `ready:false` leaves the original email-draft form available after a page reload. To revoke server SMTP access, remove `/opt/maciejgryziec-contact/secrets/smtp.json` after confirming the request with the owner; never delete the mailbox. Backend code, secrets and data are kept separate from the site's repository. A previous site commit can be redeployed without recreating the sidecar or mailbox.
