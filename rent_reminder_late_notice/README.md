# Rent Reminder & Late Notice

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Every morning it checks which tenants have not paid this month's rent. Tenants get an email and a text 3 days before rent is due and a late notice with the late fee the day after; on day 5 the property manager is alerted in Slack. Each notice is saved on the tenant's row.

Built for small landlords and property managers who track rent in a spreadsheet and chase it by hand.

## What it does

1. **Daily 9 AM** (Schedule Trigger) starts the run, and **Rent Settings** (Set) holds the due day, late fee, payment link and SMS number.
2. **Read Tenants** (Google Sheets) reads every tenant.
3. **Work Out Rent Status** (Code) skips tenants whose `paidMonth` is this month, then decides who needs a reminder, a late notice or an escalation today.
4. **Route by Stage** (Switch) sends each tenant down one path:
   - **Email Rent Reminder** (Gmail), then **Text Rent Reminder** (Twilio).
   - **Email Late Notice** (Gmail), then **Text Late Notice** (Twilio), both with the fee added.
   - **Alert Property Manager** (Slack) posts to `#rent-collection`.
5. **Update Tenant Row** (Google Sheets) saves the notice and any late fee due.

## Sample request

Not applicable — this workflow runs on a schedule and reads from a Google Sheet of tenants rather than an inbound request.

## Setup (about 10 minutes)

1. **Google Sheets** — connect an account on **Read Tenants** and **Update Tenant Row**, and replace the placeholder document ID (`REPLACE_WITH_SPREADSHEET_ID`) with a sheet with the columns `tenantName`, `unit`, `email`, `phone`, `rent`, `paidMonth`, `lastNotice`, `lateFeeDue`. Mark a payment by typing the month (e.g. `2026-12`) into `paidMonth`.
2. **Rent Settings** — set the rent due day, late fee, payment link and Twilio number. Check the fee and timing against your lease and local law.
3. **Gmail** — connect an account on the two email nodes.
4. **Twilio** — connect an account on the two text nodes.
5. **Slack** — connect an account on **Alert Property Manager** and point it at your own channel (currently `#rent-collection`).
6. **Error handling** — import [Workflow Error Handler](../workflow_error_handler) first, then select it under *Workflow settings → Error workflow* (shipped as `REPLACE_WITH_ERROR_WORKFLOW_ID`).

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0(["Daily 9 AM<br/><small>scheduleTrigger</small>"])
    N1["Rent Settings<br/><small>set</small>"]
    N2["Read Tenants<br/><small>googleSheets</small>"]
    N3["Work Out Rent Status<br/><small>code</small>"]
    N4{{"Route by Stage<br/><small>switch</small>"}}
    N5["Email Rent Reminder<br/><small>gmail</small>"]
    N6["Text Rent Reminder<br/><small>twilio</small>"]
    N7["Email Late Notice<br/><small>gmail</small>"]
    N8["Text Late Notice<br/><small>twilio</small>"]
    N9["Alert Property Manager<br/><small>slack</small>"]
    N10["Update Tenant Row<br/><small>googleSheets</small>"]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 -->|reminder| N5
    N4 -->|late| N7
    N4 -->|escalate| N9
    N5 --> N6
    N7 --> N8
    N6 --> N10
    N8 --> N10
    N9 --> N10

    class N0 trigger
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
