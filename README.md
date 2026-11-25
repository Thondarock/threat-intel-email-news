# Threat Intel Email News

A daily **cyber threat intelligence brief generator**. It pulls today's articles from security news RSS feeds, uses Google's generative AI to summarise each one (risk level, impact, mitigation) in plain language for a defined organisation profile, builds a styled HTML brief, and optionally emails it to your team.

## How it works

1. Reads RSS feeds (BleepingComputer, The Hacker News, SecurityWeek, Cybersecurity News, GBHackers).
2. Keeps only articles published today (UTC) and de-duplicates titles.
3. Asks the model for a structured summary: **risk level (CRITICAL / HIGH / MEDIUM / LOW), summary, impact, mitigation**.
4. Saves `SOC_Brief_<date>.html` (adds `_v1`, `_v2`… if the file exists).
5. Prompts you before emailing the brief over SMTP.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in values
```

Export the variables from `.env` into your shell (the script reads environment variables):

```powershell
# PowerShell example
$env:GOOGLE_AI_API_KEY = "..."
$env:SENDER_EMAIL = "you@gmail.com"
$env:SENDER_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
$env:RECIPIENTS = "a@example.com,b@example.com"
```

| Variable | Purpose |
|---|---|
| `GOOGLE_AI_API_KEY` | Google AI Studio key (required) |
| `SENDER_EMAIL` / `SENDER_APP_PASSWORD` | SMTP login (Gmail App Password) — only needed to send |
| `RECIPIENTS` | Comma-separated recipient list |
| `SMTP_SERVER` / `SMTP_PORT` | Default `smtp.gmail.com` / `587` |

## Usage

```bash
python "Email Delivery Action/EmailNews.py"
```

Customise `ORG_PROFILE` and `SOURCES` at the top of the script to match your environment and preferred feeds.

## Notes

- Never commit real keys or passwords. Rotate any credential that has been exposed.
- AI output can be wrong — treat briefs as awareness material and verify before acting.
