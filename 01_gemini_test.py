import os
import socket
from google import genai
from google.genai import types

# Force IPv4 for fast connection
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    if host == "generativelanguage.googleapis.com":
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _ipv4_only

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("API key missing")
    exit()

try:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=10_000)  # 10s hard timeout
    )
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Confirm connection in one short sentence."
    )
    print(response.text)
except Exception as e:
    print(f"API Error: {e}")