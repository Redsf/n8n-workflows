# Speed-to-Lead Instant Response

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Replies to every new lead within seconds: a text and an email with your booking link, a Slack ping for the rep, and a HubSpot contact. If nobody has booked or logged a call 15 minutes later, it creates a call-now task and escalates.

Built for service businesses (accounting, insurance, real estate, agencies) where the first company to respond usually wins the client.

## What it does

1. **New Lead Webhook** receives the form submission and **Business Settings** adds your company name, booking link, Twilio number and HubSpot portal ID.
2. **Normalize Lead** cleans the payload, converts US phone numbers to +1 format and timestamps the lead. **Valid Lead?** rejects bad emails with a 400.
3. **Confirm Receipt** answers the form right away, then **Upsert HubSpot Contact** saves the lead (retries 3 times).
4. **Send Instant Email** sends a branded HTML email with a booking button. **Has Phone Number?** decides whether **Send Instant SMS** runs. **Alert Sales Rep** posts the lead to `#new-leads` with a HubSpot link. Each send retries and never blocks the others.
5. **Build First-Touch Log** records seconds-to-first-touch and **Log First Touch** writes it to a Google Sheet.
6. **Wait 15 Minutes**, then **Check Contact Activity** reads the contact's latest meeting and last-contacted dates. If neither is set, **Create Call-Now Task** adds a HubSpot task and **Escalate Unanswered Lead** nudges the team again.
7. **On Workflow Error** posts any failure to `#automation-alerts` and logs it to an error sheet.

## Sample request

```bash
curl -X POST https://YOUR-N8N/webhook/speed-to-lead \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Dana","lastName":"Whitfield","email":"dana@whitfieldcpa.com","phone":"(619) 555-0142","company":"Whitfield CPA","message":"Need help automating client intake","source":"website"}'
```

## Setup

1. **Business Settings**: set company name, booking link, Twilio sender number and HubSpot portal ID.
2. **HubSpot**: connect on the three HubSpot nodes.
3. **Gmail** and **Twilio**: connect on the send nodes. Your Twilio number must be SMS-enabled (A2P 10DLC registered for US numbers).
4. **Slack**: create `#new-leads` and `#automation-alerts`, connect the Slack nodes.
5. **Google Sheets**: point **Log First Touch** at a `Speed-to-Lead Log` sheet and **Log to Error Sheet** at an error log.

Every workflow ships inactive with credential placeholders. Connect your own accounts, run one test, then activate.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["New Lead Webhook / Confirm Receipt / Reject Invalid Lead"]
        N0(["New Lead Webhook<br/><small>webhook</small>"])
        N1["Business Settings<br/><small>set</small>"]
        N2["Normalize Lead<br/><small>set</small>"]
        N3{{"Valid Lead?<br/><small>if</small>"}}
        N4(["Confirm Receipt<br/><small>respondToWebhook</small>"])
        N5["Upsert HubSpot Contact<br/><small>hubspot</small>"]
        N6["Send Instant Email<br/><small>gmail</small>"]
        N7{{"Has Phone Number?<br/><small>if</small>"}}
        N8["Send Instant SMS<br/><small>twilio</small>"]
        N9["Alert Sales Rep<br/><small>slack</small>"]
        N10(["Reject Invalid Lead<br/><small>respondToWebhook</small>"])
        N11["Build First-Touch Log<br/><small>set</small>"]
        N12["Log First Touch<br/><small>googleSheets</small>"]
        N13["Wait 15 Minutes<br/><small>wait</small>"]
        N14["Check Contact Activity<br/><small>hubspot</small>"]
        N15{{"Booked or Contacted?<br/><small>if</small>"}}
        N16["Lead Handled In Time<br/><small>noOp</small>"]
        N17["Create Call-Now Task<br/><small>hubspot</small>"]
        N18["Escalate Unanswered Lead<br/><small>slack</small>"]
    end
    subgraph G1 ["Error handling"]
        N19(["On Workflow Error<br/><small>errorTrigger</small>"])
        N20["Format Error Details<br/><small>set</small>"]
        N21["Alert #automation-alerts<br/><small>slack</small>"]
        N22["Log to Error Sheet<br/><small>googleSheets</small>"]
    end
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 -->|true| N4
    N3 -->|false| N10
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 -->|true| N8
    N7 -->|false| N9
    N8 --> N9
    N9 --> N11
    N11 --> N12
    N12 --> N13
    N13 --> N14
    N14 --> N15
    N15 -->|true| N16
    N15 -->|false| N17
    N17 --> N18
    N19 --> N20
    N20 --> N21
    N20 --> N22

    class N0,N4,N10 trigger
    class N19 errorPath
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
