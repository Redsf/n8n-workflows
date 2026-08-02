# Document to Study Notes (Mistral + Qdrant)

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A folder-watching pipeline that turns any dropped-in document (PDF, DOCX, or plain text) into a set of study aids — a study guide, a briefing document, and a timeline — using retrieval-augmented generation. Files land in a watched directory, get summarized and embedded into a Qdrant vector store, then get interviewed by an LLM chain that generates each note type from the source material, writing finished Markdown files back next to the original.

Built for anyone processing recurring source material (course readings, meeting transcripts, research papers) who wants consistent, structured study notes generated automatically instead of summarizing by hand.

## What it does

1. **Local File Trigger** fires whenever a new file is added under `/home/node/storynotes/context`, using polling with symlink support.
2. **Settings** derives `project` (the subfolder name), `path`, and `filename` from the trigger's file path.
3. **Import File** loads the file's binary content, then **Get FileType** (Switch) branches to the matching extractor — **Extract from PDF**, **Extract from DOCX**, or **Extract from TEXT** — all converging on **Prep Incoming Doc**, which copies the extracted text into a `data` field.
4. Two things happen in parallel from there:
   - **Qdrant Vector Store** (insert mode, collection `storynotes`) embeds and stores the document, using **Embeddings Mistral Cloud** for vectors, **Default Data Loader** to read `data` (tagged with `project`/`filename` metadata), and **Recursive Character Text Splitter** (2000-char chunks) to split it first.
   - **Summarization Chain** (backed by **Mistral Cloud Chat Model1**, 4000-char chunks) produces a condensed summary of the same document.
5. **Merge** (chooseBranch) waits for both paths into **Prep For AI**, which assembles a record with `id` (a hash of the filename), `project`, `path`, `name`, and the generated `summary`.
6. **Get Doc Types** (raw JSON) defines the three note templates — Study Guide, Timeline, Briefing Doc — each with a `filename` and instructional `description`. **Split Out Doc Types** turns this into one item per template, and **For Each Doc Type...** (Split In Batches) loops over them.
7. Per template, on the loop's "generate" output:
   - **Interview** (LLM chain on **Mistral Cloud Chat Model**, with **Item List Output Parser**) generates 5 questions worth asking of the summary to build that note type.
   - **Split Out** breaks the questions into items, and **Discover** (**Question & Answer Retrieval Chain**, using **Vector Store Retriever** over **Qdrant Vector Store1**/**Embeddings Mistral Cloud1**, powered by **Mistral Cloud Chat Model2**) answers each against the embedded document.
   - **Aggregate** collects the answers, and **Generate** (LLM chain on **Mistral Cloud Chat Model3**) writes the final Markdown note from the template's title/description plus the aggregated answers.
   - **2secs** (Wait) pauses briefly before **For Each Doc Type...** loops to the next template — a rate-limit buffer for the Mistral API.
8. On the loop's other output, **Get Generated Documents** captures `data`, `path`, and `filename`, **To Binary** converts the Markdown text to a file, and **Export to Folder** saves it next to the source document, named as a truncated filename plus template title.

## Sample input

This workflow is triggered by a filesystem event, not a webhook or chat message. To trigger it, drop a file into the watched folder structure:

```
/home/node/storynotes/context/<project-name>/lecture-notes.pdf
```

The `project` field comes from the path segment (`path.split('/').slice(0,4)[3]`), and `filename` from the final segment — so the folder layout under the watched root matters, not just the trigger config. Supported inputs are PDF, DOCX (via the `ods` extraction operation), and plain text; anything else falls through unextracted.

## Setup (about 15 minutes)

1. **Mistral Cloud API** — add credentials to every Mistral node: **Embeddings Mistral Cloud**, **Embeddings Mistral Cloud1**, **Mistral Cloud Chat Model** through **Mistral Cloud Chat Model3** (currently reference a shared "Mistral Cloud account" credential — replace with your own key).
2. **Qdrant** — add API credentials to **Qdrant Vector Store** and **Qdrant Vector Store1**, and create a collection named `storynotes` in your Qdrant instance (both nodes reference it by name).
3. **Local File Trigger path** — update the hardcoded watch path `/home/node/storynotes/context` to a directory that exists and is readable inside your n8n container/host; if running in Docker, it must be a mounted volume.
4. **Export destination** — **Export to Folder** writes generated notes into the same folder as the source file, so that directory must also be writable by the n8n process.
5. **Note templates** — the three study-aid types are hardcoded in **Get Doc Types**'s raw JSON. Add, remove, or edit entries there to change what gets generated.
6. **Model choice** — several Chat Model nodes pin `open-mixtral-8x7b` explicitly while **Mistral Cloud Chat Model2** uses the credential's default; align these for consistent behavior.
7. **Rate limiting** — the **2secs** Wait node is a fixed delay between template generations; increase it if you hit Mistral API rate limits with larger document sets or more templates.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0(["Local File Trigger<br/><small>localFileTrigger</small>"])
    N1["Default Data Loader<br/><small>documentDefaultDataLoader</small>"]
    N2["Recursive Character Text Splitter<br/><small>textSplitterRecursiveCharacterTextSplitter</small>"]
    N3["Embeddings Mistral Cloud<br/><small>embeddingsMistralCloud</small>"]
    N4["Mistral Cloud Chat Model<br/><small>lmChatMistralCloud</small>"]
    N5["Mistral Cloud Chat Model1<br/><small>lmChatMistralCloud</small>"]
    N6["Prep Incoming Doc<br/><small>set</small>"]
    N7["Settings<br/><small>set</small>"]
    N8["Merge<br/><small>merge</small>"]
    N9["Get Doc Types<br/><small>set</small>"]
    N10["Split Out Doc Types<br/><small>splitOut</small>"]
    N11["For Each Doc Type...<br/><small>splitInBatches</small>"]
    N12["Item List Output Parser<br/><small>outputParserItemList</small>"]
    N13["Vector Store Retriever<br/><small>retrieverVectorStore</small>"]
    N14["Embeddings Mistral Cloud1<br/><small>embeddingsMistralCloud</small>"]
    N15["Qdrant Vector Store1<br/><small>vectorStoreQdrant</small>"]
    N16["Mistral Cloud Chat Model2<br/><small>lmChatMistralCloud</small>"]
    N17["Split Out<br/><small>splitOut</small>"]
    N18["Aggregate<br/><small>aggregate</small>"]
    N19["Mistral Cloud Chat Model3<br/><small>lmChatMistralCloud</small>"]
    N20["Discover<br/><small>chainRetrievalQa</small>"]
    N21["2secs<br/><small>wait</small>"]
    N22["Get Generated Documents<br/><small>set</small>"]
    N23["Generate<br/><small>chainLlm</small>"]
    N24["Prep For AI<br/><small>set</small>"]
    N25["To Binary<br/><small>convertToFile</small>"]
    N26["Export to Folder<br/><small>readWriteFile</small>"]
    N27{{"Get FileType<br/><small>switch</small>"}}
    N28["Import File<br/><small>readWriteFile</small>"]
    N29["Extract from PDF<br/><small>extractFromFile</small>"]
    N30["Extract from DOCX<br/><small>extractFromFile</small>"]
    N31["Extract from TEXT<br/><small>extractFromFile</small>"]
    N32["Summarization Chain<br/><small>chainSummarization</small>"]
    N33["Qdrant Vector Store<br/><small>vectorStoreQdrant</small>"]
    N34["Interview<br/><small>chainLlm</small>"]
    N21 --> N11
    N8 --> N24
    N20 --> N18
    N23 --> N21
    N7 --> N28
    N18 --> N23
    N34 --> N17
    N17 --> N20
    N25 --> N26
    N28 --> N27
    N24 --> N9
    N27 -->|pdf| N29
    N27 -->|docx| N30
    N27 -->|everything else| N31
    N9 --> N10
    N29 --> N6
    N30 --> N6
    N31 --> N6
    N6 --> N33
    N6 --> N32
    N0 --> N7
    N33 --> N8
    N10 --> N11
    N32 --> N8
    N11 -->|done| N22
    N11 -->|loop| N34
    N22 --> N25
    N1 -.document.-> N33
    N15 -.vectorStore.-> N13
    N13 -.retriever.-> N20
    N12 -.outputParser.-> N34
    N3 -.embedding.-> N33
    N4 -.languageModel.-> N34
    N14 -.embedding.-> N15
    N5 -.languageModel.-> N32
    N16 -.languageModel.-> N20
    N19 -.languageModel.-> N23
    N2 -.textSplitter.-> N1

    class N0 trigger
    class N1,N2,N3,N4,N5,N12,N13,N14,N15,N16,N19 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
