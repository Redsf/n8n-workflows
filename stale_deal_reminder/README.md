# Stale Deal Reminder

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Every weekday morning it finds open HubSpot deals with no logged activity for 7+ days. Each rep gets a Slack digest with an AI-suggested next step per deal, a follow-up task is created the first time a deal goes stale, and the sales manager gets one alert for everything idle 14+ days.

Built for small sales teams where deals quietly die because nobody noticed they stopped moving.

## What it does

1. **Weekdays 8 AM** (Schedule Trigger) starts the run, and **Pipeline Settings** (Set) holds the stale and escalation thresholds.
2. **Find Untouched Open Deals** (HubSpot) searches for open deals whose last activity, or creation date if never touched, is older than the threshold. **Get Deal Owners** (HTTP Request) loads owner names once.
3. **Score Stale Deals** (Code) computes days idle, matches owners and flags newly stale and escalated deals.
4. From there the flow splits three ways:
   - **Suggest Next Step** (Basic LLM Chain with **Claude Model**) writes one action per deal, **Build Owner Digests** (Code) groups them per owner and **Post Owner Digest** (Slack) sends one message per rep to `#sales-team`.
   - **Just Went Stale** (Filter) keeps deals that crossed the threshold in the last 3 days, so **Create Follow-up Task** (HubSpot) does not duplicate tasks daily.
   - **Idle 14+ Days** (Filter) feeds **Alert Sales Manager** (Slack), one message to `#sales-managers` with the value at risk.

## Sample request

Not applicable — this workflow runs on a weekday schedule and reads from HubSpot rather than an inbound request.

## Setup (about 10 minutes)

1. **Pipeline Settings** — set the thresholds and portal ID. Keep the 7 in `staleCutoffMs` in line with `staleDays`.
2. **HubSpot** — connect an account on **Find Untouched Open Deals**, **Get Deal Owners** and **Create Follow-up Task**.
3. **Anthropic** — connect an account on **Claude Model**.
4. **Slack** — connect an account on **Post Owner Digest** and **Alert Sales Manager** (currently `#sales-team` and `#sales-managers`).
5. **Error handling** — import [Workflow Error Handler](../workflow_error_handler) first, then select it under *Workflow settings → Error workflow* (shipped as `REPLACE_WITH_ERROR_WORKFLOW_ID`).

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
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
    N6 -.languageModel.-> N5

    class N0 trigger
    class N6 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
