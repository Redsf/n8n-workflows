# Resume Data Extraction & PDF Generation (Gotenberg)

<!-- CANVAS:START -->
![Workflow canvas](canvas.png)
<!-- CANVAS:END -->

A Telegram bot that accepts an uploaded resume (PDF), extracts structured data from it with an LLM, reformats each section into HTML, renders it back into a clean PDF via Gotenberg, and sends the regenerated document back to the same Telegram chat.

Built as a reference implementation for turning unstructured resume text into a normalized, structured JSON record — and, as a bonus, demonstrating a self-hosted HTML-to-PDF pipeline that avoids paid PDF-generation APIs.

## What it does

1. **Telegram trigger** listens for incoming `message` updates on a Telegram bot.
2. **Auth** (if) checks the sender's `message.chat.id` against a hardcoded allow-listed chat ID; anything else is dropped at **No operation (unauthorized)**.
3. **Check if start message** (if) ignores the bot's initial `/start` command (routing it to **No operation (start message)**) and only proceeds for real uploads.
4. **Get file** (Telegram, `resource: file`) downloads the uploaded document using its `file_id`, and **Extract text from PDF** pulls the raw text out of the binary.
5. **Parse resume data** (LangChain LLM chain) sends that text to **OpenAI Chat Model** with the instruction to extract name, experience, technologies, etc. into "well-unified JSON," validated against **Structured Output Parser**'s JSON schema (personal_info, employment_history, education, projects, volunteering, programming_languages, foreign_languages) — with **Auto-fixing Output Parser** (backed by **OpenAI Chat Model1**) retrying/correcting the output if it doesn't conform to schema.
6. **Set parsed fields** passes the parsed JSON forward, fanning out in parallel to six section-specific nodes: **Personal info**, **Technologies**, **Employment history**, **Education**, **Projects**, **Volunteering** — plus four code nodes (**Convert employment history to HTML**, **Convert education to HTML**, **Convert projects to HTML**, **Convert volunteering to HTML**) that render each array section into an HTML fragment.
7. The set/convert outputs are progressively joined: **Merge education and employment history** and **Merge projects and volunteering** combine sibling sections, both feeding **Merge other data**; separately **Merge personal info and technologies** joins those two; both branches converge at **Merge all**.
8. **Set final data** concatenates every section's HTML fragment (personal info, employment history, education, projects, volunteering, technologies) into one `output` string separated by `<br/><br/>`.
9. **Convert raw to base64** base64-encodes that HTML string, and **Convert to HTML** (Convert to File) turns it into a binary `index.html` file.
10. **Generate plain PDF doc** posts that HTML file as multipart form data to a self-hosted **Gotenberg** instance's Chromium HTML-to-PDF endpoint (`http://gotenberg:3000/forms/chromium/convert/html`), getting a PDF binary back.
11. **Send PDF to the user** (Telegram, `sendDocument`) delivers the resulting PDF back to the original chat, named after the candidate (lowercased, spaces replaced with hyphens).

## Sample input

There's no webhook payload to construct — the "request" is a document uploaded to the Telegram bot. The Telegram trigger payload looks like:

```json
{
  "message": {
    "chat": { "id": 123456789 },
    "document": {
      "file_id": "BQACAgQAAxkBAAI...",
      "file_name": "jane_doe_resume.pdf",
      "mime_type": "application/pdf"
    }
  }
}
```

The intermediate structured extraction (validated against the JSON schema in **Structured Output Parser**) looks like:

```json
{
  "personal_info": { "name": "Jane Doe", "email": "jane@example.com", "linkedin": "linkedin.com/in/janedoe" },
  "employment_history": [
    { "position": "Senior Engineer", "company": "Acme Corp", "duration": "2021-2024", "responsibilities": ["Led platform migration", "Mentored junior engineers"] }
  ],
  "education": [ { "institution": "State University", "start_year": 2015, "degree": "B.Sc. Computer Science" } ],
  "programming_languages": { "languages": ["Python", "TypeScript"], "tools": ["Docker", "n8n"], "methodologies": ["Agile"] }
}
```

## Setup (~30 minutes)

1. **Telegram bot** — create a bot via BotFather, add a `telegramApi` credential to **Telegram trigger**, **Get file**, and **Send PDF to the user**.
2. **Hardcoded chat ID (required change)** — **Auth** compares `message.chat.id` against `0` as a placeholder; replace `0` with your own Telegram chat ID (or rework the condition entirely) or every message will be routed to **No operation (unauthorized)**.
3. **OpenAI** — add an `openAiApi` credential to **OpenAI Chat Model** (drives **Parse resume data**) and **OpenAI Chat Model1** (drives the **Auto-fixing Output Parser**). The original build used `gpt-4-turbo-preview` with JSON response mode.
4. **Gotenberg** — this workflow requires a running Gotenberg instance reachable at `http://gotenberg:3000` (the hostname implies a Docker Compose/same-network setup) for **Generate plain PDF doc** to work. Self-host it (see gotenberg.dev) or swap this HTTP call for another HTML-to-PDF provider (e.g. PDFMonkey, ApiTemplate) if you don't want to run Gotenberg yourself.
5. **Output schema customization** — the JSON schema in **Structured Output Parser** defines every field the LLM is asked to extract (personal info, employment history, education, projects, volunteering, languages/tools/methodologies, foreign languages); adjust it to match the resume fields you actually care about.
6. **HTML formatting** — the four "Convert ... to HTML" code nodes control how each section is rendered before the final PDF is generated; customize them if you want a different resume layout/styling than plain concatenated `<br/>`-separated blocks.

---

<!-- ARCHITECTURE:START -->
## Architecture

```mermaid
flowchart TD
    N0["OpenAI Chat Model<br/><small>lmChatOpenAi</small>"]
    N1["Convert education to HTML<br/><small>code</small>"]
    N2["Auto-fixing Output Parser<br/><small>outputParserAutofixing</small>"]
    N3["OpenAI Chat Model1<br/><small>lmChatOpenAi</small>"]
    N4["Structured Output Parser<br/><small>outputParserStructured</small>"]
    N5["Convert employment history to HTML<br/><small>code</small>"]
    N6["Convert projects to HTML<br/><small>code</small>"]
    N7["Convert volunteering to HTML<br/><small>code</small>"]
    N8(["Telegram trigger<br/><small>telegramTrigger</small>"])
    N9{{"Auth<br/><small>if</small>"}}
    N10["No operation (unauthorized)<br/><small>noOp</small>"]
    N11{{"Check if start message<br/><small>if</small>"}}
    N12["No operation (start message)<br/><small>noOp</small>"]
    N13["Get file<br/><small>telegram</small>"]
    N14["Extract text from PDF<br/><small>extractFromFile</small>"]
    N15["Set parsed fileds<br/><small>set</small>"]
    N16["Personal info<br/><small>set</small>"]
    N17["Technologies<br/><small>set</small>"]
    N18["Employment history<br/><small>set</small>"]
    N19["Education<br/><small>set</small>"]
    N20["Projects<br/><small>set</small>"]
    N21["Volunteering<br/><small>set</small>"]
    N22["Merge education and employment history<br/><small>merge</small>"]
    N23["Merge projects and volunteering<br/><small>merge</small>"]
    N24["Merge personal info and technologies<br/><small>merge</small>"]
    N25["Merge all<br/><small>merge</small>"]
    N26["Set final data<br/><small>set</small>"]
    N27["Convert raw to base64<br/><small>code</small>"]
    N28["Convert to HTML<br/><small>convertToFile</small>"]
    N29["Generate plain PDF doc<br/><small>httpRequest</small>"]
    N30["Send PDF to the user<br/><small>telegram</small>"]
    N31["Parse resume data<br/><small>chainLlm</small>"]
    N32["Merge other data<br/><small>merge</small>"]
    N9 -->|true| N11
    N9 -->|false| N10
    N13 --> N14
    N20 --> N23
    N19 --> N22
    N25 --> N26
    N17 --> N24
    N21 --> N23
    N16 --> N24
    N26 --> N27
    N28 --> N29
    N32 --> N25
    N8 --> N9
    N31 --> N15
    N15 --> N5
    N15 --> N1
    N15 --> N6
    N15 --> N16
    N15 --> N7
    N15 --> N17
    N18 --> N22
    N27 --> N28
    N14 --> N31
    N11 -->|true| N13
    N11 -->|false| N12
    N29 --> N30
    N6 --> N20
    N1 --> N19
    N7 --> N21
    N23 --> N32
    N5 --> N18
    N24 --> N25
    N22 --> N32
    N0 -.languageModel.-> N31
    N3 -.languageModel.-> N2
    N4 -.outputParser.-> N2
    N2 -.outputParser.-> N31

    class N8 trigger
    class N0,N2,N3,N4 aiSubnode
    classDef trigger stroke-width:3px
    classDef aiSubnode stroke-dasharray:5 3
    classDef errorPath stroke-width:3px,stroke-dasharray:2 2
    classDef disabled stroke-dasharray:1 4,opacity:0.45
```

> Shapes: rounded = trigger, hexagon = branch point. Dashed borders mark AI sub-nodes; dotted edges are the model, memory and tool connections feeding an agent. Faded nodes are disabled in this export.
<!-- ARCHITECTURE:END -->
