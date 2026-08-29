# CodeBuddy CN Manual Token Grabber

Simple Python tool to manually log in to CodeBuddy CN (+852 Hong Kong numbers) and extract the **60-day OAuth token pair** (Access + Refresh tokens) for use in 9router/OneiAPI.

## Features
- Generates a device OIDC authorization flow.
- Triggers SMS code delivery to your HK number.
- Prompts for OTP code in terminal.
- Performs backend login and returns raw tokens inside `tokens/cbcn_tokens_<phone>.json`.
- Includes a **bulk injector** script to push all acquired tokens into 9router/OneiAPI at once.

## Setup

1. Install requirements:
   ```bash
   pip install requests beautifulsoup4
   ```

2. Run the token grabber script to create account(s):
   ```bash
   python cbcn_manual_grab.py
   ```
   *(Repeat as many times as you want for multiple numbers. All JSON files automatically drop into `tokens/`)*

## Detailed Execution Steps

1. **Enter HK Proxy (optional):** Enter proxy address if Tencent blocks datacenter IPs. Hit Enter to skip if running locally.
2. **Enter Phone:** Input your 8-digit Hong Kong number (e.g. `70981305`). Do not include prefix `+852`.
3. **Wait for SMS:** Check your SMS box/5sim panel. Type the 6-digit code in the terminal prompt and hit Enter.
4. **Acquire Tokens:** The script outputs success status and saves tokens to `tokens/cbcn_tokens_<phone>.json`.

## How to Inject into 9Router / OneiAPI (Bulk)

### Method 1: Using the Bulk Auto-Injector Script (Recommended)
We provide a helper script to automatically scan the `tokens/` folder and inject **all acquired JSON tokens** into your 9router backend:

1. Run the bulk injector:
   ```bash
   python cbcn_9router_inject.py
   ```
2. Enter your 9router base URL (e.g., `http://localhost:3000`).
3. Enter your 9router admin password.
4. The script scans `tokens/*.json` and registers every account under `CB_<phone>`.

*(Tip: Set `ROUTER_URL` and `ROUTER_PASSWORD` environment variables to skip prompts)*

---

### Method 2: Manual Web UI
1. Open your 9router Dashboard.
2. Go to **Providers** page and search for **CodeBuddy CN**.
3. Click **API Key**.
4. Open the JSON file in `tokens/` and copy the **`accessToken`** string into the **API Key** box.
5. Save.
