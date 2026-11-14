# Old Lead Revival

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Every weekday morning it finds HubSpot leads with no activity for 90+ days, writes each one a short personal check-in with AI, and asks your team to approve every email in Slack before it is sent. Replies alert the rep.

Built for firms sitting on a CRM full of leads that went quiet, who want them re-engaged without a blast campaign.

## What it does

1. **Weekdays 9 AM** starts the run. **Revival Settings** holds the sender, booking link, daily cap and cutoff.
2. **Find Cold Leads** searches HubSpot for lifecycle = lead, last activity before the cutoff, not opted out, oldest first, up to the daily cap. **Has Email** drops anything without an address.
3. **One Lead at a Time** loops: **Write Revival Email** (Claude) drafts a 60 to 110 word body from the lead's notes, then **Ask for Approval** posts it to `#lead-revival` with *Send it* / *Skip* buttons (expires after 24h).
4. Approved: **Send Revival Email** (Gmail, with an opt-out line) and **Log Email in HubSpot**, which also resets the contact's activity date so it is not picked again tomorrow. Either way **Log Revival Attempt** writes the outcome to a sheet.
5. **Post Daily Summary** reports how many were sent and skipped.
6. **Reply Received** polls Gmail every 15 minutes for replies, **Alert Rep of Reply** posts them, and **Mark Reply as Read** stops double alerts.
7. **On Workflow Error** posts any failure to `#automation-alerts` and logs it.

## Sample request

Not applicable: runs on a weekday schedule and reads from HubSpot.

## Setup

1. **Revival Settings**: sender name, booking link, daily cap. Change the 90 in `cutoffMs` to adjust how cold a lead must be.
2. Connect **HubSpot**, **Anthropic**, **Slack**, **Gmail** and **Google Sheets**.
3. Create `#lead-revival` and `#automation-alerts` in Slack.
4. Approvals run one at a time, so keep the daily cap small enough for your team to review each morning.

Every workflow ships inactive with credential placeholders. Connect your own accounts, run one test, then activate.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Weekdays 9 AM"]
        N0(["Weekdays 9 AM<br/><small>scheduleTrigger</small>"])
        N1["Revival Settings<br/><small>set</small>"]
        N2["Find Cold Leads<br/><small>hubspot</small>"]
        N3{{"Has Email<br/><small>filter</small>"}}
        N4["Post Daily Summary<br/><small>slack</small>"]
        N5["Write Revival Email<br/><small>chainLlm</small>"]
        N6["Claude Model<br/><small>lmChatAnthropic</small>"]
        N7["Ask for Approval<br/><small>slack</small>"]
        N8{{"Approved?<br/><small>if</small>"}}
        N9["Send Revival Email<br/><small>gmail</small>"]
        N10["Log Email in HubSpot<br/><small>hubspot</small>"]
        N11["Mark Sent<br/><small>set</small>"]
        N12["Log Revival Attempt<br/><small>googleSheets</small>"]
        N13["Mark Skipped<br/><small>set</small>"]
        N14["One Lead at a Time<br/><small>splitInBatches</small>"]
    end
    subgraph G1 ["Reply Received"]
        N15(["Reply Received<br/><small>gmailTrigger</small>"])
        N16["Alert Rep of Reply<br/><small>slack</small>"]
        N17["Mark Reply as Read<br/><small>gmail</small>"]
    end
    subgraph G2 ["Error handling"]
        N18(["On Workflow Error<br/><small>errorTrigger</small>"])
        N19["Format Error Details<br/><small>set</small>"]
        N20["Alert #automation-alerts<br/><small>slack</small>"]
        N21["Log to Error Sheet<br/><small>googleSheets</small>"]
    end
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N14
    N5 --> N7
    N7 --> N8
    N8 -->|true| N9
    N8 -->|false| N13
    N9 --> N10
    N10 --> N11
    N11 --> N12
    N12 --> N14
    N13 --> N12
    N14 -->|done| N4
    N14 -->|loop| N5
    N15 --> N16
    N16 --> N17
    N18 --> N19
    N19 --> N20
    N19 --> N21
    N6 -.languageModel.-> N5

    class N0,N15 trigger
    class N18 errorPath
    class N6 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
