# Dynamic Prompt Data Extraction (Airtable)

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A workflow that turns Airtable column descriptions into live, user-editable LLM prompts: upload a PDF into a designated "File" column, and every other column whose description contains an extraction instruction gets auto-filled by an LLM reading that PDF — no code or template changes needed to add a new field, just add a column and describe what it should contain.

Built for teams who want non-technical users to define what data gets extracted from documents (by editing an Airtable column description) without touching the underlying n8n workflow.

## What it does

**Main flow (triggered by Airtable webhook events):**

1. **Airtable Webhook** receives Airtable's webhook ping (no payload details — just a signal that something changed) and **Get Webhook Payload** calls Airtable's Webhooks API to fetch the actual payload list for that base/webhook ID.
2. **Get Table Schema** (Airtable, `getSchema`) pulls the base's field schema, and **Get Prompt Fields** (code) filters it down to fields that have a non-empty `description` — these descriptions are the "dynamic prompts."
3. **Parse Event** (code) inspects the fetched payload to classify the event as `row.updated`, `field.created`, or `field.updated`, and extracts the relevant `baseId`, `tableId`, `rowId` and/or changed `field`.
4. **Event Type** (switch) branches on that classification:
   - **row.updated** → **Event Ref1** → **Get Row** fetches the full updated record → **Filter Valid Rows** keeps it only if its `File` attachment is populated → **Loop Over Items1** (split in batches, one row at a time) → **Row Ref** → **Get File Data1** downloads the PDF → **Extract from File1** pulls its text → **Fields to Update** (code) determines which columns still need values → **Generate Field Value1** (LLM chain, **OpenAI Chat Model**) extracts each missing field's value per its column description and type → **Get Result1** → **Add Row ID to Payload** → **Update Record** writes the values back to Airtable, then the loop continues to the next row.
   - **field.created** or **field.updated** → **Event Ref** → **Filter Valid Fields** ensures the field actually has a description → **Fetch Records** (Airtable `search`, filtered to rows where `File` is non-empty) → **Loop Over Items** (split in batches, one row at a time) → **Row Reference** → **Get File Data** downloads that row's PDF → **Extract from File** → **Generate Field Value** (LLM chain, **OpenAI Chat Model1**) generates just the one new/changed field's value → **Get Result** → **Update Row** writes it back, then the loop continues to the next row.

**Webhook setup flow (run once per Airtable base, manually):**

5. **When clicking 'Test workflow'** → **Set Airtable Vars** sets `appId` (base ID), `tableId`, `notificationUrl`, and `inputField` (defaults to `"File"`) as placeholders.
6. **Get Table Schema1** → **Get "Input" Field** fans out to two Airtable Webhooks API calls: **RecordsChanged Webhook** (subscribes to record `update` events scoped to the input field) and **FieldsChanged Webhook** (subscribes to field `add`/`update` events) — these register this workflow's webhook URL with Airtable so the main flow actually receives events.

## Sample input

There's no user-constructed request — the real trigger is Airtable's own webhook ping to **Airtable Webhook**, which carries only a `base.id` and `webhook.id`; the actual change payload is fetched separately. A representative parsed event (output of **Parse Event**) looks like:

```json
{
  "baseId": "appAyH3GCBJ56cfXl",
  "tableId": "tblXXXXXXXXXXXXXX",
  "event_type": "row.updated",
  "fieldId": null,
  "field": null,
  "rowId": "recXXXXXXXXXXXXXX"
}
```

For the field-created/updated path, `field` carries the schema entry driving the prompt, e.g. `{"id": "fldXXXX", "name": "Contract End Date", "type": "singleLineText", "description": "Extract the contract's end date in YYYY-MM-DD format"}`.

## Setup (~35 minutes)

1. **Airtable Personal Access Token** — add an `airtableTokenApi` credential to every Airtable node: **Get Webhook Payload**, **Get Table Schema**, **Get Table Schema1**, **Fetch Records**, **Update Row**, **Get Row**, **Update Record**, **RecordsChanged Webhook**, **FieldsChanged Webhook**.
2. **OpenAI** — add an `openAiApi` credential to **OpenAI Chat Model** (feeds **Generate Field Value1**, the row-updated path) and **OpenAI Chat Model1** (feeds **Generate Field Value**, the field-created/updated path).
3. **Publish the workflow and grab its production webhook URL** — needed before you can register Airtable webhooks against it.
4. **Run the webhook setup flow once per base** — trigger **When clicking 'Test workflow'**, first replacing the placeholders in **Set Airtable Vars**: `<MY_BASE_ID>`, `<MY_TABLE_ID>`, and `<MY_WEBHOOK_URL>` (your published workflow's webhook URL). This registers **RecordsChanged Webhook** and **FieldsChanged Webhook** against your base — Airtable webhooks expire after 7 days of inactivity and must be re-created if they lapse.
5. **Table schema requirements** — your Airtable table needs an attachment column named `File` (matching `Filter Valid Rows`' check on `$json.File[0].url` and `Fetch Records`' `filterByFormula: NOT({File} = "")`) that holds the source PDF, plus any number of additional columns whose **description** field contains the extraction instruction for that column. Update the hardcoded `"File"` references throughout (**Filter Valid Rows**, **Fetch Records**, **Set Airtable Vars**'s `inputField`) if your input column is named differently.
6. **Update Row / Update Record schema mapping** — both nodes ship with a column schema snapshot (`Name`, `File`, `Full Name`, `Created`, `Last Modified`, `Address`) matching the example base; if your table's columns differ, n8n will need you to refresh the schema mapping in these nodes after connecting your own base.
7. This template is reusable across bases, but the webhook registration step (step 4) must be repeated for each new Airtable base/table you want to wire up.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Airtable Webhook"]
        N0{{"Event Type<br/><small>switch</small>"}}
        N1["Get Prompt Fields<br/><small>code</small>"]
        N2["Get File Data<br/><small>httpRequest</small>"]
        N3["Extract from File<br/><small>extractFromFile</small>"]
        N4["Get Result<br/><small>set</small>"]
        N5["Loop Over Items<br/><small>splitInBatches</small>"]
        N6["Row Reference<br/><small>noOp</small>"]
        N7["Generate Field Value<br/><small>chainLlm</small>"]
        N8["Fields to Update<br/><small>code</small>"]
        N9["Loop Over Items1<br/><small>splitInBatches</small>"]
        N10["Row Ref<br/><small>noOp</small>"]
        N11["Get File Data1<br/><small>httpRequest</small>"]
        N12["Extract from File1<br/><small>extractFromFile</small>"]
        N13["Get Result1<br/><small>set</small>"]
        N14["Generate Field Value1<br/><small>chainLlm</small>"]
        N15{{"Filter Valid Rows<br/><small>filter</small>"}}
        N16{{"Filter Valid Fields<br/><small>filter</small>"}}
        N17["Event Ref<br/><small>noOp</small>"]
        N18["Event Ref1<br/><small>noOp</small>"]
        N19["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
        N20["OpenAI Chat Model1<br/><small>lmChatOpenAi</small>"]
        N21["Get Webhook Payload<br/><small>httpRequest</small>"]
        N22["Parse Event<br/><small>code</small>"]
        N23["Get Table Schema<br/><small>airtable</small>"]
        N24["Fetch Records<br/><small>airtable</small>"]
        N25["Update Row<br/><small>airtable</small>"]
        N26["Get Row<br/><small>airtable</small>"]
        N27["Add Row ID to Payload<br/><small>set</small>"]
        N28["Update Record<br/><small>airtable</small>"]
        N29(["Airtable Webhook<br/><small>webhook</small>"])
    end
    subgraph G1 ["When clicking ‘Test workflow’"]
        N30(["When clicking ‘Test workflow’<br/><small>manualTrigger</small>"])
        N31["Set Airtable Vars<br/><small>set</small>"]
        N32["Get Table Schema1<br/><small>airtable</small>"]
        N33["Get &quot;Input&quot; Field<br/><small>set</small>"]
        N34["RecordsChanged Webhook<br/><small>httpRequest</small>"]
        N35["FieldsChanged Webhook<br/><small>httpRequest</small>"]
    end
    N26 --> N15
    N10 --> N11
    N17 --> N16
    N18 --> N26
    N0 -->|row.updated| N18
    N0 -->|field.created| N17
    N0 -->|field.updated| N17
    N4 --> N25
    N25 --> N5
    N13 --> N27
    N22 --> N0
    N24 --> N5
    N2 --> N3
    N6 --> N2
    N28 --> N9
    N11 --> N12
    N5 -->|loop| N6
    N29 --> N23
    N8 --> N14
    N23 --> N1
    N9 -->|loop| N10
    N3 --> N7
    N15 --> N9
    N33 --> N34
    N1 --> N21
    N32 --> N33
    N31 --> N32
    N31 --> N35
    N12 --> N8
    N16 --> N24
    N21 --> N22
    N7 --> N4
    N27 --> N28
    N14 --> N13
    N30 --> N31
    N19 -.languageModel.-> N14
    N20 -.languageModel.-> N7

    class N29,N30 trigger
    class N19,N20 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
