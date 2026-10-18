# n8n Workflow Portfolio

[![validate](https://github.com/Redsf/n8n-workflows/actions/workflows/validate.yml/badge.svg)](https://github.com/Redsf/n8n-workflows/actions/workflows/validate.yml)

A collection of 59 production-style n8n automations covering AI agents, RAG knowledge systems, e-commerce operations, real estate, and HR document processing. Each workflow lives in its own folder as a ready-to-import JSON file with a README explaining what it does, how it's wired, and how to configure it.

These solve real operational problems: recovering abandoned carts, qualifying and routing leads, extracting data from invoices, answering questions with grounded AI, and keeping teams informed without manual busywork.

> **By [Redowan Ahmed Farhan](https://github.com/Redsf)** — AI Automation Engineer. Several of these workflows are the credential-free reference builds of systems I've shipped to production for clients. The numbers below are results from those live deployments.
>
> 🏅 **Official n8n creator** — selected workflows from this portfolio are published on n8n's template marketplace: [n8n.io/creators/redowanfarhan →](https://n8n.io/creators/redowanfarhan/)

## Real-world impact

| Workflow in this repo | Where it ran | Outcome |
|---|---|---|
| [Abandoned Cart Recovery Engine](abandoned_cart_recovery_engine) | Shopify store | **14%** of abandoned carts recovered · **+9%** monthly revenue |
| [Order & Fulfillment Sync](order_fulfillment_sync_automation) | E-commerce ops | **1,500+ orders/mo** on autopilot · **−95%** entry errors · 3 hrs/day saved |
| [AI Review & Reputation Manager](ai_review_reputation_manager) | Local business | **100%** review coverage · rating climbed **4.2 → 4.7★** in 6 months |
| [Automated Invoice Processing](automated_invoice_document_processing) | Finance team | Month-end close from **3 days → near zero** |
| [Cold Email Outreach Automation](cold_email_outreach_automation) | B2B SaaS | **−87%** manual work · **10–12 meetings/mo** booked |
| [AI Applicant Screening (CV pipeline)](cv_processing_workflow) | HR / recruiting | **200+ CVs/opening** · **−80%** screening time |
| [Automated Client Ad Reporting](automated_client_ad_reporting) | Agency ops | **12 hrs/mo saved per client** · 100% reports on time |
| [AI Candidate Shortlisting (ERPNext)](candidate_shortlisting_erpnext) | HR / recruiting | **300+ applicants/role** triaged · shortlist turnaround **2 days → 20 minutes** |
| [WooCommerce AI Support Agent](woocommerce_ai_support_agent) | E-commerce store | **68%** of tickets resolved without a human touch |
| [Instagram Trend Content Generator](instagram_trend_content_generator) | Social / marketing | **3x** posting cadence with the same one-person team |
| [Zoom AI Meeting Assistant](zoom_meeting_assistant_clickup) | Client services | **100%** of meetings get follow-up tasks logged same-day |

## Architecture diagrams

Five of the flagship workflows above are broken down node-by-node with Mermaid flowcharts —
no images needed, renders directly on GitHub: **[ARCHITECTURE.md →](ARCHITECTURE.md)**

## How to use a workflow

1. Open the folder for the workflow you want.
2. Read its `README.md` for what it does, the trigger, and the setup steps.
3. In n8n, go to **Workflows → Import from File** and select the `.json` file.
4. Connect the credentials listed in the workflow's README, then activate it.

Credentials are referenced by name only. No API keys, tokens, or secrets are stored in any of these files, and every credential ID is the `REPLACE_WITH_CREDENTIAL_ID` placeholder rather than an ID from a real n8n instance.

## Quality checks

Every push runs [`scripts/validate_workflows.py`](scripts/validate_workflows.py)
across all 59 workflows, plus a gitleaks scan of the working tree.

**Blocking (fails the build):**

- Invalid JSON, or a file that isn't an n8n export
- A live API key pattern anywhere in the file
- A credential ID that isn't the public placeholder — these leak which credential a private instance used and break import for everyone else

**Advisory (reported, doesn't block):**

- No active Error Trigger — failures pass unnoticed
- Nodes not connected to anything
- Disabled nodes left on the canvas

The advisory checks are deliberately not blocking, because they describe
reliability posture rather than correctness. Worth knowing: **15 of 59
workflows currently have an active Error Trigger.** The rest will fail silently
if you activate them as-is. The validator tells you which ones on every run.

Run it locally before opening a PR:

```bash
python scripts/validate_workflows.py .
```

Add `--strict` to treat the advisory warnings as failures.

## Workflows

### AI Agents & RAG Knowledge Systems

| # | Workflow | Summary |
|---|----------|---------|
| 01 | [Multilingual AI Hotel Guest Assistant](multilingual_guest_assistant) | WhatsApp/Viber guest support agent that answers in the guest's language, grounded in a hotel knowledge base, with front-desk escalation. |
| 02 | [Financial Documents Assistant (Qdrant + Mistral AI)](financial_documents_assistant_qdrant_mistral) | Ingests financial PDFs into a Qdrant vector store using Mistral embeddings for retrieval-augmented Q&A. |
| 03 | [Autonomous AI Crawler](autonomous_ai_crawler) | Agent-driven web crawler that follows links autonomously and persists findings to Supabase. |
| 04 | [BambooHR AI Policies & Benefits Chatbot](bamboohr_policies_benefits_chatbot) | HR chatbot that answers policy and benefits questions by combining a vector store with live BambooHR employee data. |
| 05 | [RAG-Powered Internal Knowledge Chatbot](rag_internal_knowledge_chatbot) | Nightly sync from Notion and Google Drive into Pinecone, with a Slack-triggered Q&A agent. |
| 06 | [HR & IT Helpdesk Chatbot with Audio Transcription](hr_it_helpdesk_chatbot_audio_transcription) | Telegram helpdesk bot that transcribes voice notes and answers from a PGVector knowledge base. |
| 07 | [Customer Service Agent with RAG](customer_service_agent_rag) | Reads incoming support emails and drafts grounded replies from a Supabase vector store. |
| 08 | [RAG Model with Supabase & Postgres](rag_model_supabase_postgres) | Adds Telegram as a second interface and Postgres-backed chat memory on top of a Supabase RAG pipeline. |
| 09 | [Chat With Files in Supabase Storage](supabase_storage_file_chat_agent) | Agent that answers questions against files held in Supabase Storage without a separate ingestion step. |
| 10 | [Zoom AI Meeting Assistant](zoom_meeting_assistant_clickup) | Turns a Zoom recording into a mailed summary, ClickUp tasks, and a scheduled follow-up call. |
| 11 | [Branded AI Website Chatbot](branded_website_chatbot) | Embeddable chatbot that books meetings against a live calendar and routes availability requests through itself as a sub-workflow. |
| 12 | [Chat With PDFs (Cited Sources)](pdf_chat_with_citations) | Pinecone-backed PDF Q&A agent that quotes the exact source passage behind every answer. |
| 13 | [Stock Earnings Report RAG Analysis](stock_earnings_rag_analysis) | Ingests earnings-call PDFs and answers analyst questions with a Gemini + Pinecone retrieval agent. |

### Customer Communication & Support

| # | Workflow | Summary |
|---|----------|---------|
| 14 | [WhatsApp AI Sales Agent](whatsapp_ai_sales_agent) | Pinecone-grounded sales agent on WhatsApp with calendar booking and conversation memory. |
| 15 | [Cold Email Outreach Automation](cold_email_outreach_automation) | Batches prospects from a sheet, personalizes outreach with an LLM, and sends with rate limiting. |
| 16 | [Gmail AI Auto-Reply Agent](gmail_ai_auto_reply_agent) | Watches a Gmail inbox and drafts context-aware replies automatically. |
| 17 | [Gmail Customer Support Agent](gmail_customer_support_agent) | Triages and answers customer support emails with an LLM agent and conversation memory. |
| 18 | [Modular AI Email Routing Classifier](modular_email_routing_classifier) | Configurable text-classifier front end that routes incoming e-commerce emails to the right handling branch. |
| 19 | [WhatsApp AI Auto-Responder](whatsapp_ai_auto_responder) | Answers incoming WhatsApp messages automatically with an LLM agent, no manual reply needed. |
| 20 | [AI Sales Meeting Prep via WhatsApp (Apify)](whatsapp_sales_meeting_prep_apify) | Scrapes a prospect's public profile with Apify, briefs an LLM, and delivers a meeting-prep summary over WhatsApp. |
| 21 | [Customer Support Issue Classifier & Resolution](support_issue_classifier_resolution) | Classifies incoming support issues by type/severity with an AI text classifier and routes them to resolution. |
| 22 | [Email Summarization & Review Queue](email_summarization_review_queue) | Summarizes inbox email with AI and queues drafts for human review before anything sends. |
| 23 | [Outlook AI Email Assistant (Monday + Airtable)](outlook_ai_assistant_monday_airtable) | Drafts Outlook replies with contact context pulled live from Monday.com and Airtable. |
| 24 | [Business WhatsApp RAG Chatbot](whatsapp_business_rag_chatbot) | Full retrieval-augmented WhatsApp Business chatbot answering from a Qdrant knowledge base. |
| 25 | [AI Voice Chatbot for Restaurants (ElevenLabs)](voice_chatbot_elevenlabs_restaurants) | Voice-in, voice-out customer service agent for restaurants using ElevenLabs speech synthesis over an n8n RAG backend. |

### E-commerce & Operations

| # | Workflow | Summary |
|---|----------|---------|
| 26 | [Vision AI Receipt & Document Verification](vision_receipt_verification) | Validates receipt/invoice images against expected booking values with GPT-4o Vision and routes exceptions for review. |
| 27 | [Abandoned Cart Recovery Engine](abandoned_cart_recovery_engine) | Shopify checkout-abandonment recovery sequence with timed follow-ups across email and WhatsApp. |
| 28 | [Order & Fulfillment Sync Automation](order_fulfillment_sync_automation) | Syncs new Shopify orders to a database and polls delivery status, notifying customers and staff. |
| 29 | [Ecommerce Order Notifier & Logger](ecommerce_order_notifier_logger) | Webhook-driven order intake that logs to Google Sheets and alerts the team on Slack. |
| 30 | [Daily Product Pricing Monitor](daily_product_pricing_monitor) | Scheduled competitor price checks with Slack/email alerts when prices move outside range. |
| 31 | [Real-Time Inventory & Auto-Reorder Pipeline](realtime_inventory_auto_reorder_pipeline) | Monitors stock levels and uses an AI agent to decide and trigger reorders before stockouts. |
| 32 | [WooCommerce AI Support Agent](woocommerce_ai_support_agent) | Storefront support agent that answers order and product questions directly against the WooCommerce API. |
| 33 | [Personal Shopper RAG Chatbot (WooCommerce)](personal_shopper_rag_woocommerce) | Product-recommendation chatbot grounded in a Google Drive catalog via retrieval-augmented generation. |

### Real Estate & Appointment Scheduling

| # | Workflow | Summary |
|---|----------|---------|
| 34 | [Appointment Reminder Sender](appointment_reminder_sender) | Daily scheduled reminders pulled from a bookings sheet, sent by email with a Slack digest. |

### Marketing, Content & Growth

| # | Workflow | Summary |
|---|----------|---------|
| 35 | [Negative Review Monitor](negative_review_monitor) | Polls review sources on a schedule and alerts the team the moment a negative review appears. |
| 36 | [AI Review & Reputation Manager](ai_review_reputation_manager) | LLM-drafted responses to incoming reviews, batched hourly with Slack approval routing. |
| 37 | [Automated Client Ad Reporting](automated_client_ad_reporting) | Weekly ad-performance pull, summarized by an LLM, and emailed to clients automatically. |
| 38 | [Hacker News "Who is Hiring" Scraper](hacker_news_hiring_scraper) | Extracts and filters relevant job listings from the monthly HN hiring thread into Airtable. |
| 39 | [AI Content Repurposing & Social Publishing](ai_content_repurposing_social_publishing) | Turns one submitted piece of content into multiple platform-ready posts and tracks weekly performance. |
| 40 | [SEO & Competitor Intelligence Pipeline](seo_competitor_intelligence_pipeline) | Weekly SEO and competitor data pull, summarized by an LLM and delivered by email. |
| 41 | [AI LinkedIn Content Pipeline](ai_linkedin_content_machine) | Sources trending topics via Apify/SerpAPI and drafts and publishes LinkedIn posts with AI. |
| 42 | [AI Newsletter Generator (RSS → Email)](ai_newsletter_generator_rss_to_email) | Aggregates RSS feeds, curates and writes a newsletter draft, and emails it out. |
| 43 | [Comment Responder for LinkedIn](linkedin_comment_responder) | Scheduled scan of LinkedIn post comments with AI-drafted replies logged for review. |
| 44 | [LinkedIn Post Scraper](linkedin_post_scraper) | Form-triggered LinkedIn scraping and AI analysis pipeline with results written to Google Sheets. |
| 45 | [Instagram Trend Content Generator](instagram_trend_content_generator) | Finds trending topics and generates on-brand Instagram post copy and images with AI image generation. |
| 46 | [FAQ Enrichment at Scale](faq_enrichment_at_scale) | Scans website pages and auto-generates FAQ sections at scale using AI, batched for SEO content coverage. |
| 47 | [Email Subscription Service (Forms + Airtable + AI)](email_subscription_service_forms) | Form-driven newsletter sign-up pipeline that stores subscribers in Airtable and personalizes the welcome flow with AI. |
| 48 | [AI-Powered Social Media Amplifier](social_media_amplifier) | Pulls trending Hacker News/GitHub items and drafts ready-to-post Twitter/LinkedIn amplification content. |

### HR & Document Automation

| # | Workflow | Summary |
|---|----------|---------|
| 49 | [Automated Invoice & Document Processing Pipeline](automated_invoice_document_processing) | Extracts structured data from emailed invoices with an LLM and writes it to a database. |
| 50 | [AI Document & Invoice Extraction (Google Drive)](ai_document_invoice_extraction_google_drive) | Watches a Google Drive folder and extracts invoice data with GPT into Google Sheets. |
| 51 | [AI Employee Onboarding Automation](employee_onboarding_automation) | Form-triggered onboarding that generates welcome content, provisions access requests, and notifies HR/IT/manager. |
| 52 | [Job Application CV Processing Workflow](cv_processing_workflow) | Parses submitted CVs with an LLM, scores candidates, and logs structured results. |
| 53 | [Document to Study Notes (Mistral + Qdrant)](document_to_study_notes_mistral_qdrant) | Breaks down source documents into structured study notes using Mistral AI embeddings and a Qdrant vector store. |
| 54 | [Conversational AI Interview Agent](conversational_ai_interview_agent) | Runs a multi-turn conversational interview through n8n Forms, driven by an AI agent instead of a static question list. |
| 55 | [RFP Process Automation (OpenAI Assistants)](rfp_automation_openai_assistants) | Automates RFP intake and first-draft response generation using an OpenAI Assistant with file search. |
| 56 | [Invoice Extraction with Human-in-the-Loop (Cradl AI)](invoice_extraction_human_in_loop_cradl) | Extracts invoice data via Cradl AI, routes low-confidence fields to a human reviewer, and auto-trains the model from corrections. |
| 57 | [Dynamic Prompt Data Extraction (Airtable)](dynamic_prompt_data_extraction_airtable) | Generic data-extraction pipeline that pulls its prompt template from Airtable, so the extraction schema can change without touching the workflow. |
| 58 | [Resume Data Extraction & PDF Generation (Gotenberg)](resume_data_extraction_pdf_gotenberg) | Parses a submitted resume, restructures it, and renders a clean output PDF via a self-hosted Gotenberg service. |
| 59 | [AI Candidate Shortlisting (ERPNext)](candidate_shortlisting_erpnext) | Scores and shortlists job applicants stored in ERPNext using an LLM evaluation against the role's requirements. |

## Stack

Built primarily on **n8n**, with LLM providers (OpenAI, Groq, Google Gemini, Mistral, Anthropic Claude, ElevenLabs), vector stores (Pinecone, Supabase, Qdrant, PGVector), document/OCR tooling (Cradl AI, Gotenberg), and integrations spanning Shopify, WooCommerce, ERPNext, Gmail, Outlook, Slack, WhatsApp, Telegram, Google Workspace, Notion, Airtable, Monday.com, ClickUp, Cal.com, Twilio, Apify, and BambooHR.

## About the author

**Redowan Ahmed Farhan** — AI Automation Engineer building n8n workflows, AI agents, and RAG systems that automate real business operations.

- 💼 LinkedIn — [redowan-ahmed-farhan](https://linkedin.com/in/redowan-ahmed-farhan)
- 🏅 n8n creator profile — [n8n.io/creators/redowanfarhan](https://n8n.io/creators/redowanfarhan/)
- ✉️ Email — redowanfarhan@gmail.com
- 📍 Dhaka, Bangladesh · Open to freelance and full-time automation roles

## License

Released under the [MIT License](LICENSE). Workflows are shared as reference implementations — swap in your own credentials, sheet IDs, and endpoints before running them against production data.
