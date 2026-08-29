import os
import sys
import glob
import json
import requests

def main():
    print("=== 9Router / OneiAPI Bulk Connection Injector ===")
    
    tokens_dir = "tokens"
    if not os.path.exists(tokens_dir):
        print(f"Error: Folder '{tokens_dir}' not found. Run cbcn_manual_grab.py first to acquire tokens.")
        sys.exit(1)
        
    json_files = glob.glob(os.path.join(tokens_dir, "*.json"))
    if not json_files:
        print(f"Error: No JSON token files found in '{tokens_dir}/' directory.")
        sys.exit(1)
        
    print(f"Found {len(json_files)} token file(s) in '{tokens_dir}/'.")
    
    # Get 9router config from environment or prompts
    router_url = os.environ.get("ROUTER_URL") or input("Enter 9router Base URL (e.g. http://localhost:3000): ").strip()
    router_password = os.environ.get("ROUTER_PASSWORD") or input("Enter 9router Admin Password: ").strip()
    
    router_url = router_url.rstrip('/')
    
    # 1. Login to 9router / OneiAPI
    print("\n[1] Logging into 9router admin portal...")
    session = requests.Session()
    try:
        r_login = session.post(f"{router_url}/api/auth/login", json={"password": router_password})
        if r_login.status_code != 200:
            print(f"Error: Login failed (HTTP {r_login.status_code}):", r_login.text)
            sys.exit(1)
        print("[+] Login successful.")
    except Exception as e:
        print("Error connecting to router:", e)
        sys.exit(1)

    # 2. Loop and inject each token file
    print("\n[2] Injecting connections into 9router...")
    success_count = 0
    fail_count = 0

    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                token_data = json.load(f)
                
            phone = token_data.get('phone', 'unknown').replace('+852', '')
            access_token = token_data.get('accessToken')
            refresh_token = token_data.get('refreshToken')
            expires_in = token_data.get('expiresIn', 5184000)
            
            if not access_token or not refresh_token:
                print(f"[-] Skipping {file_path}: Invalid structure.")
                fail_count += 1
                continue

            connection_name = f"CB_{phone}"
            payload = {
                "provider": "codebuddy-cn",
                "authType": "apikey",
                "name": connection_name,
                "priority": 1,
                "isActive": True,
                "apiKey": access_token,
                "data": json.dumps({
                    "accessToken": access_token,
                    "refreshToken": refresh_token,
                    "expiresIn": expires_in,
                    "tokenType": "Bearer",
                    "scope": "openid",
                    "testStatus": "active"
                })
            }
            
            r_add = session.post(f"{router_url}/api/providers", json=payload)
            if r_add.status_code in [200, 201]:
                print(f"  [+] Injected '{connection_name}' from {os.path.basename(file_path)}")
                success_count += 1
            else:
                print(f"  [-] Failed '{connection_name}': HTTP {r_add.status_code}")
                fail_count += 1

        except Exception as e:
            print(f"  [-] Error processing {file_path}:", e)
            fail_count += 1

    print("\n" + "="*40)
    print(f"INJECTION SUMMARY: {success_count} Succeeded, {fail_count} Failed.")
    print("="*40)

if __name__ == "__main__":
    main()
