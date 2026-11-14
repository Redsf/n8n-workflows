# BambooHR Policies & Benefits Chatbot

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

An internal HR chatbot that answers employee questions about company policies and benefits by embedding BambooHR documents into a vector store, and that can also look up a specific employee or find the most senior contact in a department. Two flows share one workflow: a manual ingestion run that indexes policy PDFs from BambooHR, and a chat-driven agent that answers questions and delegates people lookups to itself as a sub-workflow.

Built for HR teams who want a single self-serve assistant that covers both "what does our 401k policy say" and "who do I contact in Finance" without a human touching either question.

## What it does

**Policy ingestion (manual trigger):**

1. **When clicking 'Test workflow'** starts the ingestion run.
2. **GET all files** pulls the full company file list from BambooHR.
3. **Filter out files from undesired categories** keeps only files in the "Company Files" category.
4. **Split out individual files** turns the file list into one item per file.
5. **Filter out non-pdf files** drops anything that isn't a PDF.
6. **Download file from BambooHR** fetches each policy PDF's binary content.
7. **Supabase Vector Store** (insert mode) embeds and stores each document, using **Embeddings OpenAI** for vectors, the **Default Data Loader** to read the binary, and the **Recursive Character Text Splitter** to chunk text before embedding.

**Chat agent (chat trigger):**

1. **Employee initiates a conversation** starts a chat session.
2. **HR AI Agent** answers using **OpenAI Chat Model** and **Window Buffer Memory** for short-term context, and has two tools available:
   - **Vector Store Tool** ("company_files") retrieves policy content from **Supabase Vector Store Retrieval**, backed by **Embeddings OpenAI1** and summarized by **OpenAI Chat Model1**.
   - **Employee Lookup Tool** calls back into this same workflow via its **AI-Powered HR Benefits and Company Policies Chatbot** execute-workflow trigger, passing either a person's name or a department name.
3. Inside the lookup sub-workflow, **Text Classifier** (powered by **OpenAI Chat Model2**) decides whether the query names a person or a department, then branches:
   - **Person path:** **GET all employees** → **Filter out other employees** (exact name match) → **Stringify employee record for response**.
   - **Department path:** **GET all employees (second path)** → **Extract departments** → **Ensure uniqueness in department list** → **Extract department** (via **OpenAI Chat Model3**, picking the closest matching department name) → **Retrieve all employees** → **Filter out other departments** → **Extract relevant employee fields** → **Identify most senior employee** (an LLM call via **OpenAI Chat Model4**, validated by the **Auto-fixing Output Parser** / **OpenAI Chat Model5** / **Structured Output Parser** chain) → **Format name for response**.
4. The agent's system prompt instructs it to try the knowledge base first for a named contact, then fall back to the department lookup, and finally to the requester's own supervisor chain if nothing else resolves.

## Sample request

This workflow uses n8n's built-in chat trigger, not a raw webhook. Open the chat panel on the **Employee initiates a conversation** node and send a message such as:

```
What's our policy on 401k matching, and who should I contact with questions?
```

or, for a people lookup:

```
Who is the most senior person in Engineering?
```

The sub-workflow trigger (**AI-Powered HR Benefits and Company Policies Chatbot**) expects `{"query": {"name": "<person or department>"}}` when called directly; the repo ships pinned test data of `{"query": {"name": "HR"}}` for this node.

## Setup (about 25 minutes)

1. **OpenAI** — add your API key to every OpenAI node: **OpenAI Chat Model** through **OpenAI Chat Model5**, **Embeddings OpenAI**, and **Embeddings OpenAI1**.
2. **BambooHR** — add API credentials to **GET all files**, **Download file from BambooHR**, **GET all employees**, **GET all employees (second path)**, and **Retrieve all employees**.
3. **Supabase** — add credentials to **Supabase Vector Store** and **Supabase Vector Store Retrieval**, and confirm the `company_files` table (with a `match_files` query function) exists in your project.
4. **Self-referencing sub-workflow** — the **Employee Lookup Tool** node calls `{{ $workflow.id }}`, i.e. this same workflow. No extra wiring needed, but don't rename or duplicate the workflow without checking that reference.
5. **Run ingestion first** — trigger **When clicking 'Test workflow'** once before going live so the vector store has content to answer from. Re-run it whenever policy PDFs change, since there's no scheduled re-sync.

Only files in the BambooHR "Company Files" category are ingested — confirm that category name matches your BambooHR account, or adjust the filter in **Filter out files from undesired categories**.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart LR
    subgraph G0 ["When clicking 'Test workflow'"]
        N0(["When clicking 'Test workflow'<br/><small>manualTrigger</small>"])
        N1["Default Data Loader<br/><small>documentDefaultDataLoader</small>"]
        N2["Embeddings OpenAI<br/><small>embeddingsOpenAi</small>"]
        N3["Recursive Character Text Splitter<br/><small>textSplitterRecursiveCharacterTextSplitter</small>"]
        N16["GET all files<br/><small>bambooHr</small>"]
        N17{{"Filter out files from undesired categories<br/><small>filter</small>"}}
        N18["Split out individual files<br/><small>splitOut</small>"]
        N19{{"Filter out non-pdf files<br/><small>filter</small>"}}
        N20["Download file from BambooHR<br/><small>bambooHr</small>"]
        N21["Supabase Vector Store<br/><small>vectorStoreSupabase</small>"]
    end
    subgraph G1 ["Employee initiates a conversation"]
        N4["Window Buffer Memory<br/><small>memoryBufferWindow</small>"]
        N5["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
        N6["Vector Store Tool<br/><small>toolVectorStore</small>"]
        N7["OpenAI Chat Model1<br/><small>lmChatOpenAi</small>"]
        N8["Embeddings OpenAI1<br/><small>embeddingsOpenAi</small>"]
        N9["Employee Lookup Tool<br/><small>toolWorkflow</small>"]
        N22(["Employee initiates a conversation<br/><small>chatTrigger</small>"])
        N23["Supabase Vector Store Retrieval<br/><small>vectorStoreSupabase</small>"]
        N38["HR AI Agent<br/><small>agent</small>"]
    end
    subgraph G2 ["AI-Powered HR Benefits and Company Policies Chatbot"]
        N10["OpenAI Chat Model2<br/><small>lmChatOpenAi</small>"]
        N11["OpenAI Chat Model3<br/><small>lmChatOpenAi</small>"]
        N12["OpenAI Chat Model4<br/><small>lmChatOpenAi</small>"]
        N13["Auto-fixing Output Parser<br/><small>outputParserAutofixing</small>"]
        N14["OpenAI Chat Model5<br/><small>lmChatOpenAi</small>"]
        N15["Structured Output Parser<br/><small>outputParserStructured</small>"]
        N24(["AI-Powered HR Benefits and Company Policies Chatbot<br/><small>executeWorkflowTrigger</small>"])
        N25{{"Text Classifier<br/><small>textClassifier</small>"}}
        N26["GET all employees<br/><small>bambooHr</small>"]
        N27{{"Filter out other employees<br/><small>filter</small>"}}
        N28["Stringify employee record for response<br/><small>set</small>"]
        N29["GET all employees (second path)<br/><small>bambooHr</small>"]
        N30["Extract departments<br/><small>aggregate</small>"]
        N31["Ensure uniqueness in department list<br/><small>set</small>"]
        N32["Extract department<br/><small>informationExtractor</small>"]
        N33["Retrieve all employees<br/><small>bambooHr</small>"]
        N34{{"Filter out other departments<br/><small>filter</small>"}}
        N35["Extract relevant employee fields<br/><small>aggregate</small>"]
        N36["Identify most senior employee<br/><small>chainLlm</small>"]
        N37["Format name for response<br/><small>set</small>"]
    end
    N0 --> N16
    N16 --> N17
    N17 --> N18
    N18 --> N19
    N19 --> N20
    N20 --> N21
    N22 --> N38
    N24 --> N25
    N25 -->|person| N26
    N25 -->|department| N29
    N26 --> N27
    N27 --> N28
    N29 --> N30
    N30 --> N31
    N31 --> N32
    N32 --> N33
    N33 --> N34
    N34 --> N35
    N35 --> N36
    N36 --> N37
    N1 -.document.-> N21
    N2 -.embedding.-> N21
    N3 -.textSplitter.-> N1
    N4 -.memory.-> N38
    N5 -.languageModel.-> N38
    N6 -.tool.-> N38
    N7 -.languageModel.-> N6
    N8 -.embedding.-> N23
    N9 -.tool.-> N38
    N10 -.languageModel.-> N25
    N11 -.languageModel.-> N32
    N12 -.languageModel.-> N36
    N13 -.outputParser.-> N36
    N14 -.languageModel.-> N13
    N15 -.outputParser.-> N13
    N23 -.vectorStore.-> N6

    class N0,N22,N24 trigger
    class N1,N2,N3,N4,N5,N6,N7,N8,N9,N10,N11,N12,N13,N14,N15,N23 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
