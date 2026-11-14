# AI Review & Reputation Manager

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Polls Google Business Profile and Trustpilot every hour, drafts an on-brand reply for every new review with an LLM, and routes each one by sentiment: negative reviews escalate straight to the owner in Slack, positive ones wait for a one-tap approval before the reply gets published back to the platform.

Built for local businesses and multi-location brands that want every review answered quickly without a person drafting each response from scratch.

## What it does

1. **Every Hour** (Schedule Trigger) kicks off the run.
2. **Fetch Google Reviews** and **Fetch Trustpilot Reviews** call both platforms in parallel, and **Combine Sources** merges the two result sets.
3. **Dedupe New Reviews** (Code node) tracks previously seen review IDs in workflow static data so the same review is never processed twice.
4. **Any New Reviews?** (IF) stops the run with **No New Reviews** if nothing new came in.
5. **Process Each Review** (Split In Batches) loops through the new reviews one at a time.
6. **Draft Reply (AI Agent)**, backed by **OpenAI Chat Model** (gpt-5-mini) and a **Structured Output Parser**, reads each review and returns a sentiment classification, a draft reply, and a suggested resolution for negative cases.
7. **Negative Review?** (IF) branches on that sentiment:
   - Negative reviews go to **Escalate to Owner**, which posts the review and the suggested resolution to an owner-alerts Slack channel, then loops back for the next review.
   - Positive reviews go to **Request Approval**, a Slack `sendAndWait` prompt (24 hour timeout) asking a teammate to approve the drafted reply.
8. **Approved?** (IF) checks the approval response: if approved, **Publish Reply** posts the AI-drafted reply back to Trustpilot; if not, the loop moves on without publishing.
9. The batch loop (**Process Each Review**) continues until every review in the batch has been handled.

## Setup (about 20 minutes)

1. **Google Business Profile API** — add a header-auth credential on **Fetch Google Reviews** and replace `YOUR_ACCOUNT`/`YOUR_LOCATION` in the URL.
2. **Trustpilot API** — add a header-auth credential on **Fetch Trustpilot Reviews** (replace `YOUR_UNIT_ID`) and on **Publish Reply**.
3. **OpenAI** — connect your API key on **OpenAI Chat Model**.
4. **Slack** — connect an account on **Escalate to Owner** (replace the `owner-alerts` channel ID), **Request Approval** (replace the `review-replies` channel ID), and **Notify Ops** (replace the `ops-alerts` channel ID).
5. All `REPLACE_WITH_CREDENTIAL_ID` and `REPLACE_WITH_CHANNEL_ID` placeholders need to be swapped for real credential and channel IDs before activating.

## Error handling

**Fetch Google Reviews**, **Fetch Trustpilot Reviews**, and **Publish Reply** all retry up to 3 times on failure. A dedicated **Error Trigger** posts the failing node and message to an ops Slack channel via **Notify Ops**.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Every Hour"]
        N0(["Every Hour<br/><small>scheduleTrigger</small>"])
        N1["Fetch Google Reviews<br/><small>httpRequest</small>"]
        N2["Fetch Trustpilot Reviews<br/><small>httpRequest</small>"]
        N3["Combine Sources<br/><small>merge</small>"]
        N4["Dedupe New Reviews<br/><small>code</small>"]
        N5{{"Any New Reviews?<br/><small>if</small>"}}
        N6["No New Reviews<br/><small>noOp</small>"]
        N7["Process Each Review<br/><small>splitInBatches</small>"]
        N8["Limit To Done<br/><small>noOp</small>"]
        N9["Draft Reply (AI Agent)<br/><small>agent</small>"]
        N10["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
        N11["Structured Output Parser<br/><small>outputParserStructured</small>"]
        N12{{"Negative Review?<br/><small>if</small>"}}
        N13["Escalate to Owner<br/><small>slack</small>"]
        N14["Request Approval<br/><small>slack</small>"]
        N15{{"Approved?<br/><small>if</small>"}}
        N16["Publish Reply<br/><small>httpRequest</small>"]
    end
    subgraph G1 ["Error handling"]
        N17(["Error Trigger<br/><small>errorTrigger</small>"])
        N18["Notify Ops<br/><small>slack</small>"]
    end
    N0 --> N1
    N0 --> N2
    N1 --> N3
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 -->|true| N6
    N5 -->|false| N7
    N7 -->|done| N8
    N7 -->|loop| N9
    N9 --> N12
    N12 -->|true| N13
    N12 -->|false| N14
    N14 --> N15
    N15 -->|true| N16
    N15 -->|false| N7
    N16 --> N7
    N13 --> N7
    N17 --> N18
    N10 -.languageModel.-> N9
    N11 -.outputParser.-> N9

    class N0 trigger
    class N17 errorPath
    class N10,N11 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
