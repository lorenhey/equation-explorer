import os
import json
import requests
import urllib.request
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set.")
        return

    # Read public key
    with open(".git/deploy_key.pub", "r") as f:
        pub_key = f.read().strip()

    repo_name = "equation-explorer"
    
    proxies = urllib.request.getproxies()

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-Deployer"
    }

    # 1. Create Repo
    print("Creating repo...")
    create_repo_url = "https://api.github.com/user/repos"
    create_repo_data = {
        "name": repo_name,
        "private": False,
        "description": "A computable mathematical knowledge graph for exploring and solving physics equations."
    }
    
    try:
        response = requests.post(create_repo_url, json=create_repo_data, headers=headers, proxies=proxies, verify=False)
        if response.status_code == 201:
            print("Repo created successfully.")
        elif response.status_code == 422 and "name already exists" in response.text:
            print("Repo already exists, continuing...")
        else:
            print(f"Failed to create repo: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Exception during create repo: {e}")
        return
            
    # 2. Upload Deploy Key
    print("Uploading deploy key...")
    add_key_url = f"https://api.github.com/repos/lorenhey/{repo_name}/keys"
    add_key_data = {
        "title": "Antigravity Deploy Key",
        "key": pub_key,
        "read_only": False
    }
    
    try:
        response2 = requests.post(add_key_url, json=add_key_data, headers=headers, proxies=proxies, verify=False)
        if response2.status_code == 201:
            print("Deploy key added successfully.")
        elif response2.status_code == 422 and "key is already in use" in response2.text:
            print("Key already exists, continuing...")
        else:
            print(f"Failed to add key: {response2.status_code} - {response2.text}")
    except Exception as e:
        print(f"Exception during add key: {e}")

if __name__ == "__main__":
    main()
