# n8n workflow review and remediation

Every workflow JSON in the repo (59 of them; `scripts/` holds none) was reviewed by tracing the
connection graph and expression references, not just reading node parameters. This file records
what was found, what was fixed, and what was deliberately left alone.

## 1. Defects found and fixed

### `ai_linkedin_content_machine` — was broken in three ways

- **The image branch was severed.** `Image generation` had `main: [[]]` and `Generate an image`
  had no inbound edge, so `Download Generated Image` never fired and `Upload Image to LinkedIn`
  ran with no binary. **Fixed:** connected `Image generation -> Generate an image`.
- **`Quality Gate Check` referenced a node that does not exist.** It called
  `$('Generate LinkedIn Post')`; the text agent is named `For text content`. The call sat inside a
  try/catch, so the gate silently reported POOR confidence on every run instead of crashing.
  **Fixed:** reference corrected.
- **`Error Handler` was connected to nothing.** **Fixed:** the two LinkedIn nodes now use
  `onError: continueErrorOutput` and route their error output into it.
- **Fixed:** removed `pinData`, which replayed stale test output instead of calling the model.

### `candidate_shortlisting_erpnext` — silently discarded candidates

The `File Type` switch declared `.pdf`, `.doc` and `.jpg`, but only output 0 was wired. A `.doc`
or `.jpg` resume produced no processing and no rejection; the applicant heard nothing.
**Fixed:** `.doc`, `.jpg` and a new fallback output now route to the existing rejection node.

> Judgement call: marking these applicants Rejected is a business decision. If unsupported
> formats should instead be queued for manual review, rewire those three outputs.

### `financial_documents_assistant_qdrant_mistral` — changed files were never indexed

On the `file_changed` path, `Has Existing Point?1` dropped its false branch. A changed file with
no prior point in Qdrant was discarded. **Fixed:** false branch now routes to
`Remap for File_Added Flow`, which continues into the read-and-embed chain.

Still worth knowing: the shipped trigger is a manual one while `Set Variables` reads `$json.event`.
Run as imported, `event` is undefined and nothing happens. A Local File Trigger is needed upstream.
Left as-is because adding one requires knowing the watched directory.

### `stock_earnings_rag_analysis` — the ingestion half had no trigger

`List Of Files To Load (Google Sheets) -> Loop Over Items -> Pinecone` had no inbound edge, so the
index was never populated unless that node was executed by hand. **Fixed:** added an
`Index Earnings Reports` manual trigger feeding the ingestion chain. Also removed `pinData`.

### `social_media_amplifier` — worse than first reported

`Validate Generate Content` did not just call `JSON.parse` unguarded. After parsing, the inner
condition re-tested `$json.message.content`, the **raw string**, rather than the parsed object.
A string has no `.twitter` property, so that branch always fell through to `return {}` and the
parsed content was always discarded. **Fixed:** parse is guarded, and the check now tests the
parsed object. Also removed `pinData`.

### `ai_document_invoice_extraction_google_drive` — dead error handling

`Error Handler` held real code expecting per-node error data but was connected to nothing.
**Fixed:** the Drive download and both GPT-4o nodes now route their error output into it.

### `faq_enrichment_at_scale` — cleanup, not a defect

An earlier draft of this review called this workflow broken. **That was wrong.** `Update Row Status`
feeds `Strapi`, which is the wired publish target, so the workflow does publish. The `Wordpress`,
`Webflow` and `HTTP Request` nodes were unconfigured alternative-CMS stubs carrying no parameters
and no connections. **Removed** as dead weight. Add the node for your own CMS in their place.

## 2. Examined and deliberately left alone

- **`cold_email_outreach_automation` / `Parse Email Content`** is `disabled: true` as well as
  disconnected. That is an intentional "off" switch on a real 8.7 KB implementation, not dead code.
- **`woocommerce_ai_support_agent` / `Encrypt email`** is a manual utility you run by hand to
  produce a value for `Example encrypted email`; its partner `Decrypt email address` is disabled.
  Note it hardcodes `password = 'a random password'`, which is fine for a demo and not for anything
  else.
- **IF nodes dropping a false branch** in `linkedin_post_scraper`, `negative_review_monitor`,
  `support_issue_classifier_resolution` and `cold_email_outreach_automation` are filter patterns
  where discarding non-matching items is the intent.
- **`realtime_inventory_auto_reorder_pipeline` / `Already Reordered Today?`** reads inverted
  (true means *not* reordered today) but is wired correctly.
- **Default node names** (`AI Agent`, `Merge`, `If`, `Switch`, `Edit Fields`) are n8n's own
  convention. Renaming roughly 40 of them would churn expressions for little gain.

## 3. False positives worth recording

So nobody re-raises them:

- **Sub-nodes have no inbound edge by design.** Every `OpenAI Chat Model`, `Embeddings *`,
  `Window Buffer Memory`, `*Tool` and `Structured Output Parser` connects *outward* to its agent
  over an `ai_*` port. An early scan flagged about 90 of these; all were false.
- **`autonomous_ai_crawler`** `$('Add protocool to domain (URL)')` resolves inside the `URLs`
  toolWorkflow sub-workflow, where that node exists.
- **`whatsapp_sales_meeting_prep_apify`** `$('body')` and `$('title')` are jQuery selectors in a
  Code node (`const $ = context.jQuery`), not n8n node references.

## 4. Naming

**17 workflows had no `name` at all** and imported into n8n as blank. Every one of the 59 now
carries a name.

Each folder's `README.md` already held a curated, accurate heading, in several cases better than
anything worth inventing (`rag_model_supabase_postgres` is really a Telegram assistant;
`linkedin_post_scraper` also rewrites). So the workflow `name` is now **synced to the folder
README heading** across all 59. JSON, folder README and the root table agree.

Two headings carried informal or marketing wording and were changed in the README, the root table
and the JSON together:

| Folder | Before | After |
|---|---|---|
| `ai_linkedin_content_machine` | AI LinkedIn Content Machine | AI LinkedIn Content Pipeline |
| `whatsapp_business_rag_chatbot` | Complete Business WhatsApp RAG Chatbot | Business WhatsApp RAG Chatbot |

Node names with spelling errors, corrected along with every connection and expression reference:

| Workflow | Before | After |
|---|---|---|
| `candidate_shortlisting_erpnext` | Reume Attachment Link | Resume Attachment Link |
| `customer_service_agent_rag` | G-mail writter | Gmail Writer |
| `linkedin_post_scraper` | Varify The authenticity | Verify Authenticity |
| `support_issue_classifier_resolution` | Find Simlar Issues | Find Similar Issues |
| `cold_email_outreach_automation` | Personalize (triple space) E-mail | Personalize Email |

Left alone on purpose:

- **Default node names** (`AI Agent`, `Merge`, `If`, `Switch`, `Edit Fields`) are n8n's own
  convention. Renaming roughly 40 of them would churn expressions for little gain.
- **Folder names.** `README.md` links to them and CI walks them, so renaming is a separate change
  with its own blast radius.

## 5. Repo-wide hygiene, still outstanding

| Issue | Workflows | Note |
|---|---|---|
| No `retryOnFail` on network nodes | 59 / 59 | A per-node boolean with no external dependency. Every LLM call here will eventually meet a 429. |
| No `onError` on network nodes | 56 / 59 | One failed item aborts the whole run. |
| No `errorWorkflow` in settings | 58 / 59 | Defensible for a template library; the ID is instance-specific. |
| `executionOrder: v0` | 20 / 59 | Legacy branch ordering. |
| Webhook with no authentication | 12 | Publicly callable endpoints. |
| Switch with no fallback output | 9 | Unmatched items vanish without trace. |

These are uniform across the repo and are a deliberate follow-up rather than part of this pass.

## 6. Verification

- `python scripts/validate_workflows.py .` → **0 errors**, warnings down from 61 to 56.
- All 59 files parse as JSON and keep the repo's `indent=2` formatting.
- No stale references remain to any renamed node.
