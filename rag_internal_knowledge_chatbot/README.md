# RAG-Powered Internal Knowledge Chatbot

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A Slack-native Q&A bot that answers employee questions from your company's internal documentation. Notion pages and Google Drive files are synced into a Pinecone vector store every night, and mentioning the bot in Slack triggers an AI agent that retrieves the relevant chunks and replies in-thread with a source link attached.

Built for internal ops and knowledge-management teams that want documentation to stay searchable and current without anyone manually re-indexing it.

## What it does

This workflow runs two independent flows off two triggers.

**Nightly index sync:**

1. **Nightly Sync (2am)** fires once a day.
2. **Search Notion Pages** and **Search Drive Files** run in parallel, pulling the full page/file list from each source.
3. **Combine Doc Sources** merges both lists into one stream.
4. **Normalize Doc List** (Code node) reshapes every item into a common `{id, title, url, source}` structure.
5. **Process Each Doc** loops through the documents one at a time (batch size 1).
6. **Is Notion Doc?** branches on the `source` field:
   - Notion path: **Get Notion Page Blocks** fetches the page's blocks, then **Flatten Notion Text** joins the block text into a single content string.
   - Drive path: **Download Drive File** downloads the binary, **Extract Drive Text** pulls plain text out of it, then **Build Drive Doc** assembles the same `{id, title, url, source, content}` shape.
7. **Pinecone: Insert Docs** upserts each document into Pinecone, embedding it via **Insert Embeddings** and chunking/loading it through **Doc Loader**, which attaches title, url, and source as metadata.
8. The loop feeds back into **Process Each Doc** until every document is processed, then falls through to **Sync Done**.

**Slack Q&A:**

1. **Slack Q&A Trigger** fires on an `app_mention` event in the configured channel.
2. **Strip Mention** (Code node) removes the `<@BOTID>` tag from the message text and captures the channel and thread timestamp.
3. **Answer Question (AI Agent)** answers the question using **OpenAI Chat Model (Q&A)** and the **Knowledge Base (RAG Tool)**, a Pinecone retrieval tool (top 4 matches, with document metadata included) backed by **Retrieval Embeddings**. The agent's system prompt requires it to cite the source URL from the retrieved metadata, or say honestly that nothing relevant was found.
4. **Reply in Thread** posts the agent's answer back to Slack as a threaded reply.

**Error handling:** a separate **Error Trigger** catches any failure across the workflow and **Notify Ops** posts the failing error message to a Slack ops-alerts channel.

## Setup (about 25 minutes)

1. **Notion** — connect your account in **Search Notion Pages** and **Get Notion Page Blocks**.
2. **Google Drive** — connect your account in **Search Drive Files** and **Download Drive File**.
3. **OpenAI** — add your key in **Insert Embeddings**, **Retrieval Embeddings**, and **OpenAI Chat Model (Q&A)** (uses `text-embedding-3-small` for embeddings and `gpt-5-mini` for chat).
4. **Pinecone** — connect your account in **Pinecone: Insert Docs** and **Knowledge Base (RAG Tool)**, and set your actual index name in both nodes (replace the `REPLACE_WITH_PINECONE_INDEX` placeholder).
5. **Slack** — connect your account in **Slack Q&A Trigger**, **Reply in Thread**, and **Notify Ops**. Enable the `app_mention` event on your Slack app, set the target channel ID in **Slack Q&A Trigger** (replace `REPLACE_WITH_CHANNEL_ID`), and set the ops-alerts channel in **Notify Ops**.

All credential IDs in this workflow are placeholders (`REPLACE_WITH_CREDENTIAL_ID`) — assign your own n8n credentials to each node before activating.

## Error handling

Notion and Drive API calls retry up to twice on failure. A dedicated **Error Trigger** catches any workflow-level failure and **Notify Ops** posts the error message to a Slack channel, so a broken nightly sync or a failed Slack reply doesn't go unnoticed.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Nightly Sync (2am)"]
        N0(["Nightly Sync (2am)<br/><small>scheduleTrigger</small>"])
        N1["Search Notion Pages<br/><small>notion</small>"]
        N2["Search Drive Files<br/><small>googleDrive</small>"]
        N3["Combine Doc Sources<br/><small>merge</small>"]
        N4["Normalize Doc List<br/><small>code</small>"]
        N5["Process Each Doc<br/><small>splitInBatches</small>"]
        N6["Sync Done<br/><small>noOp</small>"]
        N7{{"Is Notion Doc?<br/><small>if</small>"}}
        N8["Get Notion Page Blocks<br/><small>notion</small>"]
        N9["Flatten Notion Text<br/><small>code</small>"]
        N10["Download Drive File<br/><small>googleDrive</small>"]
        N11["Extract Drive Text<br/><small>extractFromFile</small>"]
        N12["Build Drive Doc<br/><small>code</small>"]
        N13["Pinecone: Insert Docs<br/><small>vectorStorePinecone</small>"]
        N14["Insert Embeddings<br/><small>embeddingsOpenAi</small>"]
        N15["Doc Loader<br/><small>documentDefaultDataLoader</small>"]
    end
    subgraph G1 ["Slack Q&amp;A Trigger"]
        N16(["Slack Q&amp;A Trigger<br/><small>slackTrigger</small>"])
        N17["Strip Mention<br/><small>code</small>"]
        N18["Answer Question (AI Agent)<br/><small>agent</small>"]
        N19["OpenAI Chat Model (Q&amp;A)<br/><small>lmChatOpenAi</small>"]
        N20["Knowledge Base (RAG Tool)<br/><small>vectorStorePinecone</small>"]
        N21["Retrieval Embeddings<br/><small>embeddingsOpenAi</small>"]
        N22["Reply in Thread<br/><small>slack</small>"]
    end
    subgraph G2 ["Error handling"]
        N23(["Error Trigger<br/><small>errorTrigger</small>"])
        N24["Notify Ops<br/><small>slack</small>"]
    end
    N0 --> N1
    N0 --> N2
    N1 --> N3
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 -->|done| N6
    N5 -->|loop| N7
    N7 -->|true| N8
    N7 -->|false| N10
    N8 --> N9
    N9 --> N13
    N10 --> N11
    N11 --> N12
    N12 --> N13
    N13 --> N5
    N16 --> N17
    N17 --> N18
    N18 --> N22
    N23 --> N24
    N14 -.embedding.-> N13
    N15 -.document.-> N13
    N19 -.languageModel.-> N18
    N20 -.tool.-> N18
    N21 -.embedding.-> N20

    class N0,N16 trigger
    class N23 errorPath
    class N14,N15,N19,N20,N21 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
