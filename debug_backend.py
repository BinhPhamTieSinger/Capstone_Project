
import requests
import json

def test_chat(message):
    url = "http://localhost:8003/chat"
    payload = {
        "message": message,
        "thread_id": "debug_test_1"
    }
    try:
        print(f"Sending: {message}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(data, indent=2)}")
        return data.get("response", "")
    except Exception as e:
        print(f"Error: {e}")
        if response:
             print(f"Response Content: {response.text}")

print("--- TEST 1: Chart ---")
chart_resp = test_chat("Demo me a line chart.")

print("\n--- TEST 2: Web Search ---")
search_resp = test_chat("Search web for me about Gradient Descent give me the exact link")
