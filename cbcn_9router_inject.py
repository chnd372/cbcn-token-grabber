import os
import sys
import json
import requests

def main():
    print("=== 9Router / OneiAPI Connection Injector ===")
    
    token_file = input("Enter path to token JSON file (e.g., cbcn_tokens_70211189.json): ").strip()
    if not os.path.exists(token_file):
        print(f"Error: File {token_file} not found.")
        sys.exit(1)
        
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        
    phone = token_data.get('phone', 'unknown').replace('+852', '')
    access_token = token_data.get('accessToken')
    refresh_token = token_data.get('refreshToken')
    expires_in = token_data.get('expiresIn', 5184000)
    
    if not access_token or not refresh_token:
        print("Error: Invalid token JSON file structure.")
        sys.exit(1)
        
    # Get 9router config from environment or prompts
    router_url = os.environ.get("ROUTER_URL") or input("Enter 9router Base URL (e.g. http://localhost:3000): ").strip()
    router_password = os.environ.get("ROUTER_PASSWORD") or input("Enter 9router Admin Password: ").strip()
    connection_name = input(f"Enter connection name (default: CB_{phone}): ").strip() or f"CB_{phone}"
    
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
        
    # 2. Prepare Payload
    # Structure mirrors standard 9router/OneiAPI providerConnections table layout
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
    
    # 3. Post/Inject to 9router
    print(f"[2] Injecting connection '{connection_name}' into 9router...")
    try:
        r_add = session.post(f"{router_url}/api/providers", json=payload)
        if r_add.status_code in [200, 201]:
            print(f"\n*** SUCCESS! Connection '{connection_name}' injected successfully. ***")
            print(f"Response: {r_add.text}")
        else:
            print(f"Error: Injection failed (HTTP {r_add.status_code}):", r_add.text)
            sys.exit(1)
    except Exception as e:
        print("Error injecting connection:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
