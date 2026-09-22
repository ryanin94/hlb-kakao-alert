# HLB 리라푸그라티닙 FDA 결과 → 카카오톡 자동 알림

이 프로젝트는 **Elevar Therapeutics 공식 뉴스룸**을 주기적으로 확인하고,
리라푸그라티닙(lirafugratinib) 관련 FDA 결정으로 보이는 새 발표가 발견되면
**카카오톡 '나에게 보내기'**로 알림을 보내도록 구성되어 있습니다.

## 동작 방식

1. GitHub Actions가 5분 간격으로 실행
2. Elevar 공식 뉴스룸에서 새 글 확인
3. `lirafugratinib`/`RLY-4008` 관련 새 글 중
   `FDA`, `approved`, `approval`, `complete response letter`, `CRL`,
   `PDUFA`, `delay`, `延期` 등의 결과 키워드를 확인
4. 새 결과가 감지되면 카카오톡 '나와의 채팅'으로 알림
5. 이미 알림한 글은 `state.json`에 기록해 중복 알림 방지

> GitHub Actions의 scheduled workflow는 실행 시점이 지연될 수 있습니다.
> 따라서 '정확히 5분마다'가 아니라 대략적인 주기라고 생각하세요.

## 1. 카카오 개발자 앱 만들기

공식 문서:
https://developers.kakao.com/

- 앱 생성
- `카카오 로그인` 활성화
- Redirect URI 등록:
  `http://localhost:8000/callback`
- 동의항목에서 `talk_message` 권한 설정
- REST API 키와 Client Secret 확인

카카오 공식 문서:
https://developers.kakao.com/docs/ko/kakaotalk-message/rest-api

## 2. 로컬에서 최초 인증

Python 3.10+ 권장.

```bash
pip install requests
python kakao_auth.py
```

브라우저에서 카카오 로그인을 완료하면 `kakao_token.json`이 생성됩니다.

그 파일 안의 `refresh_token`을 GitHub Repository Secret에 등록합니다.

Secret 이름:
`KAKAO_REFRESH_TOKEN`

REST API 키:
`KAKAO_REST_API_KEY`

Client Secret:
`KAKAO_CLIENT_SECRET`

## 3. GitHub에 올리기

이 폴더를 GitHub repository에 올립니다.

Repository > Settings > Secrets and variables > Actions에서 다음 3개를 등록:

- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET`
- `KAKAO_REFRESH_TOKEN`

Actions가 repository 내용을 수정할 수 있도록 workflow에 `contents: write` 권한이 포함되어 있습니다.

## 4. 테스트

GitHub의 Actions 탭에서
`HLB FDA Result Kakao Alert`를 선택하고
`Run workflow`를 눌러 수동 실행합니다.

테스트 메시지를 보내려면:

```bash
python monitor.py --test
```

## 주의

- 카카오 REST API 키/Client Secret/Refresh Token을 공개 저장소에 절대 올리지 마세요.
- `kakao_token.json`은 `.gitignore`에 포함되어 있습니다.
- 이 알림기는 투자 판단을 하지 않고 **공식 발표를 감지해 전달**합니다.
- 최초 감지 소스는 Elevar 공식 뉴스룸입니다. FDA와 HLB/DART 발표가 조금 늦게 따라올 수 있으므로 중요한 결정은 원문을 직접 확인하세요.
