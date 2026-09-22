import http.server
import json
import os
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs, urlencode
import requests

REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "").strip()
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "").strip()
REDIRECT_URI = "http://localhost:8000/callback"
TOKEN_FILE = "kakao_token.json"

if not REST_API_KEY:
    REST_API_KEY = input("Kakao REST API Key: ").strip()
if not CLIENT_SECRET:
    CLIENT_SECRET = input("Kakao Client Secret: ").strip()

result = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        qs = parse_qs(parsed.query)
        result["code"] = qs.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("인증 완료. 이 창을 닫아도 됩니다.".encode("utf-8"))

    def log_message(self, fmt, *args):
        pass

server = http.server.HTTPServer(("localhost", 8000), Handler)
threading.Thread(target=server.handle_request, daemon=True).start()

params = {
    "client_id": REST_API_KEY,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": "talk_message",
}
url = "https://kauth.kakao.com/oauth/authorize?" + urlencode(params)

print("\n브라우저에서 카카오 로그인을 진행합니다.")
print(url)
webbrowser.open(url)

while "code" not in result:
    pass

server.server_close()

resp = requests.post(
    "https://kauth.kakao.com/oauth/token",
    data={
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": result["code"],
        "client_secret": CLIENT_SECRET,
    },
    timeout=20,
)
resp.raise_for_status()
token = resp.json()

with open(TOKEN_FILE, "w", encoding="utf-8") as f:
    json.dump(token, f, ensure_ascii=False, indent=2)

print(f"\n완료: {TOKEN_FILE} 생성")
print("이 파일의 refresh_token 값을 GitHub Secret KAKAO_REFRESH_TOKEN에 넣으세요.")
