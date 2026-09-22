import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ELEVAR_NEWS = "https://elevartx.com/news/"
STATE_FILE = "state.json"

DRUG_TERMS = [
    "lirafugratinib",
    "rly-4008",
]

RESULT_TERMS = [
    "fda",
    "approved",
    "approval",
    "complete response letter",
    "crl",
    "pdufa",
    "action date",
    "decision",
    "delay",
    "delayed",
    "refuse to approve",
    "refusal",
]

HEADERS = {
    "User-Agent": "HLB-FDA-Kakao-Alert/1.0 (+https://elevartx.com/news/)"
}

def fetch_news():
    r = requests.get(ELEVAR_NEWS, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    candidates = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = urljoin(ELEVAR_NEWS, a["href"])
        title = " ".join(a.get_text(" ", strip=True).split())
        if not title or href in seen:
            continue
        if "elevartx.com" not in href:
            continue
        seen.add(href)

        # Focus on press-release-like pages.
        if "/2026/" not in href and "/2025/" not in href:
            continue

        candidates.append((title, href))

    return candidates

def is_relevant(title, url):
    hay = f"{title} {url}".lower()
    return (
        any(t in hay for t in DRUG_TERMS)
        and any(t in hay for t in RESULT_TERMS)
    )

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_alerted_url": ""}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def refresh_access_token():
    refresh = os.environ["KAKAO_REFRESH_TOKEN"]
    key = os.environ["KAKAO_REST_API_KEY"]
    secret = os.environ["KAKAO_CLIENT_SECRET"]

    r = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": key,
            "refresh_token": refresh,
            "client_secret": secret,
        },
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()

    # If Kakao rotates the refresh token, print it so the GitHub secret can
    # be updated. In the current short-lived monitoring window this is usually
    # not needed, but the code handles the response safely.
    if data.get("refresh_token"):
        print("NEW_REFRESH_TOKEN=" + data["refresh_token"])

    return data["access_token"]

def send_kakao(title, url):
    token = refresh_access_token()
    template = {
        "object_type": "text",
        "text": (
            "🚨 HLB 리라푸그라티닙 FDA 결과 감지\n\n"
            f"{title}\n\n"
            "출처: Elevar Therapeutics 공식 뉴스룸\n"
            f"{url}\n\n"
            "※ 자동 감지 알림입니다. 원문을 확인하세요."
        ),
        "link": {
            "web_url": url,
            "mobile_web_url": url,
        },
        "button_title": "공식 발표 보기",
    }

    r = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        send_kakao(
            "테스트: HLB 리라푸그라티닙 알림 시스템 정상 작동 확인",
            "https://elevartx.com/news/",
        )
        print("Kakao test sent.")
        return

    state = load_state()
    last = state.get("last_alerted_url", "")

    candidates = fetch_news()

    # The page is normally newest-first. Check all relevant posts so that a
    # delayed workflow run does not miss the result.
    relevant = [(t, u) for t, u in candidates if is_relevant(t, u)]

    if not relevant:
        print("No relevant FDA-result release found.")
        return

    # Alert only the newest relevant URL not yet seen.
    title, url = relevant[0]
    if url == last:
        print("Already alerted:", url)
        return

    send_kakao(title, url)
    state["last_alerted_url"] = url
    state["last_alerted_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print("ALERTED:", title, url)

if __name__ == "__main__":
    main()
