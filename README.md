# CodeBuddy CN Token Grabber & 9Router Injector

Python toolkit to manually acquire **60-day OAuth token pairs** (Access + Refresh tokens) for CodeBuddy CN (+852 Hong Kong numbers) and automatically verify/inject them into 9router / OneiAPI.

## Features & Scripts

1. **`cbcn_manual_grab.py` (Manual Grabber + Instant Injector)**
   - Enter your 8-digit Hong Kong number.
   - Triggers SMS delivery to phone.
   - Enter 6-digit OTP code in terminal.
   - Harvests enterprise state 2 tokens (valid 60 days).
   - Saves token JSON locally in `tokens/cbcn_tokens_<phone>.json`.
   - **Direct 9router Inject + Ping Test:** Optionally injects immediately into 9router and verifies via streaming ping test (`glm-5.2`).

2. **`cbcn_9router_inject.py` (Bulk Injector + Ping Verify)**
   - Scans all files in `tokens/*.json` and bulk-injects them into 9router.
   - Runs stream chat completion tests against upstream to verify active state.

## Setup

1. Install requirements:
   ```bash
   pip install requests beautifulsoup4
   ```

2. Run grabber:
   ```bash
   python3 cbcn_manual_grab.py
   ```

3. Optional environment variables to skip prompts:
   ```bash
   export ROUTER_URL="https://api.icantl.my.id"
   export ROUTER_PASSWORD="your_password"
   export PROXY="http://user:pass@gw.dataimpulse.com:823" # Recommended if VPS IP gets WAF 403
   ```
