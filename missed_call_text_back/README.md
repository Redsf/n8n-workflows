# Missed-Call Text Back

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

When a call to your Twilio number goes unanswered, the caller gets a friendly text with your booking link within seconds, worded differently for open hours and after hours. Known HubSpot contacts get a callback task, and the team is alerted in Slack. Text replies are handled by [Missed-Call Reply Classifier](../missed_call_reply_classifier).

Built for offices that miss calls while with clients: CPA firms in tax season, insurance agencies, home-service and real estate teams.

## What it does

1. **Twilio Call Status** (Webhook) receives Twilio's status callback, and **Business Settings** (Set) adds your name, booking link, number, time zone and opening hours.
2. **Normalize Call** (Set) extracts the caller and works out whether the call came in during business hours. **Missed Call?** (If) only lets no-answer, busy, failed and canceled calls continue; **Acknowledge Missed Call** and **Acknowledge Answered Call** always send Twilio an empty TwiML reply.
3. **Find Caller in HubSpot** (HubSpot) searches phone and mobile phone. **During Business Hours?** (If) picks **Text Back (Open Hours)** or **Text Back (After Hours)** (Twilio).
4. **Known Contact?** (If) runs **Create Callback Task** (HubSpot), due in 30 minutes or 9 AM next day after hours.
5. **Alert Team** (Slack) posts to `#missed-calls` either way, then **Build Call Log Row** (Set) and **Log Missed Call** (Google Sheets) record the call.

## Sample request

Twilio sends this automatically. To test by hand:

```bash
curl -X POST https://YOUR-N8N/webhook/missed-call \
  -d "CallSid=CA123" -d "CallStatus=no-answer" -d "From=+16195550142" -d "To=+15555550100"
```

## Setup (about 10 minutes)

1. **Business Settings** — set your business name, booking link, Twilio number, IANA time zone and open/close hours.
2. **Twilio** — connect an account on both **Text Back** nodes, and in the Twilio console set *Call status changes* on your number to the `missed-call` URL.
3. **HubSpot** — connect an account on **Find Caller in HubSpot** and **Create Callback Task**.
4. **Slack** — connect an account on **Alert Team** and point it at your own channel (currently `#missed-calls`).
5. **Google Sheets** — connect an account on **Log Missed Call** and replace the placeholder document ID (`REPLACE_WITH_SPREADSHEET_ID`).
6. **Error handling** — import [Workflow Error Handler](../workflow_error_handler) first, then select it under *Workflow settings → Error workflow* (shipped as `REPLACE_WITH_ERROR_WORKFLOW_ID`).

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0(["Twilio Call Status<br/><small>webhook</small>"])
    N1["Business Settings<br/><small>set</small>"]
    N2["Normalize Call<br/><small>set</small>"]
    N3{{"Missed Call?<br/><small>if</small>"}}
    N4(["Acknowledge Missed Call<br/><small>respondToWebhook</small>"])
    N5["Find Caller in HubSpot<br/><small>hubspot</small>"]
    N6{{"During Business Hours?<br/><small>if</small>"}}
    N7["Text Back (Open Hours)<br/><small>twilio</small>"]
    N8{{"Known Contact?<br/><small>if</small>"}}
    N9["Text Back (After Hours)<br/><small>twilio</small>"]
    N10(["Acknowledge Answered Call<br/><small>respondToWebhook</small>"])
    N11["Create Callback Task<br/><small>hubspot</small>"]
    N12["Alert Team<br/><small>slack</small>"]
    N13["Build Call Log Row<br/><small>set</small>"]
    N14["Log Missed Call<br/><small>googleSheets</small>"]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 -->|true| N4
    N3 -->|false| N10
    N4 --> N5
    N5 --> N6
    N6 -->|true| N7
    N6 -->|false| N9
    N7 --> N8
    N8 -->|true| N11
    N8 -->|false| N12
    N9 --> N8
    N11 --> N12
    N12 --> N13
    N13 --> N14

    class N0,N4,N10 trigger
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
