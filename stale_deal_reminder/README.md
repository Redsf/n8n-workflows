# Stale Deal Reminder

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Every weekday morning it finds open HubSpot deals with no logged activity for 7+ days. Each rep gets a Slack digest with an AI-suggested next step per deal, a follow-up task is created the first time a deal goes stale, and the sales manager gets one alert for everything idle 14+ days.

Built for small sales teams where deals quietly die because nobody noticed they stopped moving.

## What it does

1. **Weekdays 8 AM** starts the run. **Pipeline Settings** holds the stale and escalation thresholds.
2. **Find Untouched Open Deals** searches HubSpot for open deals whose last activity (or creation date, if never touched) is older than the threshold. **Get Deal Owners** loads owner names once.
3. **Score Stale Deals** (Code) computes days idle, matches owners and flags newly stale and escalated deals.
4. **Suggest Next Step** (Claude) writes one concrete action per deal. **Build Owner Digests** groups them per owner and **Post Owner Digest** sends one message per rep to `#sales-team`.
5. **Just Went Stale** keeps deals that crossed the threshold in the last 3 days, so **Create Follow-up Task** does not duplicate tasks daily.
6. **Idle 14+ Days** feeds **Alert Sales Manager**, one message to `#sales-managers` with the value at risk.
7. **On Workflow Error** posts any failure to `#automation-alerts` and logs it.

## Sample request

Not applicable: runs on a weekday schedule and reads from HubSpot.

## Setup

1. **Pipeline Settings**: thresholds and portal ID. Keep the 7 in `staleCutoffMs` in line with `staleDays`.
2. Connect **HubSpot** (also on **Get Deal Owners**), **Anthropic** and **Slack**, plus **Google Sheets** for the error log.
3. Create `#sales-team`, `#sales-managers` and `#automation-alerts`.

Every workflow ships inactive with credential placeholders. Connect your own accounts, run one test, then activate.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Weekdays 8 AM"]
        N0(["Weekdays 8 AM<br/><small>scheduleTrigger</small>"])
        N1["Pipeline Settings<br/><small>set</small>"]
        N2["Find Untouched Open Deals<br/><small>hubspot</small>"]
        N3["Get Deal Owners<br/><small>httpRequest</small>"]
        N4["Score Stale Deals<br/><small>code</small>"]
        N5["Suggest Next Step<br/><small>chainLlm</small>"]
        N6["Claude Model<br/><small>lmChatAnthropic</small>"]
        N7["Build Owner Digests<br/><small>code</small>"]
        N8["Post Owner Digest<br/><small>slack</small>"]
        N9{{"Just Went Stale<br/><small>filter</small>"}}
        N10["Create Follow-up Task<br/><small>hubspot</small>"]
        N11{{"Idle 14+ Days<br/><small>filter</small>"}}
        N12["Alert Sales Manager<br/><small>slack</small>"]
    end
    subgraph G1 ["Error handling"]
        N13(["On Workflow Error<br/><small>errorTrigger</small>"])
        N14["Format Error Details<br/><small>set</small>"]
        N15["Alert #automation-alerts<br/><small>slack</small>"]
        N16["Log to Error Sheet<br/><small>googleSheets</small>"]
    end
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N4 --> N9
    N4 --> N11
    N5 --> N7
    N7 --> N8
    N9 --> N10
    N11 --> N12
    N13 --> N14
    N14 --> N15
    N14 --> N16
    N6 -.languageModel.-> N5

    class N0 trigger
    class N13 errorPath
    class N6 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
