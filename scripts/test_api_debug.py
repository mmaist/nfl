1#!/usr/bin/env python3
"""
Debug script to test API authentication.
"""
import os
from dotenv import load_dotenv
import requests
import subprocess

# Load environment variables
load_dotenv()

def test_with_curl():
    """Test with curl to verify it works"""
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        print("ERROR: BEARER_TOKEN not found in .env file")
        return
        
    print("Testing with curl...")
    print(f"Bearer token length: {len(bearer_token)}")
    print(f"Bearer token preview: {bearer_token[:20]}...{bearer_token[-10:]}")
    cmd = [
        'curl', '-s', '-X', 'GET',
        'https://pro.nfl.com/api/secured/videos/filmroom/plays?season=2024&seasonType=REG&weekSlug=WEEK_1&gameId=7d403a46-1312-11ef-afd1-646009f18b2e',
        '-H', f'Authorization: Bearer {bearer_token}',
        '-H', 'Accept: application/json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Curl status code: {result.returncode}")
    if result.returncode == 0:
        print(f"Curl response (first 200 chars): {result.stdout[:200]}...")
    else:
        print(f"Curl error: {result.stderr}")

def test_with_requests():
    """Test with requests library"""
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        print("ERROR: BEARER_TOKEN not found in .env file")
        return
        
    print("\n\nTesting with requests library...")
    
    url = "https://pro.nfl.com/api/secured/videos/filmroom/plays"
    params = {
        "season": "2024",
        "seasonType": "REG", 
        "weekSlug": "WEEK_1",
        "gameId": "7d403a46-1312-11ef-afd1-646009f18b2e"
    }
    
    # Try different header combinations
    header_variants = [
        {
            "name": "Basic headers",
            "headers": {
                "Authorization": f"Bearer {bearer_token}",
                "Accept": "application/json"
            }
        },
        {
            "name": "With User-Agent",
            "headers": {
                "Authorization": f"Bearer {bearer_token}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        },
        {
            "name": "Full browser headers",
            "headers": {
                "Authorization": f"Bearer {bearer_token}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        }
    ]
    
    for variant in header_variants:
        print(f"\n{variant['name']}:")
        try:
            response = requests.get(url, params=params, headers=variant['headers'])
            print(f"Status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            if response.status_code == 200:
                print(f"Success! Response (first 200 chars): {response.text[:200]}...")
                break
            else:
                print(f"Error response: {response.text[:300]}...")
        except Exception as e:
            print(f"Exception: {e}")

def test_session():
    """Test with requests Session (like in the scraper)"""
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        print("ERROR: BEARER_TOKEN not found in .env file")
        return
        
    print("\n\nTesting with requests Session...")
    
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    
    session = requests.Session()
    retries = Retry(total=5,
                   backoff_factor=0.1,
                   status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    url = "https://pro.nfl.com/api/secured/videos/filmroom/plays"
    params = {
        "season": 2024,
        "seasonType": "REG",
        "weekSlug": "WEEK_1",
        "gameId": "7d403a46-1312-11ef-afd1-646009f18b2e"
    }
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = session.get(url, params=params, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Response (first 200 chars): {response.text[:200]}...")
        else:
            print(f"Error response: {response.text[:300]}...")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_with_curl()
    test_with_requests()
    test_session()