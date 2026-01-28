# chzzk-python

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

치지직(CHZZK) 스트리밍 플랫폼을 위한 비공식 Python SDK

[English](README.md)

## 설치

```bash
# uv 사용 (권장)
uv add chzzk-python

# pip 사용
pip install chzzk-python
```

### CLI 설치

```bash
# uv 사용 (권장)
uv add "chzzk-python[cli]"

# pip 사용
pip install "chzzk-python[cli]"
```

## 빠른 시작

```python
from chzzk import ChzzkClient, FileTokenStorage

# OAuth를 지원하는 클라이언트 생성
client = ChzzkClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8080/callback",
    token_storage=FileTokenStorage("token.json"),
)

# 인증 URL 생성
auth_url, state = client.get_authorization_url()
# 사용자가 auth_url을 방문하여 앱을 승인

# 코드를 토큰으로 교환 (OAuth 콜백 후)
token = client.authenticate(code="auth-code", state=state)

# API 사용
user = client.user.get_me()
print(f"채널: {user.channel_name}")
```

## API 카테고리 및 구현 현황

| 카테고리 | 상태 | 설명 |
|---------|------|------|
| **Authorization** | ✅ 구현됨 | OAuth 2.0, 토큰 발급/갱신/취소 |
| **User** | ✅ 구현됨 | 로그인 사용자 정보 조회 |
| **Channel** | ✅ 구현됨 | 채널 정보, 매니저, 팔로워, 구독자 |
| **Category** | ✅ 구현됨 | 카테고리 검색 |
| **Live** | ✅ 구현됨 | 라이브 목록, 스트림 키, 방송 설정 |
| **Chat** | ✅ 구현됨 | 메시지 전송, 공지, 채팅 설정 |
| **Session** | ✅ 구현됨 | 세션 생성/조회, 이벤트 구독 |
| **Restriction** | ✅ 구현됨 | 활동 제한 목록 관리 |
| **Drops** | ❌ 미구현 | - |
| **Webhook Event** | ❌ 미구현 | - |

> 터미널에서 빠르게 사용할 수 있는 [CLI](#커맨드-라인-인터페이스-cli)도 제공됩니다.

## 주요 기능

### 동기/비동기 지원

동기 및 비동기 클라이언트 모두 사용 가능합니다:

```python
# 동기
from chzzk import ChzzkClient

with ChzzkClient(client_id="...", client_secret="...") as client:
    user = client.user.get_me()

# 비동기
from chzzk import AsyncChzzkClient

async with AsyncChzzkClient(client_id="...", client_secret="...") as client:
    user = await client.user.get_me()
```

### 토큰 저장소

다양한 토큰 저장 옵션:

```python
from chzzk import InMemoryTokenStorage, FileTokenStorage, CallbackTokenStorage

# 메모리 저장 (기본값)
storage = InMemoryTokenStorage()

# 파일 기반 저장
storage = FileTokenStorage("token.json")

# 커스텀 콜백
storage = CallbackTokenStorage(
    get_callback=lambda: load_from_db(),
    save_callback=lambda token: save_to_db(token),
    delete_callback=lambda: delete_from_db(),
)
```

### 실시간 이벤트

채팅, 후원, 구독 이벤트를 실시간으로 수신:

```python
from chzzk import ChzzkClient, ChatEvent, DonationEvent, SubscriptionEvent

client = ChzzkClient(...)
event_client = client.create_event_client()

@event_client.on_chat
def on_chat(event: ChatEvent):
    print(f"{event.profile.nickname}: {event.content}")

@event_client.on_donation
def on_donation(event: DonationEvent):
    print(f"{event.donator_nickname}님이 {event.pay_amount}원 후원")

@event_client.on_subscription
def on_subscription(event: SubscriptionEvent):
    print(f"{event.subscriber_nickname}님이 구독!")

# 연결 및 구독
event_client.connect()
event_client.subscribe_chat()
event_client.subscribe_donation()
event_client.subscribe_subscription()
event_client.run_forever()
```

## 사용 예제

### OAuth 인증 플로우

```python
from chzzk import ChzzkClient, FileTokenStorage

client = ChzzkClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8080/callback",
    token_storage=FileTokenStorage("token.json"),
    auto_refresh=True,  # 만료된 토큰 자동 갱신
)

# 1. 인증 URL 생성
auth_url, state = client.get_authorization_url()
print(f"방문: {auth_url}")

# 2. 사용자 승인 후, 코드를 토큰으로 교환
token = client.authenticate(code="received-code", state=state)

# 3. 필요시 수동으로 토큰 갱신
new_token = client.refresh_token()

# 4. 로그아웃 시 토큰 취소
client.revoke_token()
```

### 채널 및 라이브 정보

```python
# 채널 정보 조회
channel = client.channel.get_channel("channel-id")
print(f"채널: {channel.channel_name}")
print(f"설명: {channel.channel_description}")

# 팔로워 조회
followers = client.channel.get_followers(size=20)
for follower in followers.data:
    print(f"팔로워: {follower.nickname}")

# 라이브 방송 목록 조회
lives = client.live.get_lives(size=10)
for live in lives.data:
    print(f"{live.channel_name}: {live.live_title} ({live.concurrent_user_count}명 시청)")

# 라이브 설정 조회/수정
setting = client.live.get_setting()
client.live.update_setting(default_live_title="나의 방송 제목")
```

### 채팅 메시지

```python
# 채팅 메시지 전송
client.chat.send_message(channel_id="channel-id", message="안녕하세요!")

# 채팅 공지 설정
client.chat.set_notice(
    channel_id="channel-id",
    message="방송에 오신 것을 환영합니다!",
)

# 채팅 설정 조회/수정
settings = client.chat.get_settings(channel_id="channel-id")
client.chat.update_settings(
    channel_id="channel-id",
    chat_available_group="FOLLOWER",
)
```

### 비동기 예제

```python
import asyncio
from chzzk import AsyncChzzkClient, FileTokenStorage

async def main():
    async with AsyncChzzkClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
        redirect_uri="http://localhost:8080/callback",
        token_storage=FileTokenStorage("token.json"),
    ) as client:
        # 사용자 정보 조회
        user = await client.user.get_me()
        print(f"채널: {user.channel_name}")

        # 라이브 방송 목록 조회
        lives = await client.live.get_lives(size=10)
        for live in lives.data:
            print(f"{live.channel_name}: {live.live_title}")

asyncio.run(main())
```

## 예외 처리

```python
from chzzk import (
    ChzzkError,              # 기본 예외
    ChzzkAPIError,           # API 오류 응답
    AuthenticationError,     # 401 오류
    InvalidTokenError,       # 유효하지 않거나 만료된 토큰
    InvalidClientError,      # 유효하지 않은 클라이언트 자격 증명
    ForbiddenError,          # 403 오류
    NotFoundError,           # 404 오류
    RateLimitError,          # 429 오류
    ServerError,             # 5xx 오류
    TokenExpiredError,       # 토큰 만료, 재인증 필요
    InvalidStateError,       # OAuth state 불일치
    SessionError,            # 세션 관련 오류
    SessionConnectionError,  # Socket.IO 연결 실패
    SessionLimitExceededError,  # 최대 세션 수 초과
    EventSubscriptionError,  # 이벤트 구독 실패
)

try:
    user = client.user.get_me()
except InvalidTokenError:
    # 토큰이 유효하지 않거나 만료됨
    token = client.refresh_token()
except RateLimitError:
    # 요청 한도 초과, 대기 후 재시도
    time.sleep(60)
except ChzzkAPIError as e:
    print(f"API 오류: [{e.status_code}] {e.error_code}: {e.message}")
```

## 비공식 API (Unofficial API)

공식 API 외에도 네이버 쿠키 인증을 통한 비공식 API를 제공합니다.
이를 통해 실시간 채팅 수신/전송이 가능합니다.

> ⚠️ 비공식 API는 언제든 변경될 수 있으며, 공식적으로 지원되지 않습니다.

### 비공식 채팅 클라이언트

**동기 버전:**

```python
from chzzk.unofficial import UnofficialChatClient, ChatMessage

chat = UnofficialChatClient(
    nid_aut="your-nid-aut-cookie",
    nid_ses="your-nid-ses-cookie",
)

@chat.on_chat
def on_chat(msg: ChatMessage):
    print(f"{msg.nickname}: {msg.content}")

@chat.on_donation
def on_donation(msg):
    print(f"{msg.nickname} donated {msg.pay_amount}won")

chat.connect("channel-id")
chat.send_message("안녕하세요!")
chat.run_forever()
```

**비동기 버전:**

```python
from chzzk.unofficial import AsyncUnofficialChatClient, ChatMessage

async with AsyncUnofficialChatClient(
    nid_aut="your-nid-aut-cookie",
    nid_ses="your-nid-ses-cookie",
) as chat:
    @chat.on_chat
    async def on_chat(msg: ChatMessage):
        print(f"{msg.nickname}: {msg.content}")

    await chat.connect("channel-id")
    await chat.send_message("안녕하세요!")
    await chat.run_forever()
```

### 네이버 쿠키 획득 방법

1. 네이버에 로그인
2. 브라우저 개발자 도구 (F12) → Application → Cookies
3. `NID_AUT`와 `NID_SES` 쿠키 값 복사

### 비공식 API 예외 처리

```python
from chzzk import ChatConnectionError, ChatNotLiveError

try:
    chat.connect("channel-id")
except ChatNotLiveError:
    print("채널이 현재 라이브 중이 아닙니다")
except ChatConnectionError as e:
    print(f"연결 실패: {e}")
```

## 커맨드 라인 인터페이스 (CLI)

비공식 API 기능을 빠르게 사용할 수 있는 CLI를 제공합니다.

### 인증

```bash
# 네이버 QR 코드로 로그인 (권장)
chzzk auth qr

# 타임아웃 설정과 함께 QR 코드 로그인
chzzk auth qr --timeout 60

# 네이버 쿠키 수동 저장 (대화형)
chzzk auth login

# 인증 상태 확인
chzzk auth status

# 저장된 쿠키 삭제
chzzk auth logout
```

쿠키는 `~/.chzzk/cookies.json`에 저장됩니다.

### 라이브 상태

```bash
# 상세 라이브 정보 조회
chzzk live info CHANNEL_ID

# 단순 LIVE/OFFLINE 상태 조회
chzzk live status CHANNEL_ID

# JSON 형식 출력
chzzk --json live info CHANNEL_ID
```

### 채팅

```bash
# 실시간 채팅 보기
chzzk chat watch CHANNEL_ID

# 오프라인 상태에서도 채팅 보기
chzzk chat watch CHANNEL_ID --offline

# 채팅을 파일로 저장
chzzk chat watch CHANNEL_ID --output chat.jsonl
chzzk chat watch CHANNEL_ID --output chat.txt --output-format txt

# 방송 정보 기반 자동 파일명 생성 (권장)
# 생성 형식: {channel_id}_{live_id}_{YYYYMMDD}.jsonl
chzzk chat watch CHANNEL_ID --output-dir ./logs

# 단일 메시지 전송 (인증 필요)
chzzk chat send CHANNEL_ID "안녕하세요!"

# 오프라인 채널에 전송
chzzk chat send CHANNEL_ID "안녕하세요!" --offline

# 대화형 모드: 메시지 송수신
chzzk chat send CHANNEL_ID --interactive
# 또는
chzzk chat send CHANNEL_ID -i

# 대화형 모드에서 채팅 로그 저장
chzzk chat send CHANNEL_ID -i --output-dir ./logs

# 오프라인 채널에서 대화형 모드
chzzk chat send CHANNEL_ID -i --offline
```

### 전역 옵션

```bash
--nid-aut TEXT      # NID_AUT 쿠키 오버라이드 (환경변수: CHZZK_NID_AUT)
--nid-ses TEXT      # NID_SES 쿠키 오버라이드 (환경변수: CHZZK_NID_SES)
--json              # JSON 형식으로 출력
--log-level LEVEL   # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR)
```

### 환경 변수

| 변수 | 설명 |
|-----|------|
| `CHZZK_NID_AUT` | NID_AUT 쿠키 값 |
| `CHZZK_NID_SES` | NID_SES 쿠키 값 |
| `CHZZK_LOG_LEVEL` | 기본 로그 레벨 |
| `CHZZK_CHAT_OUTPUT` | 기본 채팅 출력 파일 경로 |
| `CHZZK_CHAT_OUTPUT_DIR` | 기본 채팅 출력 디렉토리 (파일명 자동 생성) |
| `CHZZK_CHAT_OUTPUT_FORMAT` | 기본 채팅 출력 형식 (jsonl, txt) |

## 예제 코드

완전한 작동 예제는 [examples](examples/) 디렉토리를 참조하세요:

- `oauth_server.py` - Flask를 사용한 OAuth 인증
- `realtime_chat.py` - 실시간 채팅/후원/구독 이벤트 (동기)
- `realtime_chat_async.py` - 실시간 이벤트 (비동기)
- `session_management.py` - 세션 관리 예제
- `unofficial_chat.py` - 비공식 채팅 클라이언트 (동기)
- `unofficial_chat_async.py` - 비공식 채팅 클라이언트 (비동기)

## API 문서

자세한 API 문서는 [공식 치지직 API 문서](https://chzzk.gitbook.io/chzzk)를 참조하세요.

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여

기여를 환영합니다! Pull Request를 자유롭게 제출해 주세요.

## 면책 조항

이것은 비공식 SDK이며 NAVER 또는 치지직과 제휴되어 있지 않습니다. 사용에 따른 책임은 사용자에게 있습니다.
