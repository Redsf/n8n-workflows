# Speed-to-Lead Instant Response

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Replies to every new lead within seconds: a text and an email with your booking link, a Slack ping for the rep, and a HubSpot contact. If nobody has booked or logged a call 15 minutes later, it creates a call-now task and escalates.

Built for service businesses (accounting, insurance, real estate, agencies) where the first company to respond usually wins the client.

## What it does

1. **New Lead Webhook** (Webhook) receives the form submission, and **Business Settings** (Set) adds your company name, booking link, Twilio number and HubSpot portal ID.
2. **Normalize Lead** (Set) cleans the payload, converts US phone numbers to +1 format and timestamps the lead. **Valid Lead?** (If) sends bad emails to **Reject Invalid Lead**, which answers with a 400.
3. **Confirm Receipt** (Respond to Webhook) answers the form right away, then **Upsert HubSpot Contact** (HubSpot) saves the lead, retrying 3 times.
4. From there the flow splits three ways:
   - **Send Instant Email** (Gmail) sends a branded email with a booking button.
   - **Has Phone Number?** (If) decides whether **Send Instant SMS** (Twilio) runs.
   - **Alert Sales Rep** (Slack) posts the lead to `#new-leads` with a HubSpot link.
5. **Build First-Touch Log** (Set) records seconds-to-first-touch and **Log First Touch** (Google Sheets) writes it to a sheet.
6. **Wait 15 Minutes** (Wait), then **Check Contact Activity** (HubSpot) reads the latest meeting and last-contacted dates. **Booked or Contacted?** (If) ends at **Lead Handled In Time** if either is set; otherwise **Create Call-Now Task** (HubSpot) adds a task and **Escalate Unanswered Lead** (Slack) nudges the team again.

## Sample request

```bash
curl -X POST https://YOUR-N8N/webhook/speed-to-lead \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Dana","lastName":"Whitfield","email":"dana@whitfieldcpa.com","phone":"(619) 555-0142","company":"Whitfield CPA","message":"Need help automating client intake","source":"website"}'
```

## Setup (about 15 minutes)

1. **Business Settings** — set your company name, booking link, Twilio sender number and HubSpot portal ID.
2. **HubSpot** — connect an account on **Upsert HubSpot Contact**, **Check Contact Activity** and **Create Call-Now Task**.
3. **Gmail** — connect an account on **Send Instant Email** and adjust the wording as needed.
4. **Twilio** — connect an account on **Send Instant SMS**. The number must be SMS-enabled (A2P 10DLC registered for US numbers).
5. **Slack** — connect an account on **Alert Sales Rep** and **Escalate Unanswered Lead**, and point them at your own channel (currently `#new-leads`).
6. **Google Sheets** — connect an account on **Log First Touch** and replace the placeholder document ID (`REPLACE_WITH_SPREADSHEET_ID`) with your own sheet.
7. **Error handling** — import [Workflow Error Handler](../workflow_error_handler) first, then select it under *Workflow settings → Error workflow* (shipped as `REPLACE_WITH_ERROR_WORKFLOW_ID`).

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
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

    class N0,N4,N10 trigger
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
