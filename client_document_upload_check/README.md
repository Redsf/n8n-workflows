# Client Document Upload Check

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

Clients upload their onboarding documents through a hosted n8n form. Each file is saved to the client's Drive folder, read and matched to their checklist by Claude, and the tracker is updated. The client gets an email saying what is still needed, and the team hears when everything is in.

The second step of [Client Onboarding Kickoff](../client_onboarding_kickoff), for firms collecting documents from new clients.

## What it does

1. **Client Uploads Documents** (Form Trigger) hosts the upload page at `/form/client-documents`.
2. **Find Client in Tracker** (Google Sheets) looks up the email. **Known Client?** (If) sends unknown addresses to **Flag Unknown Uploader** (Slack).
3. **Split Uploaded Files** (Code) makes one item per file, and **Save to Client Folder** (Google Drive) files each one.
4. **Read PDF Text** (Extract from File) reads the first pages; images pass through without text.
5. **Check Document** (Basic LLM Chain with **Claude Model** and **Document Check Schema**) matches each file to one checklist item and flags unreadable or wrong files.
6. **Update Checklist** (Code) removes what arrived, and **Save Progress** (Google Sheets) writes the new list and status back to the tracker.
7. **All Documents In?** (If) splits two ways:
   - Yes: **Email: All Received** (Gmail) thanks the client and **Ready for Kickoff** (Slack) tells the team.
   - No: **Email: Still Needed** (Gmail) lists what is missing and any problem files.

## Sample request

Open the hosted form URL from **Client Uploads Documents**. The welcome email from [Client Onboarding Kickoff](../client_onboarding_kickoff) links to it with the client's email filled in.

## Setup (about 10 minutes)

1. **Google Sheets** — connect an account on **Find Client in Tracker** and **Save Progress**, and use the same **Onboarding Tracker** sheet as Client Onboarding Kickoff (`REPLACE_WITH_SPREADSHEET_ID`).
2. **Google Drive** — connect an account on **Save to Client Folder**.
3. **Anthropic** — connect an account on **Claude Model**.
4. **Gmail** — connect an account on both email nodes.
5. **Slack** — connect an account on **Ready for Kickoff** and **Flag Unknown Uploader** (currently `#onboarding`).
6. **Error handling** — import [Workflow Error Handler](../workflow_error_handler) first, then select it under *Workflow settings → Error workflow* (shipped as `REPLACE_WITH_ERROR_WORKFLOW_ID`).
7. Activate the workflow and copy the production form URL into **Onboarding Settings** of Client Onboarding Kickoff.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0(["Client Uploads Documents<br/><small>formTrigger</small>"])
    N1["Find Client in Tracker<br/><small>googleSheets</small>"]
    N2{{"Known Client?<br/><small>if</small>"}}
    N3["Split Uploaded Files<br/><small>code</small>"]
    N4["Save to Client Folder<br/><small>googleDrive</small>"]
    N5["Read PDF Text<br/><small>extractFromFile</small>"]
    N6["Check Document<br/><small>chainLlm</small>"]
    N7["Claude Model<br/><small>lmChatAnthropic</small>"]
    N8["Document Check Schema<br/><small>outputParserStructured</small>"]
    N9["Update Checklist<br/><small>code</small>"]
    N10["Save Progress<br/><small>googleSheets</small>"]
    N11{{"All Documents In?<br/><small>if</small>"}}
    N12["Email: All Received<br/><small>gmail</small>"]
    N13["Ready for Kickoff<br/><small>slack</small>"]
    N14["Email: Still Needed<br/><small>gmail</small>"]
    N15["Flag Unknown Uploader<br/><small>slack</small>"]
    N0 --> N1
    N1 --> N2
    N2 -->|true| N3
    N2 -->|false| N15
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N9
    N9 --> N10
    N10 --> N11
    N11 -->|true| N12
    N11 -->|false| N14
    N12 --> N13
    N7 -.languageModel.-> N6
    N8 -.outputParser.-> N6

    class N0 trigger
    class N7,N8 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
