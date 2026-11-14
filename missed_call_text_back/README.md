# Missed-Call Text Back

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

When a call to your Twilio number goes unanswered, the caller gets a friendly text with your booking link within seconds, worded differently for open hours and after hours. Known HubSpot contacts get a callback task, the team is alerted in Slack, and when the caller texts back, AI sorts the reply before posting it.

Built for offices that miss calls while with clients: CPA firms in tax season, insurance agencies, home-service and real estate teams.

## What it does

1. **Twilio Call Status** (Webhook) receives Twilio's status callback, and **Business Settings** (Set) adds your name, booking link, number, time zone and opening hours.
2. **Normalize Call** (Set) extracts the caller and works out whether the call came in during business hours. **Missed Call?** (If) only lets no-answer, busy, failed and canceled calls continue; **Acknowledge Missed Call** and **Acknowledge Answered Call** always send Twilio an empty TwiML reply.
3. **Find Caller in HubSpot** (HubSpot) searches phone and mobile phone. **During Business Hours?** (If) picks **Text Back (Open Hours)** or **Text Back (After Hours)** (Twilio).
4. **Known Contact?** (If) runs **Create Callback Task** (HubSpot), due in 30 minutes or 9 AM next day after hours. **Alert Team** (Slack) posts to `#missed-calls` either way, then **Build Call Log Row** (Set) and **Log Missed Call** (Google Sheets) record the call.
5. **Twilio Incoming SMS** (Webhook) catches replies, **Acknowledge SMS** answers Twilio and **Normalize Reply** (Set) cleans the text. **Classify Reply** (Text Classifier with **Claude Model**) sorts each one into urgent, wants booking, question, opt-out or other, a **Tag** node labels it, and **Post Reply to Slack** (Slack) shows it.
6. **On Workflow Error** (Error Trigger) feeds **Format Error Details**, which posts to `#automation-alerts` and writes a row to the error sheet.

## Sample request

Twilio sends these automatically. To test by hand:

```bash
curl -X POST https://YOUR-N8N/webhook/missed-call \
  -d "CallSid=CA123" -d "CallStatus=no-answer" -d "From=+16195550142" -d "To=+15555550100"

curl -X POST https://YOUR-N8N/webhook/missed-call-reply \
  -d "From=+16195550142" -d "Body=Can someone call me about a tax notice? It is due Friday."
```

## Setup (about 15 minutes)

1. **Business Settings** — set your business name, booking link, Twilio number, IANA time zone and open/close hours.
2. **Twilio** — connect an account on both **Text Back** nodes. In the Twilio console, set *Call status changes* to the `missed-call` URL and *A message comes in* to `missed-call-reply`.
3. **HubSpot** — connect an account on **Find Caller in HubSpot** and **Create Callback Task**.
4. **Anthropic** — connect an account on **Claude Model**.
5. **Slack** — connect an account on **Alert Team**, **Post Reply to Slack** and **Alert #automation-alerts**, and create `#missed-calls` and `#automation-alerts`.
6. **Google Sheets** — connect an account on **Log Missed Call** and **Log to Error Sheet**, and replace the placeholder document IDs (`REPLACE_WITH_SPREADSHEET_ID`) with your own sheets.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Twilio Call Status / Acknowledge Missed Call / Acknowledge Answered Call"]
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
    end
    subgraph G1 ["Twilio Incoming SMS / Acknowledge SMS"]
        N15(["Twilio Incoming SMS<br/><small>webhook</small>"])
        N16(["Acknowledge SMS<br/><small>respondToWebhook</small>"])
        N17["Normalize Reply<br/><small>set</small>"]
        N18{{"Classify Reply<br/><small>textClassifier</small>"}}
        N19["Claude Model<br/><small>lmChatAnthropic</small>"]
        N20["Tag: Urgent<br/><small>set</small>"]
        N21["Post Reply to Slack<br/><small>slack</small>"]
        N22["Tag: Wants Booking<br/><small>set</small>"]
        N23["Tag: Question<br/><small>set</small>"]
        N24["Tag: Opt Out<br/><small>set</small>"]
        N25["Tag: Other<br/><small>set</small>"]
    end
    subgraph G2 ["Error handling"]
        N26(["On Workflow Error<br/><small>errorTrigger</small>"])
        N27["Format Error Details<br/><small>set</small>"]
        N28["Alert #automation-alerts<br/><small>slack</small>"]
        N29["Log to Error Sheet<br/><small>googleSheets</small>"]
    end
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
    N15 --> N16
    N16 --> N17
    N17 --> N18
    N18 -->|urgent| N20
    N18 -->|wants_booking| N22
    N18 -->|question| N23
    N18 -->|opt_out| N24
    N18 -->|other| N25
    N20 --> N21
    N22 --> N21
    N23 --> N21
    N24 --> N21
    N25 --> N21
    N26 --> N27
    N27 --> N28
    N27 --> N29
    N19 -.languageModel.-> N18

    class N0,N4,N10,N15,N16 trigger
    class N26 errorPath
    class N19 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
