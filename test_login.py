import requests

url = "http://127.0.0.1:8000/api/auth/login"
data = {
    "username": "test@email.com",
    "password": "dcastillo2009"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error connecting to backend: {e}")
