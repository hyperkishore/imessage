# iMessage Sender - State Diagrams

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HYBRID ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Phase 1: Local Mode                Phase 2: Distributed Mode          │
│   ┌──────────────────┐               ┌──────────────────────────┐       │
│   │  BDR's Mac       │               │   Central Web Server     │       │
│   │  ┌────────────┐  │               │   ┌──────────────────┐   │       │
│   │  │ Web App    │  │               │   │ Sender Registry  │   │       │
│   │  │ (Flask)    │  │               │   │ - VP's Mac       │   │       │
│   │  ├────────────┤  │               │   │ - Manager's Mac  │   │       │
│   │  │ AppleScript│──┼──► iMessage   │   │ - BDR1's Mac     │   │       │
│   │  └────────────┘  │               │   └────────┬─────────┘   │       │
│   └──────────────────┘               │            │             │       │
│                                      └────────────┼─────────────┘       │
│                                                   │                      │
│                                      ┌────────────▼─────────────┐       │
│                                      │     Message Queue        │       │
│                                      └────────────┬─────────────┘       │
│                                                   │                      │
│                       ┌───────────────────────────┼───────────────┐     │
│                       ▼                           ▼               ▼     │
│               ┌──────────────┐           ┌──────────────┐ ┌──────────┐ │
│               │ VP's Mac     │           │ Manager's Mac│ │ BDR Mac  │ │
│               │ Agent        │           │ Agent        │ │ Agent    │ │
│               └──────────────┘           └──────────────┘ └──────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Local Mode State Diagram

**Use Case**: BDR installs app on their Mac, registers their phone, sends messages.

```
                                    ┌─────────────────┐
                                    │     START       │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │   App Launched on Mac        │
                              │   (First Time Setup)         │
                              └──────────────┬───────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │   SENDER REGISTRATION        │
                              │   ┌────────────────────────┐ │
                              │   │ Enter Your Name        │ │
                              │   │ Enter Your Phone #     │ │
                              │   │ [Verify via iMessage]  │ │
                              │   └────────────────────────┘ │
                              └──────────────┬───────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │   VERIFICATION               │
                              │   - Send test message to self│
                              │   - Confirm phone # works    │
                              └──────────────┬───────────────┘
                                             │
                           ┌─────────────────┴─────────────────┐
                           │                                   │
                           ▼                                   ▼
                    ┌─────────────┐                     ┌─────────────┐
                    │   SUCCESS   │                     │   FAILED    │
                    │   Profile   │                     │   Retry or  │
                    │   Created   │                     │   Fix Setup │
                    └──────┬──────┘                     └─────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │   DASHBOARD / HOME         │
              │   ┌──────────────────────┐ │
              │   │ Sending as:          │ │
              │   │ "John (BDR)"         │ │
              │   │ +1-555-123-4567      │ │
              │   │ [Change Sender ▼]    │ │
              │   └──────────────────────┘ │
              └────────────┬───────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Enter Sheet │ │ Select      │ │ View Sent   │
    │ URL         │ │ Template    │ │ History     │
    └──────┬──────┘ └──────┬──────┘ └─────────────┘
           │               │
           └───────┬───────┘
                   ▼
         ┌─────────────────────┐
         │   PREVIEW MESSAGES  │
         │   - See recipients  │
         │   - Edit messages   │
         │   - Confirm sender  │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   SEND CONFIRMATION │
         │   "Send 25 messages │
         │   from +1-555-xxx?" │
         └──────────┬──────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   ┌─────────────┐     ┌─────────────┐
   │  SENDING    │     │  CANCELLED  │
   │  Progress   │     └─────────────┘
   │  [=====>  ] │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────────┐
   │   RESULTS           │
   │   ✓ 23 sent         │
   │   ✗ 2 failed        │
   │   [View Details]    │
   └─────────────────────┘
```

---

## Phase 2: Distributed Mode State Diagram

**Use Case**: Escalation - Send from leader's phone via their registered Mac.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SENDER SELECTION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  USER LOGS IN   │
                              │  (Any Browser)  │
                              └────────┬────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │     SELECT SENDER            │
                        │  ┌────────────────────────┐  │
                        │  │ Available Senders:     │  │
                        │  │                        │  │
                        │  │ ○ My Phone (local)     │  │
                        │  │   +1-555-BDR-1234      │  │
                        │  │   ✓ Online             │  │
                        │  │                        │  │
                        │  │ ○ Sarah (VP Sales)     │  │
                        │  │   +1-555-VP-5678       │  │
                        │  │   ✓ Online             │  │
                        │  │                        │  │
                        │  │ ○ Mike (Manager)       │  │
                        │  │   +1-555-MGR-9012      │  │
                        │  │   ⚠ Offline            │  │
                        │  │                        │  │
                        │  └────────────────────────┘  │
                        └──────────────┬───────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
          ┌─────────────────────┐              ┌─────────────────────┐
          │  LOCAL SENDER       │              │  REMOTE SENDER      │
          │  (Phase 1 Flow)     │              │  (Escalation)       │
          └─────────────────────┘              └──────────┬──────────┘
                                                          │
                                                          ▼
                                    ┌──────────────────────────────────┐
                                    │  AUTHORIZATION CHECK             │
                                    │  Does user have permission to    │
                                    │  send as "Sarah (VP Sales)"?     │
                                    └──────────────┬───────────────────┘
                                                   │
                                     ┌─────────────┴─────────────┐
                                     │                           │
                                     ▼                           ▼
                              ┌─────────────┐             ┌─────────────┐
                              │ AUTHORIZED  │             │ DENIED      │
                              └──────┬──────┘             │ "Request    │
                                     │                    │  access"    │
                                     ▼                    └─────────────┘
                    ┌──────────────────────────────┐
                    │  COMPOSE MESSAGE             │
                    │  (Same flow as Phase 1)      │
                    │  but message routed to       │
                    │  remote Mac                  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  MESSAGE QUEUED              │
                    │  → Central Server            │
                    │  → Remote Mac Agent pulls    │
                    │  → AppleScript executes      │
                    │  → Status returned           │
                    └──────────────────────────────┘
```

---

## Mac Agent State Diagram (Runs on each sender's Mac)

```
                              ┌─────────────────┐
                              │  AGENT START    │
                              │  (Background)   │
                              └────────┬────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │  REGISTER WITH SERVER        │
                        │  - Send: phone, name, token  │
                        │  - Receive: agent_id         │
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │  HEARTBEAT LOOP              │◄────────┐
                        │  Poll server every 5 sec    │         │
                        │  "Any messages for me?"      │         │
                        └──────────────┬───────────────┘         │
                                       │                         │
                         ┌─────────────┴─────────────┐           │
                         │                           │           │
                         ▼                           ▼           │
                  ┌─────────────┐          ┌─────────────────┐   │
                  │ NO MESSAGES │          │ MESSAGE FOUND   │   │
                  │ Wait...     │──────────│ {phone, text}   │   │
                  └─────────────┘          └────────┬────────┘   │
                                                    │            │
                                                    ▼            │
                                    ┌──────────────────────────┐ │
                                    │  SEND VIA APPLESCRIPT    │ │
                                    │  osascript → Messages    │ │
                                    └──────────────┬───────────┘ │
                                                   │             │
                                     ┌─────────────┴─────────┐   │
                                     │                       │   │
                                     ▼                       ▼   │
                              ┌─────────────┐         ┌─────────────┐
                              │ SUCCESS     │         │ FAILED      │
                              │ Report back │         │ Report error│
                              └──────┬──────┘         └──────┬──────┘
                                     │                       │
                                     └───────────┬───────────┘
                                                 │
                                                 ▼
                                    ┌──────────────────────────┐
                                    │  UPDATE SERVER           │
                                    │  POST /messages/{id}/    │
                                    │  {status: sent/failed}   │
                                    └──────────────┬───────────┘
                                                   │
                                                   └────────────►┘
```

---

## Data Models

### Sender (stored locally + synced to server in Phase 2)

```
Sender {
    id: UUID
    name: string           // "Sarah Chen"
    phone: string          // "+1-555-123-4567"
    role: string           // "VP Sales"
    mac_agent_id: UUID     // Links to the Mac running the agent
    is_online: boolean     // Agent heartbeat status
    created_at: timestamp
    permissions: [user_ids]  // Who can send as this sender
}
```

### Message Queue (Phase 2)

```
QueuedMessage {
    id: UUID
    sender_id: UUID        // Which sender/Mac should send this
    recipient_phone: string
    message_text: string
    requested_by: user_id  // Who initiated the send
    status: enum           // queued | sent | failed
    created_at: timestamp
    sent_at: timestamp
    error: string
}
```

---

## User Permission Matrix (Phase 2)

| User Role | Can Send As Own # | Can Send As Team Lead | Can Send As VP |
|-----------|-------------------|----------------------|----------------|
| BDR       | ✓                 | ✗                    | ✗              |
| Team Lead | ✓                 | ✓ (self)             | ✗              |
| Manager   | ✓                 | ✓                    | Request        |
| VP        | ✓                 | ✓                    | ✓              |
| Admin     | ✓                 | ✓                    | ✓              |

---

## Implementation Phases

### Phase 1: Local Mode (MVP)
1. Add sender registration screen on first launch
2. Store sender profile locally (SQLite or JSON file)
3. Show "Sending as: {name} ({phone})" in header
4. No network requirements beyond existing Google Sheets

### Phase 2: Distributed Mode
1. Add central server with sender registry
2. Create Mac agent that runs in background
3. Implement message queue and polling
4. Add permissions/authorization layer
5. Real-time status updates (WebSocket or SSE)

---

## Tech Stack Recommendation

| Component | Phase 1 | Phase 2 |
|-----------|---------|---------|
| Web Frontend | Flask + Jinja | Flask + Jinja (or React) |
| Backend | Flask (local) | Flask + PostgreSQL |
| Mac Agent | AppleScript (embedded) | Python daemon + AppleScript |
| Queue | N/A | Redis or PostgreSQL |
| Real-time | N/A | WebSocket / Server-Sent Events |
| Auth | Simple password | OAuth / API keys per sender |
