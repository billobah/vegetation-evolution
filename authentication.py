# Import Libraries
import requests


def authenticate(user_name, api_key, login_url):
    payload = {"username": user_name, "token": api_key}
    r = requests.post(url=login_url, json=payload)
    r.raise_for_status()
    print("Authentifaction réussie")
    resp = r.json()
    return resp["data"]
