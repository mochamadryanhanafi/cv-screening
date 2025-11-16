import os
import requests


def test_groq_call():
    api_key = os.getenv('GROQ_API_KEY')
    api_url = os.getenv('GROQ_API_URL')
    model = os.getenv('GROQ_MODEL')
    if not (api_key and api_url and model):
        print('GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL must be set in environment or .env')
        return

    url = f"{api_url.rstrip('/')}/{model}/completions"
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {"prompt": "Say hello in one sentence.", "max_tokens": 16}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print('Status:', resp.status_code)
        print('Response:', resp.text)
    except Exception as e:
        print('Error calling Groq:', e)


if __name__ == '__main__':
    test_groq_call()
