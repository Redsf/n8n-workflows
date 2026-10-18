# n8n workflow review: all 59 workflows

Reviewed every workflow JSON in the repo. Findings below are split into **verified defects** (I traced the
connection graph or expression and confirmed the breakage) and **hygiene** (real but uniform across the repo).

`scripts/` holds no workflow JSON, so the count is 59, not 60.


## 1. Verified defects, worst first


### `ai_document_invoice_extraction_google_drive` — BUG (19 nodes)

- `Error Handler` (code) is connected to nothing. Dead code presenting as error handling.

### `ai_linkedin_content_machine` — BROKEN (22 nodes)

- **Image branch is severed.** `Image generation` (agent) has `main: [[]]` and `Generate an image` (Gemini image node) has no inbound. The edge `Image generation -> Generate an image` is missing, so `Download Generated Image` never fires and `Upload Image to LinkedIn` runs with no binary. VERIFIED from the connections map.
- `Quality Gate Check` calls `$('Generate LinkedIn Post')`; no node by that name exists (the text agent is called `For text content`). It is inside a try/catch, so the gate silently always reports POOR confidence instead of crashing.
- `Error Handler` (code) is connected to nothing: dead code that looks like error handling on the canvas.
- Ships `pinData` for `For text content`, so a fresh import replays stale test output instead of calling the model.

### `candidate_shortlisting_erpnext` — BROKEN (23 nodes)

- **`File Type` switch declares `.pdf` / `.doc` / `.jpg` but only output 0 (`.pdf`) is wired.** `.doc` and `.jpg` resumes are silently discarded; the applicant gets no rejection and no processing. VERIFIED.
- No fallback output on that switch, so any other extension vanishes too.
- `Txt File to Text (Example)` has no inbound but feeds `Merge1`. [Likely] With Merge v3 in default append mode this resolves, but an unfed Merge input is fragile across n8n versions.
- Webhook has no authentication.

### `cold_email_outreach_automation` — BUG (21 nodes)

- `Parse Email Content` (code) is connected to nothing.
- `Is Status Pending?` drops its false branch. That is intentional filtering, but `typeValidation: strict` on `$json.Status` means a missing Airtable field throws instead of routing false.

### `faq_enrichment_at_scale` — BROKEN (29 nodes)

- **Three fully disconnected nodes: `Wordpress`, `Webflow`, `HTTP Request`.** These are the publish targets. The workflow enriches FAQs and then writes them nowhere. VERIFIED.
- `For Each Service...` main output 0 is explicitly `null` (the 'done' branch is wired to nothing).
- Two switches with no fallback output.

### `financial_documents_assistant_qdrant_mistral` — BUG (16 nodes)

- **`Has Existing Point?1` (the `file_changed` path) drops its false branch.** If a changed file has no prior point in Qdrant, the new content is never indexed. Fix: wire false -> `Remap for File_Added Flow`. VERIFIED by tracing the `Handle File Event` switch (output 0=file_deleted, 1=file_changed, 2=file_added).
- `Has Existing Point?` (the `file_deleted` path) also drops false, but that is correct: nothing to delete.
- Trigger is a manual `When clicking Test workflow`, yet `Set Variables` reads `$json.event`. Run as shipped, `event` is undefined, all three switch outputs are false and nothing happens. A Local File Trigger is needed upstream.

### `social_media_amplifier` — BUG (19 nodes)

- `Validate Generate Content` calls `JSON.parse` with no try/catch. One malformed model response kills the whole execution.
- Ships `pinData` for `Schedule Trigger`.

### `stock_earnings_rag_analysis` — BUG (15 nodes)

- **The ingestion half has no trigger.** `List Of Files To Load (Google Sheets)` -> `Loop Over Items` -> Pinecone has no inbound; the only trigger feeds the AI Agent directly. The index is never populated unless you execute that node by hand.
- `Loop Over Items` 'done' output (index 0) is wired to nothing.
- Ships `pinData` for `AI Agent`.

### `woocommerce_ai_support_agent` — BUG (31 nodes)

- `Encrypt email` (code) is connected to nothing, while `Example encrypted email` (a Set node with no inbound) feeds `Decrypt email`. The encrypt/decrypt pair is demo scaffolding that never runs against real data.
- `Webhook Example Page` has no authentication.

## 2. Minor / cosmetic


### `invoice_extraction_human_in_loop_cradl` (20 nodes)

- Two nodes share the name `Sticky Note`. Cosmetic, but n8n node names are supposed to be unique.

### `resume_data_extraction_pdf_gotenberg` (33 nodes)

- `Generate plain PDF doc` posts to a plaintext `http://` URL (Gotenberg). Fine on localhost, a credential leak over any real network.

### `vision_receipt_verification` (12 nodes)

- `Parse Extraction` and `Build Error Verdict` use the legacy `$node["..."]` syntax. It still works but is deprecated in favour of `$('...')`.
- `Document Upload Webhook` has no authentication, and it accepts file uploads.

## 3. Intentional-looking patterns I checked and cleared

These tripped my analyzer but are correct on inspection. Listing them so nobody re-raises them:

- **Sub-nodes with no inbound edge** (every `OpenAI Chat Model`, `Embeddings *`, `Window Buffer Memory`, `*Tool`, `Structured Output Parser`). In n8n these connect *outward* to the agent over `ai_*` ports. Roughly 90 apparent hits, all false.
- **`autonomous_ai_crawler`** `$('Add protocool to domain (URL)')`: that node exists inside the `URLs` toolWorkflow sub-workflow. Valid.
- **`whatsapp_sales_meeting_prep_apify`** `$('body')` / `$('title')`: jQuery selectors in a Code node (`const $ = context.jQuery`), not n8n node references. Valid.
- **IF nodes dropping a false branch** in `linkedin_post_scraper`, `negative_review_monitor`, `support_issue_classifier_resolution`, `cold_email_outreach_automation`: all are filter patterns where discarding non-matching items is the intent.
- **`realtime_inventory_auto_reorder_pipeline` `Already Reordered Today?`**: the name reads inverted (true = *not* reordered today), but the wiring is correct. Rename only.
- **`financial_documents_...` `Has Existing Point?` on the delete path**: correctly terminal.

## 4. Repo-wide hygiene

| Issue | Workflows | Why it matters |
|---|---|---|
| No `retryOnFail` on network nodes | 59/59 | Every OpenAI/HTTP/Sheets call dies on a single 429 or timeout. One checkbox per node. |
| No `onError` on network nodes | 59/59 | A single failed item aborts the whole run. |
| No `errorWorkflow` in settings | 58/59 | Defensible for a template library (the ID is instance-specific). |
| `executionOrder: v0` | 20/59 | Legacy branch ordering; parallel branches that later merge can run out of canvas order. |
| Webhook with no authentication | 12 | Publicly callable endpoints. |
| `pinData` shipped in the file | 7 | A fresh import replays stale test data instead of calling the real service. |
| Switch with no fallback output | 10 | Unmatched items vanish without trace. |

### Webhooks with no authentication

- `ai_content_repurposing_social_publishing`: 'Content Submitted'
- `candidate_shortlisting_erpnext`: 'Webhook'
- `conversational_ai_interview_agent`: 'Webhook'
- `dynamic_prompt_data_extraction_airtable`: 'Airtable Webhook'
- `ecommerce_order_notifier_logger`: 'New Order Received'
- `multilingual_guest_assistant`: 'Inbound Message Webhook'
- `rfp_automation_openai_assistants`: 'Wait for Request'
- `vision_receipt_verification`: 'Document Upload Webhook'
- `voice_chatbot_elevenlabs_restaurants`: 'Listen'
- `whatsapp_business_rag_chatbot`: 'Verify'
- `whatsapp_business_rag_chatbot`: 'Respond'
- `woocommerce_ai_support_agent`: 'Example Page'

### Workflows shipping `pinData`

- `ai_linkedin_content_machine`: ['For text content']
- `autonomous_ai_crawler`: ['Get companies']
- `bamboohr_policies_benefits_chatbot`: ['AI-Powered HR Benefits and Company Policies Chatbot']
- `customer_service_agent_rag`: ['Gmail Trigger']
- `social_media_amplifier`: ['Schedule Trigger']
- `stock_earnings_rag_analysis`: ['AI Agent']
- `zoom_meeting_assistant_clickup`: ['Execute Workflow Trigger']

### Workflows on legacy `executionOrder: v0`

`ai_content_repurposing_social_publishing`, `ai_document_invoice_extraction_google_drive`, `bamboohr_policies_benefits_chatbot`, `branded_website_chatbot`, `candidate_shortlisting_erpnext`, `conversational_ai_interview_agent`, `document_to_study_notes_mistral_qdrant`, `dynamic_prompt_data_extraction_airtable`, `email_subscription_service_forms`, `faq_enrichment_at_scale`, `outlook_ai_assistant_monday_airtable`, `pdf_chat_with_citations`, `resume_data_extraction_pdf_gotenberg`, `rfp_automation_openai_assistants`, `supabase_storage_file_chat_agent`, `support_issue_classifier_resolution`, `whatsapp_ai_auto_responder`, `whatsapp_sales_meeting_prep_apify`, `woocommerce_ai_support_agent`, `zoom_meeting_assistant_clickup`

## 5. Full roster: every workflow, with its verdict

| Workflow | Nodes | Verdict |
|---|---:|---|
| `abandoned_cart_recovery_engine` | 10 | Clean (hygiene items only) |
| `ai_content_repurposing_social_publishing` | 14 | Hygiene only: webhook-open |
| `ai_document_invoice_extraction_google_drive` | 19 | **Bug** - see above |
| `ai_linkedin_content_machine` | 22 | **BROKEN** - see above |
| `ai_newsletter_generator_rss_to_email` | 23 | Clean (hygiene items only) |
| `ai_review_reputation_manager` | 19 | Clean (hygiene items only) |
| `appointment_reminder_sender` | 6 | Clean (hygiene items only) |
| `automated_client_ad_reporting` | 13 | Clean (hygiene items only) |
| `automated_invoice_document_processing` | 14 | Clean (hygiene items only) |
| `autonomous_ai_crawler` | 12 | Hygiene only: pindata |
| `bamboohr_policies_benefits_chatbot` | 39 | Hygiene only: pindata |
| `branded_website_chatbot` | 17 | Hygiene only: switch-no-fallback |
| `candidate_shortlisting_erpnext` | 23 | **BROKEN** - see above |
| `cold_email_outreach_automation` | 21 | **Bug** - see above |
| `conversational_ai_interview_agent` | 30 | Hygiene only: webhook-open |
| `customer_service_agent_rag` | 9 | Hygiene only: pindata |
| `cv_processing_workflow` | 11 | Clean (hygiene items only) |
| `daily_product_pricing_monitor` | 15 | Clean (hygiene items only) |
| `document_to_study_notes_mistral_qdrant` | 35 | Hygiene only: switch-no-fallback |
| `dynamic_prompt_data_extraction_airtable` | 36 | Hygiene only: switch-no-fallback, webhook-open |
| `ecommerce_order_notifier_logger` | 7 | Hygiene only: webhook-open |
| `email_subscription_service_forms` | 24 | Clean (hygiene items only) |
| `email_summarization_review_queue` | 22 | Hygiene only: unreachable |
| `employee_onboarding_automation` | 16 | Clean (hygiene items only) |
| `faq_enrichment_at_scale` | 29 | **BROKEN** - see above |
| `financial_documents_assistant_qdrant_mistral` | 16 | **Bug** - see above |
| `gmail_ai_auto_reply_agent` | 5 | Clean (hygiene items only) |
| `gmail_customer_support_agent` | 5 | Clean (hygiene items only) |
| `hacker_news_hiring_scraper` | 15 | Clean (hygiene items only) |
| `hr_it_helpdesk_chatbot_audio_transcription` | 21 | Clean (hygiene items only) |
| `instagram_trend_content_generator` | 27 | Clean (hygiene items only) |
| `invoice_extraction_human_in_loop_cradl` | 20 | Minor - see above |
| `linkedin_comment_responder` | 11 | Clean (hygiene items only) |
| `linkedin_post_scraper` | 10 | Hygiene only: if-dead-branch |
| `modular_email_routing_classifier` | 13 | Clean (hygiene items only) |
| `multilingual_guest_assistant` | 15 | Hygiene only: switch-no-fallback, webhook-open |
| `negative_review_monitor` | 5 | Hygiene only: if-dead-branch |
| `order_fulfillment_sync_automation` | 17 | Clean (hygiene items only) |
| `outlook_ai_assistant_monday_airtable` | 20 | Clean (hygiene items only) |
| `pdf_chat_with_citations` | 18 | Clean (hygiene items only) |
| `personal_shopper_rag_woocommerce` | 21 | Clean (hygiene items only) |
| `rag_internal_knowledge_chatbot` | 25 | Clean (hygiene items only) |
| `rag_model_supabase_postgres` | 12 | Clean (hygiene items only) |
| `realtime_inventory_auto_reorder_pipeline` | 16 | Hygiene only: if-dead-branch |
| `resume_data_extraction_pdf_gotenberg` | 33 | Minor - see above |
| `rfp_automation_openai_assistants` | 13 | Hygiene only: webhook-open |
| `seo_competitor_intelligence_pipeline` | 12 | Clean (hygiene items only) |
| `social_media_amplifier` | 19 | **Bug** - see above |
| `stock_earnings_rag_analysis` | 15 | **Bug** - see above |
| `supabase_storage_file_chat_agent` | 22 | Hygiene only: null-branch, switch-no-fallback |
| `support_issue_classifier_resolution` | 29 | Hygiene only: if-dead-branch |
| `vision_receipt_verification` | 12 | Minor - see above |
| `voice_chatbot_elevenlabs_restaurants` | 18 | Hygiene only: webhook-open |
| `whatsapp_ai_auto_responder` | 24 | Clean (hygiene items only) |
| `whatsapp_ai_sales_agent` | 16 | Clean (hygiene items only) |
| `whatsapp_business_rag_chatbot` | 18 | Hygiene only: webhook-open |
| `whatsapp_sales_meeting_prep_apify` | 47 | Hygiene only: switch-no-fallback |
| `woocommerce_ai_support_agent` | 31 | **Bug** - see above |
| `zoom_meeting_assistant_clickup` | 22 | Hygiene only: pindata |
