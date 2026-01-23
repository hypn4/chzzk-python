# Chzzk 비공식 채팅 WebSocket 프로토콜 분석

> 최종 업데이트: 2026-01-23
> 분석 방법: Chrome DevTools WebSocket 메시지 캡처

## 개요

치지직(Chzzk) 라이브 채팅은 WebSocket을 통해 실시간으로 메시지를 주고받습니다. 이 문서는 브라우저에서 캡처한 실제 WebSocket 메시지를 기반으로 프로토콜 구조를 정리한 것입니다.

---

## 용어 정리

| 용어 | 설명 | 예시 |
|------|------|------|
| `channelId` (스트리밍) | 스트리머의 채널 ID. 방송 URL에 포함됨 | `14f67c97d654f655afc0c9b3********` |
| `cid` (채팅) | 채팅 채널 ID. live-detail API에서 획득 | `N2FOy2` |
| `sid` (세션) | WebSocket 세션 ID. CONNECTED 응답에서 획득 | `S9g51s_L99y1f_qm4yfhMCdDV6Vxoi...` |
| `uid` | 사용자 ID 해시. getUserStatus API에서 획득 | `14f67c97d654f655afc0c9b3********` |
| `accTkn` | 채팅 액세스 토큰. access-token API에서 획득 | `EcXl9izPI9otGQ5yUr1i0wWLKH******` |
| `extraToken` | 추가 토큰. access-token API에서 획득 (채팅 전송 시 필요) | `uyZcBSQyl3OVq/hVGsuwTCh2Qm******` |

---

## 프로토콜 버전

- **현재 버전**: `"3"`
- 모든 메시지의 `ver` 필드에 프로토콜 버전을 명시해야 함

---

## 명령어 코드 (cmd)

| 코드 | 이름 | 방향 | 설명 |
|------|------|------|------|
| `0` | PING | Server → Client | 서버에서 보내는 핑 |
| `10000` | PONG | Client → Server | 클라이언트의 퐁 응답 |
| `100` | CONNECT | Client → Server | 연결 요청 |
| `10100` | CONNECTED | Server → Client | 연결 완료 응답 |
| `3101` | SEND_CHAT | Client → Server | 채팅 메시지 전송 |
| `5101` | REQUEST_RECENT_CHAT | Client → Server | 최근 채팅 요청 |
| `15101` | RECENT_CHAT | Server → Client | 최근 채팅 응답 |
| `93101` | CHAT | Server → Client | 실시간 채팅 메시지 |
| `93102` | DONATION | Server → Client | 후원 메시지 |
| `93006` | EVENT | Server → Client | 이벤트 메시지 |
| `94005` | KICK | Server → Client | 강제퇴장 |
| `94006` | BLOCK | Server → Client | 차단 |
| `94008` | BLIND | Server → Client | 블라인드 처리 |
| `94010` | NOTICE | Server → Client | 공지 |
| `94015` | PENALTY | Server → Client | 제재 |

---

## 메시지 구조

### 1. PONG (cmd: 10000)

서버의 PING에 대한 응답.

```json
{
  "ver": "3",
  "cmd": 10000
}
```

### 2. CONNECT (cmd: 100)

WebSocket 연결 후 인증 요청.

```json
{
  "ver": "3",
  "cmd": 100,
  "svcid": "game",
  "cid": "N2FOy2",
  "bdy": {
    "uid": "14f67c97d654f655afc0c9b3********",
    "devType": 2001,
    "accTkn": "EcXl9izPI9otGQ5yUr1i0wWLKHqfPCFTsn/hV+Ec5b5jmyEiTDARbYOZ8OxYGkjq****************",
    "auth": "SEND"
  },
  "tid": 1
}
```

**필드 설명:**
- `svcid`: 서비스 ID (항상 `"game"`)
- `cid`: 채팅 채널 ID
- `bdy.uid`: 사용자 ID 해시 (메시지 전송 시 필수)
- `bdy.devType`: 디바이스 타입 (`2001` = PC)
- `bdy.accTkn`: 채팅 액세스 토큰
- `bdy.auth`: 인증 모드 (`"SEND"` = 전송 가능, `"READ"` = 읽기 전용)
- `tid`: 트랜잭션 ID

### 3. CONNECTED (cmd: 10100)

연결 완료 응답. **중요: `sid`를 저장해야 함.**

```json
{
  "ver": "3",
  "cmd": 10100,
  "bdy": {
    "sid": "S9g51s_L99y1f_qm4yfhMCdDV6VxoiPz!fqyXd_8tXFYKo!Qa_War3NOEcVK!84Y7Scugt3t********"
  }
}
```

**중요**: `bdy.sid`를 저장하여 이후 채팅 전송 시 사용해야 합니다.

### 4. REQUEST_RECENT_CHAT (cmd: 5101)

최근 채팅 메시지 요청.

```json
{
  "ver": "3",
  "cmd": 5101,
  "svcid": "game",
  "cid": "N2FOy2",
  "sid": 1,
  "bdy": {
    "recentMessageCount": 50
  },
  "tid": 3
}
```

**참고**: 이 요청의 `sid`는 세션 ID가 아닌 숫자 `1`입니다.

### 5. SEND_CHAT (cmd: 3101) - 핵심

채팅 메시지 전송. **가장 중요한 메시지 구조.**

```json
{
  "ver": "3",
  "cmd": 3101,
  "svcid": "game",
  "cid": "N2FOy2",
  "sid": "S9g51s_L99y1f_qm4yfhMCdDV6VxoiPz!fqyXd_8tXFYKo!Qa_War3NOEcVK!84Y7Scugt3t********",
  "retry": false,
  "bdy": {
    "msg": "메시지 내용",
    "msgTypeCode": 1,
    "extras": "{\"chatType\":\"STREAMING\",\"osType\":\"PC\",\"extraToken\":\"uyZcBSQyl3OVq/hVGsuwTCh2Qm+RMtLIY0+FqBimmo1D2KWUKNlzCbrXxR81QZ8Vx5yIqW4oaz9u********\",\"streamingChannelId\":\"14f67c97d654f655afc0c9b3********\",\"emojis\":{}}",
    "msgTime": 1769139665965
  },
  "tid": 6
}
```

**필드 설명:**
- `sid`: CONNECTED 응답에서 받은 세션 ID 문자열 (숫자 아님!)
- `retry`: 재시도 여부
- `bdy.msg`: 메시지 내용
- `bdy.msgTypeCode`: 메시지 타입 (`1` = 일반 텍스트)
- `bdy.extras`: JSON 문자열로 인코딩된 추가 데이터
- `bdy.msgTime`: 밀리초 단위 타임스탬프

**extras 필드 상세 (JSON 파싱 후):**

```json
{
  "chatType": "STREAMING",
  "osType": "PC",
  "extraToken": "uyZcBSQyl3OVq/hVGsuwTCh2Qm+RMtLIY0+FqBimmo1D2KWUKNlzCbrXxR81QZ8Vx5yIqW4oaz9u********",
  "streamingChannelId": "14f67c97d654f655afc0c9b3********",
  "emojis": {}
}
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `chatType` | O | 채팅 타입 (`"STREAMING"`) |
| `osType` | O | OS 타입 (`"PC"`, `"MOBILE"` 등) |
| `extraToken` | O | access-token API에서 받은 `extraToken` |
| `streamingChannelId` | O | 스트리밍 채널 ID (connect 시 사용한 원래 channel ID) |
| `emojis` | X | 이모지 데이터 (빈 객체 가능) |

---

## 채팅 전송 플로우

```
1. live-detail API 호출
   └─> chatChannelId 획득 (예: "N2FOy2")

2. access-token API 호출 (channelId, chatType=STREAMING)
   └─> accessToken, extraToken 획득

3. getUserStatus API 호출
   └─> userIdHash 획득 (uid로 사용)

4. WebSocket 연결
   └─> wss://kr-ss1.chat.naver.com/chat

5. CONNECT 메시지 전송 (cmd: 100)
   └─> uid, accTkn, auth="SEND" 포함

6. CONNECTED 응답 수신 (cmd: 10100)
   └─> bdy.sid 저장 (중요!)

7. 채팅 전송 시 SEND_CHAT 메시지 (cmd: 3101)
   └─> sid (세션 ID 문자열)
   └─> extras에 extraToken, streamingChannelId 포함
   └─> msgTime에 현재 시간(ms) 포함
```

---

## API 엔드포인트

### access-token API

```
GET https://api.chzzk.naver.com/service/v3/channel/{channelId}/chat/access-token
```

**Query Parameters:**
- `channelId`: 스트리밍 채널 ID
- `chatType`: `STREAMING`

**Response:**
```json
{
  "code": 200,
  "content": {
    "accessToken": "EcXl9izPI9otGQ5yUr1i0wWLKH******",
    "extraToken": "uyZcBSQyl3OVq/hVGsuwTCh2Qm******",
    "realNameAuth": false,
    "temporaryRestrict": null
  }
}
```

### getUserStatus API

```
GET https://api.chzzk.naver.com/service/v1/user/status
```

**Response:**
```json
{
  "code": 200,
  "content": {
    "loggedIn": true,
    "userIdHash": "14f67c97d654f655afc0c9b3********",
    ...
  }
}
```

---

## 주의사항

1. **프로토콜 버전**: 모든 메시지에 `"ver": "3"` 사용
2. **세션 ID**: CONNECTED 응답의 `sid`는 문자열이며, SEND_CHAT에서 반드시 사용해야 함
3. **extras**: JSON 문자열로 인코딩하여 전송
4. **extraToken**: 채팅 전송 시 반드시 포함해야 함
5. **msgTime**: 밀리초 단위의 현재 타임스탬프 사용

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-23 | 최초 작성. Chrome DevTools WebSocket 캡처 기반 프로토콜 분석 |
