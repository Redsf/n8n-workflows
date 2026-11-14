# Personal Shopper RAG Chatbot (WooCommerce)

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A conversational shopping assistant that sits in front of a WooCommerce store, answering both general store questions (hours, address, policies) and product-specific queries (search by keyword, price range, SKU, or category) from the same chat window. It routes each message to the right tool automatically instead of forcing the shopper through a separate search form.

Built for e-commerce brands that want a single chat widget to replace both a FAQ page and a product search bar, without maintaining two separate systems.

## What it does

1. **When chat message received** starts the conversation from n8n's chat trigger.
2. **Edit Fields** normalizes the incoming payload down to `sessionId` and `chatInput`.
3. **Information Extractor** (backed by **OpenAI Chat Model2**) reads the message and decides whether it's a product search. If so, it pulls out keyword, min/max price, SKU, and category into a structured JSON object.
4. **AI Agent** receives that structured output plus the original message and decides which tool to call:
   - **personal_shopper** — a **WooCommerce Tool** node (`getAll` operation) that searches live store inventory using the extracted SKU, keyword, min/max price, filtered to `stockStatus: instock`.
   - **RAG** — a **Vector Store Tool** ("informazioni_negozio") backed by **Qdrant Vector Store** (retrieval mode), **Embeddings OpenAI**, and **OpenAI Chat Model1**, used for general store questions like opening hours or address.
   - **Calculator** — a generic math tool for price/quantity calculations.
   - **Window Buffer Memory** keeps short-term conversational context, and **OpenAI Chat Model** powers the agent's own reasoning.
5. The agent's system prompt explicitly tells it to call `personal_shopper` when the extractor's `search` flag is true, and to fall back to `RAG` for store-related questions.

**Ingestion (separate manual-trigger branch, run before going live):**

1. **When clicking 'Test workflow'** kicks off ingestion.
2. **HTTP Request** clears any existing points from the Qdrant collection (`points/delete`).
3. **Google Drive2** → **Google Drive1** list and fetch the source documents (store policy/info files).
4. **Qdrant Vector Store1** (insert mode) embeds and stores them, using **Embeddings OpenAI3** for vectors, **Default Data Loader2** to read the binary, and **Token Splitter1** to chunk text.

## Sample request

This workflow uses n8n's built-in chat trigger. Send a message through the chat panel on **When chat message received**:

```
Do you have any black leather bags under 80 euros?
```

or a general question:

```
What time do you close on Saturdays?
```

The Information Extractor turns the first message into something like:

```json
{
  "search_intent": true,
  "search_params": [
    { "type": "keyword", "value": "bags" },
    { "type": "max_price", "value": "80" }
  ]
}
```

which the agent then forwards to the `personal_shopper` WooCommerce tool.

## Setup (~20 minutes)

1. **OpenAI** — add your API key to **OpenAI Chat Model**, **OpenAI Chat Model1**, **OpenAI Chat Model2**, **Embeddings OpenAI**, and **Embeddings OpenAI3**.
2. **WooCommerce** — add store API credentials (consumer key/secret) to the **personal_shopper** node.
3. **Qdrant** — add API credentials to **Qdrant Vector Store** and **Qdrant Vector Store1**, and to the **HTTP Request** node used to clear the collection. Create the collection in Qdrant first, and replace the placeholder `QDRANTURL`/collection-name values used across the ingestion branch.
4. **Google Drive** — add OAuth2 credentials to **Google Drive1** and **Google Drive2** for pulling the store-info documents to embed.
5. **Run ingestion first** — trigger **When clicking 'Test workflow'** once so the Qdrant collection has content before the chat agent goes live. Re-run it whenever the source documents change; there's no scheduled re-sync.
6. **Adjust the store persona** — the system prompts on **Information Extractor** and **AI Agent** are written for a shoe/bag/clothing retailer (and partly in Italian). Rewrite them to match your actual product catalog and language before deploying.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["When chat message received"]
        N0(["When chat message received<br/><small>chatTrigger</small>"])
        N1["Window Buffer Memory<br/><small>memoryBufferWindow</small>"]
        N2["Calculator<br/><small>toolCalculator</small>"]
        N3["Edit Fields<br/><small>set</small>"]
        N4["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
        N5["RAG<br/><small>toolVectorStore</small>"]
        N6["Qdrant Vector Store<br/><small>vectorStoreQdrant</small>"]
        N7["Embeddings OpenAI<br/><small>embeddingsOpenAi</small>"]
        N8["OpenAI Chat Model1<br/><small>lmChatOpenAi</small>"]
        N9["personal_shopper<br/><small>wooCommerceTool</small>"]
        N10["Information Extractor<br/><small>informationExtractor</small>"]
        N11["OpenAI Chat Model2<br/><small>lmChatOpenAi</small>"]
        N20["AI Agent<br/><small>agent</small>"]
    end
    subgraph G1 ["When clicking ‘Test workflow’"]
        N12["Google Drive2<br/><small>googleDrive</small>"]
        N13["Google Drive1<br/><small>googleDrive</small>"]
        N14["Embeddings OpenAI3<br/><small>embeddingsOpenAi</small>"]
        N15["Default Data Loader2<br/><small>documentDefaultDataLoader</small>"]
        N16["Token Splitter1<br/><small>textSplitterTokenSplitter</small>"]
        N17(["When clicking ‘Test workflow’<br/><small>manualTrigger</small>"])
        N18["HTTP Request<br/><small>httpRequest</small>"]
        N19["Qdrant Vector Store1<br/><small>vectorStoreQdrant</small>"]
    end
    N3 --> N10
    N18 --> N12
    N13 --> N19
    N12 --> N13
    N10 --> N20
    N0 --> N3
    N17 --> N18
    N5 -.tool.-> N20
    N2 -.tool.-> N20
    N16 -.textSplitter.-> N15
    N9 -.tool.-> N20
    N7 -.embedding.-> N6
    N4 -.languageModel.-> N20
    N14 -.embedding.-> N19
    N8 -.languageModel.-> N5
    N11 -.languageModel.-> N10
    N6 -.vectorStore.-> N5
    N15 -.document.-> N19
    N1 -.memory.-> N20

    class N0,N17 trigger
    class N1,N2,N4,N5,N6,N7,N8,N9,N11,N14,N15,N16 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
