"""
Test script for TraceFlow REST API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_get_accounts():
    print("\n=== Testing GET /api/accounts/ ===")
    response = requests.get(f"{BASE_URL}/accounts/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} accounts")
        if data:
            print(f"First account: {data[0]['name']} (Type: {data[0]['account_type']})")
    else:
        print(f"Error: {response.text}")

def test_get_transactions():
    print("\n=== Testing GET /api/transactions/ ===")
    response = requests.get(f"{BASE_URL}/transactions/?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} transactions")
        if data:
            print(f"First transaction: ${data[0]['amount']} on {data[0]['transaction_date']}")
    else:
        print(f"Error: {response.text}")

def test_reconciliation_stats():
    print("\n=== Testing GET /api/reconciliation/stats/ ===")
    response = requests.get(f"{BASE_URL}/reconciliation/stats/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total matches: {data['total_matches']}")
        print(f"Match rate: {data['match_rate']:.1f}%")
        print(f"Match types: {data['match_types']}")
    else:
        print(f"Error: {response.text}")

def test_summary_stats():
    print("\n=== Testing GET /api/stats/summary/ ===")
    response = requests.get(f"{BASE_URL}/stats/summary/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Bank transactions: {data['bank_transactions']}")
        print(f"Book entries: {data['book_entries']}")
        print(f"Matches: {data['matches']}")
        print(f"Unreconciled: {data['unreconciled_transactions']}")
    else:
        print(f"Error: {response.text}")

def test_create_account():
    print("\n=== Testing POST /api/accounts/ ===")
    new_account = {
        "name": "API Test Account",
        "account_type": "BANK",
        "account_number": "TEST-12345",
        "description": "Created via REST API"
    }
    response = requests.post(f"{BASE_URL}/accounts/", json=new_account)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Created account ID: {data['id']}")
        return data['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_delete_account(account_id):
    if account_id:
        print(f"\n=== Testing DELETE /api/accounts/{account_id}/ ===")
        response = requests.delete(f"{BASE_URL}/accounts/{account_id}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Result: {data['message']}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("TraceFlow REST API Test Suite")
    print("=" * 60)
    
    try:
        # Read-only tests
        test_get_accounts()
        test_get_transactions()
        test_reconciliation_stats()
        test_summary_stats()
        
        # Write tests
        account_id = test_create_account()
        test_delete_account(account_id)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API. Make sure the server is running at http://127.0.0.1:8000")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
