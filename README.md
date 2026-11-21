# NASER AI MEDIA ENGINE
### Fully Autonomous AI-Powered Media, History, Science & Knowledge Publishing Platform
**Publication Hub:** [https://naserkhan.substack.com](https://naserkhan.substack.com)

---

## 🌟 Overview

The **Naser AI Media Engine** is a fully autonomous digital media company engineered to operate entirely through **GitHub Actions** at **₹0 monthly recurring cost**.

It discovers compelling subjects, conducts factual research, writes original documentary-grade articles, renders professional magazine covers, publishes newsletter drafts, syndicates short notes, and tracks performance without requiring a VPS or local computer.

---

## 🏛 Editorial Philosophy & Categories

The publication’s identity is **an intellectual curiosity and knowledge magazine exploring humanity, history, science, technology, philosophy, psychology, nature, existence and imagination.**

| Category | Allocation | Focus |
|---|---:|---|
| **History & Extraordinary Personalities** | **50%** | Conquerors, emperors, scientists, philosophers, visionaries, turning points, blunders, and psychological deep-dives. |
| **Science, AI & Technology** | **15%** | Quantum physics, 4th dimension, space exploration, mathematics, neuroscience, and AGI. |
| **Philosophy & Psychology** | **12%** | Stoicism, existentialism, cognitive biases, dark psychology, decision making, consciousness. |
| **Entrepreneurship & Billionaire Mindsets** | **8%** | Strategic moats, asymmetric risk, failures, leadership psychology, case studies. |
| **Human Biology & Nature** | **5%** | Brain architecture, DNA, evolution, sensory adaptations, mathematical patterns in nature. |
| **Horror, Sci-Fi & Mysteries** | **5%** | Philosophical speculative fiction, alternate timelines, space enigmas (labeled fiction). |
| **Quotes, Puzzles & Mind Games** | **5%** | Verified historical quotations, chess paradoxes, logic puzzles, reader challenges. |

---

## ⚙️ Core Architecture

```
naser-ai-media-engine/
├── .github/
│   └── workflows/
│       ├── daily-publishing.yml      # 9:00 AM IST: Research, write, composite banner & publish
│       ├── daily-discovery.yml       # 8:30 AM IST: Discover & score candidate topics
│       └── notes-generation.yml      # 12:30, 3:30, 6:00 PM IST: Micro-notes & quotes
├── config/
│   ├── settings.json                 # Category allocations, word limits, schedules
│   └── branding.json                 # Colors, dimensions, typography rules
├── engine/
│   ├── discovery.py                  # Seed bank + dynamic topic discovery
│   ├── research.py                   # Wikipedia REST API fact verification & citations
│   ├── topic_scoring.py              # Curiosity, importance, uniqueness scoring
│   ├── writer.py                     # Multi-angle long-form essay drafting
│   ├── quality_check.py              # Word counts, anti-hallucination, cliche filter
│   ├── image_engine.py               # Archival sourcing + Pillow magazine compositor
│   ├── quote_generator.py            # Verified quotes and logic puzzles
│   ├── publisher.py                  # Multi-platform master publishing coordinator
│   └── notes_generator.py            # Substack Notes & micro-content generator
├── integrations/
│   ├── cookie_manager.py             # Netscape/JSON cookie parser
│   ├── llm_gateway.py                # Groq + Gemini + OpenRouter failover router
│   ├── substack_publisher.py         # Substack drafts, articles & Notes integration
│   ├── twitter_publisher.py          # X/Twitter posting
│   ├── buttondown_publisher.py       # Buttondown newsletter integration
│   ├── telegram_publisher.py         # Telegram Channel broadcast bot
│   └── wiki_archive.py               # Wikimedia Commons & Wikipedia API
├── database/
│   ├── schema.sql                    # SQLite schema (topics, articles, publications, logs)
│   ├── db.py                         # Atomic SQLite helper with deduplication
│   └── media_engine.db               # Version-controlled persistent database
├── assets/fonts/                     # Bundled Playfair Display & Cinzel fonts
├── articles/                         # Markdown archive of all published articles
└── images/                           # Generated 1200x600 banners and 1080x1080 social cards
```

---

## 🔑 GitHub Secrets Configuration

To run autonomously on GitHub Actions, add these secrets to your repository (**Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions**):

| Secret Name | Description | Required? |
|---|---|---|
| `COOKIES_TXT` | Paste the entire content of your exported Netscape `cookies.txt` file (contains Substack, Twitter, Medium, Buttondown). | **Recommended** |
| `GROQ_API_KEY` | Groq API Key (from [console.groq.com](https://console.groq.com)) for ultra-fast Llama-3.3-70B writing. | **Recommended** |
| `GEMINI_API_KEY` | Google AI Studio API Key (from [aistudio.google.com](https://aistudio.google.com)) for 1,500 free requests/day fallback. | Optional |
| `TELEGRAM_BOT_TOKEN` | Free Telegram bot token from `@BotFather` for mobile subscriber broadcasts. | Optional |
| `TELEGRAM_CHAT_ID` | Telegram Channel ID (e.g. `@yourchannel` or `-100...`). | Optional |
| `BUTTONDOWN_API_KEY` | Buttondown API token (from [buttondown.email/settings/programming](https://buttondown.email/settings/programming)). | Optional |

---

## 🚀 Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Check platform authentication
python main.py test-auth

# 3. Discover topics
python main.py discover

# 4. Generate and publish today's feature article
python main.py publish

# 5. Dispatch a curiosity note
python main.py note --slot afternoon
```

---

## 🛡 Factual Integrity & Zero Hallucination Policy

- All biographical timelines and dates are cross-referenced with the **Wikipedia Knowledge Base** before drafting.
- Images prioritize genuine historical public-domain artwork and museum photography from **Wikimedia Commons** and **The Met Open Access**.
- Quotations are verified against primary literature; AI-generated reflections are never attributed to historical figures.
- Extensively tested quality-assurance filter eliminates generic AI cliches ("delve into", "beacon of hope", "in conclusion").
