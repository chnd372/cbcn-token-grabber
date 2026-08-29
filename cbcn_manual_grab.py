import requests
import json
import re
import html
import sys
import os
import urllib.parse
from bs4 import BeautifulSoup

def main():
    print("=== CodeBuddy CN Token Grabber (Manual Version) ===")
    
    proxy = input("Enter HK Proxy (press Enter to skip): ").strip()
    phone_input = input("Enter 8-digit HK phone number (e.g. 70981305): ").strip()
    
    if not phone_input.isdigit() or len(phone_input) != 8:
        print("Error: Phone number must be 8 digits.")
        sys.exit(1)
        
    phone_full = "+852" + phone_input
    
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        print(f"Using proxy: {proxy}")
        
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    # 1. State
    print("\n[1] Fetching OIDC State...")
    try:
        resp = session.post("https://copilot.tencent.com/v2/plugin/auth/state?platform=CLI", json={}, headers={
            'X-Requested-With': 'XMLHttpRequest',
            'X-Domain': 'copilot.tencent.com',
            'X-No-Authorization': 'true',
            'X-No-User-Id': 'true',
            'X-Product': 'SaaS'
        })
        state_data = resp.json()
        device_code = state_data['data']['state']
        auth_url = state_data['data']['authUrl']
        print(f"Device Code: {device_code}")
    except Exception as e:
        print("Error fetching state:", e)
        sys.exit(1)

    # 2. OIDC form
    print("[2] Initiating Keycloak login flow...")
    kc_url = f"https://www.codebuddy.cn/auth/realms/copilot/protocol/openid-connect/auth?client_id=console&redirect_uri=https%3A%2F%2Fwww.codebuddy.cn%2Fconsole%2Faccounts%2F.apisix%2Fredirect&response_type=code&scope=openid%20offline_access&state={device_code}"
    r_kc = session.get(kc_url)
    
    soup = BeautifulSoup(r_kc.text, 'html.parser')
    form = soup.find('form', id='kc-form-login')
    if not form:
        print("Error: Keycloak form not found. CodeBuddy CN block or proxy issue.")
        sys.exit(1)
        
    action = html.unescape(form.get('action'))

    # 3. SMS trigger
    print(f"[3] Triggering SMS OTP to {phone_full}...")
    sms_url = f"https://www.codebuddy.cn/auth/realms/copilot/sms/authentication-code?phoneNumber={requests.utils.quote(phone_full)}"
    resp_sms = session.get(sms_url, headers={"Referer": r_kc.url})
    print("Upstream SMS Response:", resp_sms.text)

    # 4. Manual OTP Input
    print("\n" + "="*40)
    otp = input("Enter 6-digit OTP code received on phone: ").strip()
    print("="*40 + "\n")
    
    if not otp.isdigit() or len(otp) != 6:
        print("Error: OTP must be 6 digits.")
        sys.exit(1)

    # 5. Submit OTP
    print("[4] Submitting OTP...")
    post_data = {
        "phoneNumber": phone_full,
        "code": otp,
        "credentialId": "",
        "phoneActivated": "true",
        "login": "登录"
    }
    resp_post = session.post(action, data=post_data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": r_kc.url,
        "Origin": "https://www.codebuddy.cn"
    }, allow_redirects=False)

    # 6. Follow redirect to APISIX
    redirect_url = resp_post.headers.get('Location')
    if redirect_url:
        session.get(redirect_url, allow_redirects=True)

    # 7. Enterprise verification (state 2) to fetch tokens
    print("[5] Resolving SaaS session tokens...")
    confirm_headers = {
        "Content-Type": "application/json",
        "Referer": "https://www.codebuddy.cn/console/accounts",
        "X-Requested-With": "XMLHttpRequest"
    }
    r_ent = session.post("https://www.codebuddy.cn/console/login/enterprise", json={"state": 2}, headers=confirm_headers)
    token_res = r_ent.json()

    if token_res.get("code") != 0 or not token_res.get("data", {}).get("accessToken"):
        print("Error: Token extraction failed.", token_res)
        sys.exit(1)

    tdata = token_res["data"]
    
    # Save tokens inside tokens/ folder
    os.makedirs("tokens", exist_ok=True)
    filename = os.path.join("tokens", f"cbcn_tokens_{phone_input}.json")
    with open(filename, "w") as f:
        json.dump({
            "phone": phone_full,
            "accessToken": tdata["accessToken"],
            "refreshToken": tdata["refreshToken"],
            "expiresIn": tdata["expiresIn"]
        }, f, indent=2)
        
    print("\n*** SUCCESS! TOKENS ACQUIRED ***")
    print(f"Saved payload to: {filename}")
    print(f"Access Token (truncated): {tdata['accessToken'][:30]}...")
    print(f"Refresh Token (truncated): {tdata['refreshToken'][:30]}...")
    print(f"Expires In: {tdata['expiresIn']} seconds (~60 days)")

if __name__ == "__main__":
    main()
