# Customer Service Agent with RAG

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

An email-based support agent that watches a Gmail inbox for incoming customer questions, answers them by retrieving relevant knowledge from a Supabase vector store, and rewrites the raw answer into a polished, professional email reply.

Built for small support teams who want first-line email responses grounded in their own knowledge base (policies, FAQs, product docs) without hiring a dedicated support agent for routine questions.

## What it does

1. **Gmail Trigger** polls the connected inbox every minute for new messages.
2. **Edit Fields** (Set) extracts the customer's `Message` (from the email snippet) and their first `Name` (parsed from the `From` header).
3. **AI Agent** (LangChain Agent, backed by **OpenAI Chat Model** on GPT-5-mini) answers the customer's message. It is instructed to always consult the connected vector store tool first and reply short, precise and formal.
   - **Supabase Vector Store** is wired in as a retrieval tool (`documents` table), giving the agent RAG access to a knowledge base.
   - **Embeddings OpenAI** generates the embeddings used for vector similarity search.
   - **Simple Memory** (buffer window, keyed on the incoming message text, 50-message context window) gives the agent short-term conversational memory.
4. **G-mail writter** (LangChain Agent, backed by **OpenAI Chat Model1**) takes the AI Agent's raw answer and rewrites it into a structured, professional email — proper greeting using the customer's name, clean paragraphs, polite sign-off — without adding or omitting information.

Note: the final formatted reply produced by **G-mail writter** is not currently connected to a Gmail "send" node, so this workflow drafts the response but does not yet send it automatically — see below.

## Setup (about 15 minutes)

1. **Gmail** — connect Gmail OAuth2 in **Gmail Trigger** to watch your support inbox.
2. **OpenAI** — add your API key in **OpenAI Chat Model**, **OpenAI Chat Model1** and **Embeddings OpenAI**.
3. **Supabase** — add your Supabase credentials in **Supabase Vector Store**, and make sure a `documents` table with embedded knowledge-base content exists in your Supabase project.
4. **Complete the send step** — add a Gmail "Send" or "Reply" node after **G-mail writter** (wired to the original thread ID) to actually deliver the drafted response to the customer; currently the workflow stops at drafting.

## Notes

The workflow includes pinned sample data on **Gmail Trigger** (a sample refund-policy question from `support@example.com` to `customer@example.com`) used for testing — these are placeholder addresses, not real credentials or contacts.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0(["Gmail Trigger<br/><small>gmailTrigger</small>"])
    N1["Edit Fields<br/><small>set</small>"]
    N2["AI Agent<br/><small>agent</small>"]
    N3["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
    N4["Simple Memory<br/><small>memoryBufferWindow</small>"]
    N5["Supabase Vector Store<br/><small>vectorStoreSupabase</small>"]
    N6["Embeddings OpenAI<br/><small>embeddingsOpenAi</small>"]
    N7["G-mail writter<br/><small>agent</small>"]
    N8["OpenAI Chat Model1<br/><small>lmChatOpenAi</small>"]
    N0 --> N1
    N1 --> N2
    N2 --> N7
    N3 -.languageModel.-> N2
    N4 -.memory.-> N2
    N5 -.tool.-> N2
    N6 -.embedding.-> N5
    N8 -.languageModel.-> N7

    class N0 trigger
    class N3,N4,N5,N6,N8 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
