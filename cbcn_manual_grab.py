#!/usr/bin/env python3
"""
CodeBuddy CN Manual Token Grabber & 9Router Injector (with Ping Verification)

Flow:
1. Prompts for 8-digit HK phone number (+852)
2. Fetches OIDC Device Code & Keycloak Login Form
3. Triggers SMS Code to phone
4. Prompts for 6-digit OTP code received on phone
5. Submits OTP and harvests Enterprise State 2 OAuth Tokens (valid 60 days)
6. Option to Auto-Inject into 9router / OneiAPI with instant Stream Ping Verification!
"""

import os
import sys
import time
import json
import html
import requests
from bs4 import BeautifulSoup

def ping_verify_connection(router_url, s_router, connection_name):
    """Perform streaming completion test against 9router upstream to confirm account is 100% active"""
    print(f"  [PING TEST] Testing connection '{connection_name}' upstream...")
    try:
        ping_url = f"{router_url}/v1/chat/completions"
        ping_payload = {
            "model": "glm-5.2",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True
        }
        r = s_router.post(ping_url, json=ping_payload, headers={"Content-Type": "application/json"}, timeout=20, stream=True)
        if r.status_code != 200:
            print(f"  ❌ PING FAILED: HTTP {r.status_code} - {r.text[:100]}")
            return False
        
        has_stream = False
        for line in r.iter_lines():
            if line:
                has_stream = True
                break
        if not has_stream:
            print("  ❌ PING FAILED: Stream returned empty body.")
            return False

        print(f"  ✅ PING VERIFIED! Account '{connection_name}' is 100% ALIVE & replying!")
        return True
    except Exception as e:
        print(f"  ❌ PING FAILED with exception: {e}")
        return False

def inject_to_router(router_url, router_password, phone_input, tdata):
    """Inject tokens to 9router & run Ping Verification"""
    print("\n[+] Injecting token into 9router / OneiAPI...")
    s_router = requests.Session()
    
    # Login
    try:
        r_login = s_router.post(f"{router_url}/api/auth/login", json={"password": router_password}, timeout=15)
        if r_login.status_code != 200:
            print(f"❌ 9router login failed (HTTP {r_login.status_code}): {r_login.text}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to 9router ({router_url}): {e}")
        return False

    connection_name = f"CB_{phone_input}"
    payload = {
        "provider": "codebuddy-cn",
        "authType": "apikey",
        "name": connection_name,
        "priority": 1,
        "isActive": True,
        "apiKey": tdata["accessToken"],
        "data": json.dumps({
            "accessToken": tdata["accessToken"],
            "refreshToken": tdata["refreshToken"],
            "expiresIn": tdata.get("expiresIn", 5184000),
            "tokenType": "Bearer",
            "scope": "openid",
            "testStatus": "active"
        })
    }

    r_add = s_router.post(f"{router_url}/api/providers", json=payload, timeout=15)
    if r_add.status_code in [200, 201]:
        print(f"  [+] Account '{connection_name}' registered in 9router.")
        # Ping Test
        return ping_verify_connection(router_url, s_router, connection_name)
    else:
        print(f"  ❌ 9router injection failed (HTTP {r_add.status_code}): {r_add.text}")
        return False

def process_single_account(session, proxy, router_url=None, router_password=None):
    print("\n" + "="*50)
    phone_input = input("Enter 8-digit HK phone number (e.g. 70981305, or 'q' to quit): ").strip()
    
    if phone_input.lower() in ['q', 'quit', 'exit']:
        return False
        
    if not phone_input.isdigit() or len(phone_input) != 8:
        print("Error: Phone number must be 8 digits.")
        return True
        
    phone_full = "+852" + phone_input

    # 1. State
    print("\n[1] Fetching OIDC State...")
    try:
        resp = session.post("https://copilot.tencent.com/v2/plugin/auth/state?platform=CLI", json={}, headers={
            'X-Requested-With': 'XMLHttpRequest',
            'X-Domain': 'copilot.tencent.com',
            'X-No-Authorization': 'true',
            'X-No-User-Id': 'true',
            'X-Product': 'SaaS'
        }, timeout=20)
        state_data = resp.json()
        device_code = state_data['data']['state']
        print(f"Device Code: {device_code}")
    except Exception as e:
        print("Error fetching state:", e)
        return True

    # 2. OIDC form
    print("[2] Initiating Keycloak login flow...")
    kc_url = f"https://www.codebuddy.cn/auth/realms/copilot/protocol/openid-connect/auth?client_id=console&redirect_uri=https%3A%2F%2Fwww.codebuddy.cn%2Fconsole%2Faccounts%2F.apisix%2Fredirect&response_type=code&scope=openid%20offline_access&state={device_code}"
    r_kc = session.get(kc_url, timeout=20)
    
    soup = BeautifulSoup(r_kc.text, 'html.parser')
    form = soup.find('form', id='kc-form-login') or soup.find('form', id='kc-sms-login-form') or soup.find('form')
    if not form or 'action' not in form.attrs:
        print("Error: Keycloak form not found. CodeBuddy CN WAF block or proxy issue.")
        return True
        
    action = html.unescape(form.get('action'))

    # 3. SMS trigger
    print(f"[3] Triggering SMS OTP to {phone_full}...")
    sms_url = f"https://www.codebuddy.cn/auth/realms/copilot/sms/authentication-code?phoneNumber={requests.utils.quote(phone_full)}"
    resp_sms = session.get(sms_url, headers={"Referer": r_kc.url}, timeout=20)
    print("Upstream SMS Response:", resp_sms.text)

    # 4. Manual OTP Input
    print("\n" + "-"*40)
    otp = input(f"Enter 6-digit OTP code received for +852 {phone_input}: ").strip()
    print("-" * 40 + "\n")
    
    if not otp.isdigit() or len(otp) != 6:
        print("Error: OTP must be 6 digits.")
        return True

    # 5. Submit OTP
    print("[4] Submitting OTP...")
    post_data = {
        "phoneNumber": phone_full,
        "username": phone_full,
        "code": otp,
        "phoneActivated": "true",
        "login": "登录"
    }
    
    resp_post = session.post(action, data=post_data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": r_kc.url,
        "Origin": "https://www.codebuddy.cn"
    }, allow_redirects=False, timeout=20)

    print(f"Submit HTTP Code: {resp_post.status_code}")
    
    # 6. Check 302 Redirect
    if resp_post.status_code == 302:
        redirect_url = resp_post.headers.get('Location')
        print(f"Redirecting to APISIX OAuth callback...")
        session.get(redirect_url, allow_redirects=True, timeout=20)
    elif resp_post.status_code == 200:
        soup_err = BeautifulSoup(resp_post.text, 'html.parser')
        err_div = soup_err.find('span', {'class': 'kc-feedback-text'}) or soup_err.find('div', {'class': 'alert-error'})
        print("❌ Login Rejected by Keycloak! Reason:", err_div.text.strip() if err_div else "OTP code incorrect or session expired.")
        return True

    # 7. Enterprise verification (state 2) to fetch tokens
    print("[5] Resolving SaaS session tokens...")
    time.sleep(1)
    confirm_headers = {
        "Content-Type": "application/json",
        "Referer": "https://www.codebuddy.cn/console/accounts",
        "X-Requested-With": "XMLHttpRequest"
    }
    r_ent = session.post("https://www.codebuddy.cn/console/login/enterprise", json={"state": 2}, headers=confirm_headers, timeout=20)
    
    try:
        token_res = r_ent.json()
    except Exception as e:
        print("❌ Error: SaaS session creation failed (HTTP 401/403).")
        print("Raw response:", r_ent.text[:200])
        return True

    if token_res.get("code") != 0 or not token_res.get("data", {}).get("accessToken"):
        print("Error: Token extraction failed.", token_res)
        return True

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
    print(f"Access Token: {tdata['accessToken'][:30]}...")
    print(f"Expires In: {tdata['expiresIn']} seconds (~60 days)")

    # 8. Auto Inject & Ping Verify (If configured)
    if router_url and router_password:
        inject_to_router(router_url, router_password, phone_input, tdata)
    else:
        do_inject = input("\nDo you want to inject this account into 9router now? (y/n, default: y): ").strip().lower()
        if do_inject not in ['n', 'no']:
            r_url = input("Enter 9router Base URL (e.g. https://api.icantl.my.id): ").strip()
            r_pwd = input("Enter 9router Admin Password: ").strip()
            if r_url and r_pwd:
                inject_to_router(r_url, r_pwd, phone_input, tdata)

    return True

def main():
    print("======================================================")
    print(" CodeBuddy CN Token Grabber + 9Router Ping Verifier  ")
    print("======================================================")
    
    proxy = os.environ.get("PROXY") or input("Enter HK Proxy (press Enter to skip): ").strip()
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        print(f"Using proxy: {proxy}")
        
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    router_url = os.environ.get("ROUTER_URL")
    router_password = os.environ.get("ROUTER_PASSWORD")

    while True:
        cont = process_single_account(session, proxy, router_url, router_password)
        if not cont:
            print("\nExiting. Tokens saved in 'tokens/' directory.")
            break
            
        ask = input("\nDo you want to add another account? (y/n, default: y): ").strip().lower()
        if ask in ['n', 'no']:
            print("\nExiting. Tokens saved in 'tokens/' directory.")
            break

if __name__ == "__main__":
    main()
