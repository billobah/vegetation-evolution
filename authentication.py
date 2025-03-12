# Import Libraries
import requests


def authenticate(user_name, token_value, login_url):
    payload = {"username": user_name, "token": token_value}
    r = requests.post(url=login_url, json=payload)
    r.raise_for_status()
    print("Authentifaction réussie")
    resp = r.json()
    return resp["data"]
