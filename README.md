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

## How to Inject into OneiAPI / 9Router
Use the browser/dashboard to add a Connection under `codebuddy-cn` as **API Key** or inject the output json payload into the `providerConnections` database.
