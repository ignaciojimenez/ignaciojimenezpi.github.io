# Decisions

One-liner record of architecture and strategy decisions.

## 2026-09-05 — Security hardening (Aikido findings)

- Self-host the Inter webfont from `/fonts/` instead of loading it from Google Fonts — Google Fonts CSS cannot carry a stable SRI hash (the response varies by user-agent), so self-hosting is the only real fix for the missing-integrity finding; it also drops two external origins from the CSP and removes a third-party request from every page load.
- Use the Inter *variable* font (weights 300–700, `latin` + `latin-ext`) — 2 files (133 KB) instead of the 10 static-weight files the previous Google Fonts request pulled in.
- Drop `'unsafe-inline'` from `style-src` — the only inline CSS on the site was one `style` attribute on the home page; JS styling uses CSSOM (`element.style.*`), which CSP does not govern, so nothing else was affected.
- Add `object-src 'none'` — explicit, rather than relying on the `default-src 'self'` fallback.
- Pin dependency floors at patched versions (`Pillow==12.3.0`, `pillow-heif>=1.3.0`) rather than tracking latest, so scanners read the floor as safe.
- Keep the service worker's cache list same-origin only — it previously listed `cdn.tailwindcss.com` and a Google Fonts URL that the CSP already blocked, which would fail `cache.addAll()` and abort the whole install.
