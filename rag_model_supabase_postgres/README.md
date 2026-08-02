# Telegram RAG Assistant with Supabase & Postgres Memory

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A Telegram bot that answers user questions by retrieving relevant chunks from a Supabase vector store, while keeping full conversational context in Postgres — combined with the same Google Drive auto-ingestion pipeline used to populate that knowledge base.

Built for teams that want a Telegram-based internal assistant grounded in their own documents, with persistent per-user conversation memory rather than a stateless chatbot.

## What it does

**Ingestion path**
1. **Google Drive Trigger** polls a specific Drive folder every minute for newly created files.
2. **Download file** pulls the new file's binary content.
3. **Supabase Vector Store** (insert mode) chunks and embeds the document, using **Default Data Loader** to parse the binary and **Embeddings OpenAI** to generate embeddings, writing vectors into the Supabase `documents` table.

**Chat path**
4. **Telegram Trigger** fires on new incoming Telegram messages.
5. **AI Agent** answers the user's message, instructed to search the knowledge base first for factual questions, maintain conversational continuity, keep replies Telegram-friendly, and explicitly say "I don't have enough information on that" rather than hallucinate. It uses **OpenAI Chat Model** (`gpt-5-mini`) for reasoning, **Postgres Chat Memory** (keyed by Telegram chat ID) for persistent conversation history, and the **Supabase_Vectors** tool (retrieve-as-tool mode, top 5 matches, backed by **Embeddings OpenAI1**) to search the same `documents` table.
6. **Send a text message** replies to the user in the originating Telegram chat with the agent's output.

## Setup (about 20 minutes)

1. **Google Drive** — connect your OAuth2 account in **Google Drive Trigger** and **Download file**. Replace the watched folder ID (`1FszwCRnJYjLqfVR5MIv5JQ_oEPH0GMlC`) with your own document drop folder.
2. **Supabase** — connect your Supabase API credentials in **Supabase Vector Store** and **Supabase_Vectors** (both use a `documents` table configured for vector search).
3. **Postgres** — connect your Postgres credentials in **Postgres Chat Memory** for persistent, per-chat conversation history.
4. **OpenAI** — add your API key in **Embeddings OpenAI**, **Embeddings OpenAI1**, and **OpenAI Chat Model** (chat model is `gpt-5-mini`).
5. **Telegram** — connect your Telegram bot API credentials in **Telegram Trigger** and **Send a text message**.

## Error handling

No dedicated error-handling nodes are present. A failed download, embedding call, database write, or Telegram send will fail the execution with no retry or alerting.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["Google Drive Trigger"]
        N0(["Google Drive Trigger<br/><small>googleDriveTrigger</small>"])
        N1["Download file<br/><small>googleDrive</small>"]
        N7["Supabase Vector Store<br/><small>vectorStoreSupabase</small>"]
        N8["Embeddings OpenAI<br/><small>embeddingsOpenAi</small>"]
        N9["Default Data Loader<br/><small>documentDefaultDataLoader</small>"]
    end
    subgraph G1 ["Telegram Trigger"]
        N2["AI Agent<br/><small>agent</small>"]
        N3["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
        N4["Embeddings OpenAI1<br/><small>embeddingsOpenAi</small>"]
        N5["Supabase_Vectors<br/><small>vectorStoreSupabase</small>"]
        N6["Postgres Chat Memory<br/><small>memoryPostgresChat</small>"]
        N10(["Telegram Trigger<br/><small>telegramTrigger</small>"])
        N11["Send a text message<br/><small>telegram</small>"]
    end
    N0 --> N1
    N1 --> N7
    N10 --> N2
    N2 --> N11
    N3 -.languageModel.-> N2
    N4 -.embedding.-> N5
    N5 -.tool.-> N2
    N6 -.memory.-> N2
    N8 -.embedding.-> N7
    N9 -.document.-> N7

    class N0,N10 trigger
    class N3,N4,N5,N6,N8,N9 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
