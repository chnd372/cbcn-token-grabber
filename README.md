# CodeBuddy CN Manual Token Grabber

Simple Python tool to manually log in to CodeBuddy CN (+852 Hong Kong numbers) and extract the **60-day OAuth token pair** (Access + Refresh tokens) for use in 9router/OneiAPI.

## Features
- Generates a device OIDC authorization flow.
- Triggers SMS code delivery to your HK number.
- Prompts for OTP code in terminal.
- Performs backend login and returns the raw `accessToken` and `refreshToken` payload (stored inside `cbcn_tokens_<phone>.json`).

## Setup

1. Install requirements:
   ```bash
   pip install requests beautifulsoup4
   ```

2. Run the script:
   ```bash
   python cbcn_manual_grab.py
   ```

## Detailed Execution Steps

1. **Enter HK Proxy (optional):** Enter proxy address (e.g. `http://user:pass@host:port`) if tencent blocks datacenter IPs. Hit Enter to skip if running locally.
2. **Enter Phone:** Input your 8-digit Hong Kong number (e.g. `70981305`). Do not include prefix `+852`.
3. **Wait for SMS:** Check your SMS box/5sim panel. Once code arrives, type the 6-digit code in the terminal prompt and hit Enter.
4. **Acquire Tokens:** The script will output success status and save tokens directly to `cbcn_tokens_<phone>.json`.

## How to Inject into 9Router / OneiAPI

You have two ways to add the generated token to your 9router:

### Method 1: Web UI (Dashboard) — Recommended
1. Open your 9router Dashboard.
2. Go to **Providers** page and search for **CodeBuddy CN** (or `codebuddy-cn`).
3. Click the **API Key** button (do not click OAuth, as the web login will fail or require visual browser interaction).
4. Paste the **`accessToken`** string (the long `eyJ...` token from `cbcn_tokens_<phone>.json`) directly into the **API Key** input box.
5. Save. The backend will automatically treat it as a valid session and route requests.

### Method 2: Direct Database Injection (SQLite)
If you want usage tracking, auto-refresh support, and correct priority handling, inject the token payload directly into the SQLite database.

1. Locate your 9router `data.sqlite` database file (usually under `~/.9router/db/data.sqlite`).
2. Run the following SQL query to insert the connection:
   ```sql
   INSERT INTO providerConnections 
   (id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt)
   VALUES (
     'unique-uuid-here',
     'codebuddy-cn',
     'oauth',
     'CB_MY_ACCOUNT',
     NULL,
     1,
     1,
     '{"accessToken": "PASTE_ACCESS_TOKEN_HERE", "refreshToken": "PASTE_REFRESH_TOKEN_HERE", "expiresAt": "2026-10-29T10:00:00.000Z", "expiresIn": 5184000, "tokenType": "Bearer", "scope": "openid", "testStatus": "active"}',
     datetime('now'),
     datetime('now')
   );
   ```
3. Restart 9router to apply changes.
