#!/usr/bin/env python
"""
AutiSense API Test Script
Tests authentication and API endpoints with proper token handling.
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    """Test login endpoint and return access token."""
    print("=" * 60)
    print("Testing Login Endpoint")
    print("=" * 60)
    
    login_data = {
        'email': 'demo.admin@autisense.app',
        'password': 'demo1234',
        'role': 'admin'
    }
    
    print(f"Login URL: {BASE_URL}/auth/login")
    print(f"Login data: {json.dumps(login_data, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Extract token from nested structure
            token = data['user']['token']
            print(f"\n[PASS] Login successful! Token: {token[:50]}...")
            return token
        else:
            print(f"[FAIL] Login failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("[FAIL] Connection error: Is the Django server running?")
        print("  Start it with: python manage.py runserver")
        return None
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return None

def test_authenticated_endpoint(endpoint, token, method='GET', data=None):
    """Test an authenticated API endpoint."""
    print("\n" + "=" * 60)
    print(f"Testing {endpoint} Endpoint")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}{endpoint}"
    print(f"URL: {url}")
    print(f"Method: {method}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"[PASS] Success! Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"[FAIL] Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return False

def main():
    """Main test function."""
    print("AutiSense API Test Suite")
    print("=" * 60)
    
    # Step 1: Login
    token = test_login()
    if not token:
        print("\n✗ Tests aborted: Could not obtain authentication token")
        sys.exit(1)
    
    # Step 2: Test various endpoints
    # Note: Some endpoints have different URL patterns
    endpoints_to_test = [
        ('/children/', 'GET', None),
        ('/assessments/', 'GET', None),
        ('/notifications/', 'GET', None),
        ('/messages/conversations', 'GET', None),  # Correct endpoint for conversation list
        ('/schedules/', 'GET', None),
        ('/reports/stats', 'GET', None),  # Correct endpoint for system stats
    ]
    
    results = []
    for endpoint, method, data in endpoints_to_test:
        success = test_authenticated_endpoint(endpoint, token, method, data)
        results.append((endpoint, success))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for endpoint, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {endpoint}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[PASS] All tests passed!")
        sys.exit(0)
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == '__main__':
    main()