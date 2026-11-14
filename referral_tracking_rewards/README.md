# Referral Tracking & Rewards

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Captures referrals, thanks the referrer, logs everything in a tracker sheet, and when the referred lead becomes a client it asks finance to send the reward and tells the referrer the good news. Nobody is rewarded twice.

Built for referral-driven firms (CPAs, advisors, agencies, contractors) that track referrals in someone's head or an inbox.

## What it does

1. **New Referral** (Webhook) receives the form, **Referral Settings** (Set) holds the sender and reward text and **Normalize Referral** (Set) cleans both emails.
2. **Valid Referral?** (If) requires both emails and blocks self-referrals, sending bad ones to **Reject Invalid Referral** (400). **Confirm Referral** (Respond to Webhook) answers the form.
3. **Find Referrer in HubSpot** (HubSpot) looks up the referrer and **Save Referred Lead** (HubSpot) upserts the new lead with `referred_by_email`.
4. **Referrer in CRM?** (If) decides whether **Thank the Referrer** (Gmail) emails them. **Log Referral** (Google Sheets) writes the row with status `referred` and **Announce Referral** (Slack) posts to `#referrals`.
5. **Deal Won** (Webhook) receives the client's email from a HubSpot workflow, **Won Deal Details** (Set) adds the reward text and **Find Open Referral** (Google Sheets) looks for a row still marked `referred`.
6. **Was a Referral?** (If) splits two ways:
   - Yes: **Ask Finance to Send Reward** (Slack), **Tell Referrer the Good News** (Gmail) and **Mark Reward Sent** (Google Sheets), which changes the status so the reward cannot fire twice.
   - No: **Not a Referral Deal** ends the run.
7. **On Workflow Error** (Error Trigger) feeds **Format Error Details**, which posts to `#automation-alerts` and writes a row to the error sheet.

## Sample request

```bash
curl -X POST https://YOUR-N8N/webhook/referral \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Marcus","lastName":"Lee","email":"marcus@leewealth.com","company":"Lee Wealth Partners","referredByEmail":"dana@whitfieldcpa.com","note":"Dana said you fixed their intake process"}'

curl -X POST https://YOUR-N8N/webhook/referral-deal-won \
  -H "Content-Type: application/json" \
  -d '{"contactEmail":"marcus@leewealth.com","dealName":"Lee Wealth - Onboarding automation","amount":"9000"}'
```

## Setup (about 15 minutes)

1. **HubSpot** — create a contact property `referred_by_email` (single-line text), then connect an account on **Find Referrer in HubSpot** and **Save Referred Lead**. In a HubSpot workflow (deal closed won), send the primary contact's email to `/referral-deal-won`.
2. **Google Sheets** — create a **Referral Tracker** sheet with headers `receivedAt, leadEmail, leadName, leadCompany, referrerEmail, referrerName, referrerInCrm, status, rewardedAt`. Connect an account on **Log Referral**, **Find Open Referral**, **Mark Reward Sent** and **Log to Error Sheet**, and replace the placeholder document IDs (`REPLACE_WITH_SPREADSHEET_ID`).
3. **Gmail** — connect an account on **Thank the Referrer** and **Tell Referrer the Good News**.
4. **Slack** — connect an account on **Announce Referral**, **Ask Finance to Send Reward** and **Alert #automation-alerts**, and create `#referrals` and `#automation-alerts`.
5. **Referral Settings** and **Won Deal Details** — edit the reward text.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["New Referral / Confirm Referral / Reject Invalid Referral"]
        N0(["New Referral<br/><small>webhook</small>"])
        N1["Referral Settings<br/><small>set</small>"]
        N2["Normalize Referral<br/><small>set</small>"]
        N3{{"Valid Referral?<br/><small>if</small>"}}
        N4(["Confirm Referral<br/><small>respondToWebhook</small>"])
        N5["Find Referrer in HubSpot<br/><small>hubspot</small>"]
        N6["Save Referred Lead<br/><small>hubspot</small>"]
        N7{{"Referrer in CRM?<br/><small>if</small>"}}
        N8["Thank the Referrer<br/><small>gmail</small>"]
        N9["Log Referral<br/><small>googleSheets</small>"]
        N10(["Reject Invalid Referral<br/><small>respondToWebhook</small>"])
        N11["Announce Referral<br/><small>slack</small>"]
    end
    subgraph G1 ["Deal Won"]
        N12(["Deal Won<br/><small>webhook</small>"])
        N13["Won Deal Details<br/><small>set</small>"]
        N14["Find Open Referral<br/><small>googleSheets</small>"]
        N15{{"Was a Referral?<br/><small>if</small>"}}
        N16["Ask Finance to Send Reward<br/><small>slack</small>"]
        N17["Tell Referrer the Good News<br/><small>gmail</small>"]
        N18["Mark Reward Sent<br/><small>googleSheets</small>"]
        N19["Not a Referral Deal<br/><small>noOp</small>"]
    end
    subgraph G2 ["Error handling"]
        N20(["On Workflow Error<br/><small>errorTrigger</small>"])
        N21["Format Error Details<br/><small>set</small>"]
        N22["Alert #automation-alerts<br/><small>slack</small>"]
        N23["Log to Error Sheet<br/><small>googleSheets</small>"]
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
    N12 --> N13
    N13 --> N14
    N14 --> N15
    N15 -->|true| N16
    N15 -->|false| N19
    N16 --> N17
    N17 --> N18
    N20 --> N21
    N21 --> N22
    N21 --> N23

    class N0,N4,N10,N12 trigger
    class N20 errorPath
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
