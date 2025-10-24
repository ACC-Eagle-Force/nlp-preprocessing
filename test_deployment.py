#!/usr/bin/env python3
"""
Deployment verification script for ACC API
Run this to test your API before deploying to Render
"""

import requests
import json
import sys

def test_api(base_url="http://localhost:5000"):
    """Test all API endpoints"""
    print(f"Testing ACC API at {base_url}")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test parse endpoint
    try:
        test_data = {"text": "CSC101 assignment due tomorrow at 3pm"}
        response = requests.post(
            f"{base_url}/parse",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "CSC101" in data.get("data", {}).get("courses", []):
                print("✅ Parse endpoint working")
            else:
                print(f"❌ Parse endpoint returned unexpected data: {data}")
                return False
        else:
            print(f"❌ Parse endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Parse endpoint error: {e}")
        return False
    
    # Test batch endpoint
    try:
        test_data = {"texts": ["CSC101 exam tomorrow", "MATH201 assignment due Friday"]}
        response = requests.post(
            f"{base_url}/parse/batch",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and len(data.get("data", {}).get("results", [])) == 2:
                print("✅ Batch parse endpoint working")
            else:
                print(f"❌ Batch parse endpoint returned unexpected data: {data}")
                return False
        else:
            print(f"❌ Batch parse endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Batch parse endpoint error: {e}")
        return False
    
    print("\n🎉 All tests passed! Ready for deployment.")
    return True

if __name__ == "__main__":
    # Allow testing against different URLs
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    if test_api(base_url):
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Fix issues before deploying.")
        sys.exit(1)
