This assignment is a to create a crew of agents that would assist me with company research for networking purposes

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
## Customizing

Create an .env file to handle your API keys
**Add your `OPENAI_API_KEY` into the `.env` file**
**Add your `SERPER_API_KEY` into the `.env` file**

```python
# Examples
# OPENAI_API_KEY=sk-
# SERPER_API_KEY=ec
```
To make sure your .env file is seen by the environment, Install python-dotenv in the same environment as your notebook:
```python
from pathlib import Path
from dotenv import load_dotenv

# point to the .env file. Adjust the path if your .env is elsewhere
load_dotenv(dotenv_path=Path.cwd() / ".env")   # loads into os.environ
```

# Sample code
```python
# pip install crewai

# Warning control
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew

import os
from utils import get_openai_api_key, pretty_print_result
from utils import get_serper_api_key

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-5-nano'
os.environ["SERPER_API_KEY"] = get_serper_api_key()


from crewai_tools import SerperDevTool, \
                         ScrapeWebsiteTool, \
                         WebsiteSearchTool

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

# -----------------------------
# Config - tweak to taste
# -----------------------------
TOP_N_OVERALL = 30  # set to 10 if you want a top-10 instead
MIN_SIGNAL_SOURCES = 2  # require at least this many sources per company
DEFAULT_REGION = "{region}"  # e.g., "US & Europe" - can be overridden at runtime
DEFAULT_TIME_WINDOW = "{time_window}"  # e.g., "last 24 months" - can be overridden
INDUSTRY = "{industry}"  # required input

CLASSIFICATION_RUBRIC = """
Stage labels:
- Big Tech: public, multi-product tech platform or incumbent with either ≥10k employees or ≥10B market cap or clear category dominance.
- Late-stage startup: Series D+ or valuation ≥1B, or ≥500 employees, or estimated revenue ≥100M.
- Mid-stage startup: Series B–C, 100–499 employees, valuation ~100M–1B, or revenue ~10–100M.
- Early-stage startup: Pre-seed–Series A, <100 employees, or revenue <10M.
Signal priority when conflict appears: funding stage, then employee count, then valuation, then revenue. Always return a confidence score.
Hard caps: output is a single ranked list of at most TOP_N_OVERALL companies overall. Do not exceed the cap.
"""

OUTPUT_SCHEMA_GUIDE = """
Final JSON array item shape:
{{
  "rank": <int 1..TOP_N_OVERALL>,
  "company": "<marketed company name>",
  "sub_industry": "<one of the mapped sub-industries>",
  "stage_label": "<Big Tech | Late-stage startup | Mid-stage startup | Early-stage startup>"
}}
Provide the final JSON and also a short, human-friendly Markdown table with the same rows.
"""


#OUTPUT_SCHEMA_GUIDE = """
#Final JSON array item shape:
#{{
#  "rank": <int 1..TOP_N_OVERALL>,
#  "company": "<canonical company name>",
#  "sub_industry": "<one of the mapped sub-industries>",
#  "stage_label": "<Big Tech | Late-stage startup | Mid-stage startup | Early-stage startup>",
#  "why_it_matters": "<one crisp sentence>",
#  "key_signals": {{
#    "funding_stage_or_round": "<text or null>",
#    "employees": "<int or null>",
#    "valuation_or_revenue": "<text or null>",
#    "notable_products_or_share": "<text or null>"
#  }},
#  "confidence": "<0.0-1.0>",
#  "sources": ["<url1>", "<url2>", "..."]  # at least MIN_SIGNAL_SOURCES items
#}}
#Provide the final JSON and also a short, human-friendly Markdown table with the same rows.
#"""

# -----------------------------
# Agents
# -----------------------------

industry_taxonomist = Agent(
    role="Industry Taxonomist",
    goal=(
        "Turn the input industry into a crisp, research-ready scope with a clean sub-industry map, "
        "inclusion-exclusion rules, synonyms, and search guidance so downstream research stays focused."
    ),
    backstory=(
        "You are a former strategy consultant turned data taxonomist. You dislike vague scopes and "
        "imprecise buckets. You write tight, unambiguous definitions and choose pragmatic sub-industries "
        "that reflect how the market actually organizes itself. You capture common aliases so search is robust. "
        "You set guardrails for region and time window and explicitly note what is out of scope."
    ),
)

research_analyst = Agent(
    role="Research Analyst",
    goal=(
        "Find and enrich the most important companies in the mapped sub-industries using credible, current sources, "
        "then assemble a clean candidate table with signals needed for stage classification and ranking."
    ),
    backstory=(
        "You are a meticulous OSINT-oriented analyst. You prefer primary and reputable sources: public filings, "
        "S-1s, investor reports, funding databases, company pages, trusted tech media, and recent industry maps. "
        "You reconcile conflicting facts and always keep source URLs. You avoid fluff and discard low-credibility sources."
    ),
)

classifier_ranker = Agent(
    role="Stage Classifier and Ranker",
    goal=(
        "Apply the rubric precisely, assign stage labels with confidence scores, rank companies across the whole industry, "
        "enforce the hard cap of TOP_N_OVERALL, and produce the final JSON plus a compact Markdown table."
    ),
    backstory=(
        "You are a former VC analyst and product manager. You are pragmatic about imperfect data, explain your choices, "
        "and keep results scannable. You do light QA: dedupe entities, fix parent vs product mixups, check that each row "
        "has enough sources, and ensure no more than TOP_N_OVERALL items make it to the final list."
    ),
)

# -----------------------------
# Tasks
# -----------------------------

map_subindustries = Task(
    description=(
        "Build a practical sub-industry map for {industry}. "
        "Output a brief scope note and a list of 6-12 sub-industries max. "
        "For each sub-industry, include: 1-line definition, common aliases, and inclusion-exclusion notes.\n\n"
        f"Region default: {DEFAULT_REGION}\n"
        f"Time window: {DEFAULT_TIME_WINDOW}\n\n"
        "Rules:\n"
        "- Use real-market groupings that practitioners recognize.\n"
        "- Keep names short and unambiguous.\n"
        "- Note key overlaps and what to exclude to avoid double counting.\n"
        "- This map will drive research and tagging for the final list.\n"
        "- Do not list any companies yet.\n"
        "Tooling note: When using the Serper search tool, pass a plain string to search_query (not a dict). Example: 'fintech sub-industry map US last 12 months'.\n"
    ),
    expected_output=(
        #"A JSON object with:\n"
        #"{\n"
        #'  "industry": "<input>",\n'
        #'  "scope_note": "<2-4 sentences>",\n'
        #'  "sub_industries": [\n'
        #'    {"name": "<name>", "definition": "<one line>", "aliases": ["a","b"], "include": "<short>", "exclude": "<short>"}\n'
        #"  ]\n"
        #"}\n"
        #"Plus a short Markdown list rendering the sub-industries."
        "Deliver as a compact Markdown table for a quick skim."
    ),
    tools=[search_tool, scrape_tool],
    agent=industry_taxonomist,
)

mine_companies = Task(
    description=(
        "Using the sub-industry map produced earlier, research the most important companies in each sub-industry of {industry}. "
        "Collect signals required for stage classification and ranking. Bias toward current scale and impact in the specified region and time window.\n\n"
        "What to capture per company:\n"
        "- Canonical name and homepage URL\n"
        "- Sub-industry tag from the map\n"
        "- One-line description and notable products\n"
        "- Funding stage or latest round, employees, valuation or revenue if available\n"
        "- At least {min_sources} credible sources with URLs and last-updated dates\n\n"
        "Quality rules:\n"
        "- Prefer primary sources and recent data. Avoid low-credibility blogs.\n"
        "- Reconcile conflicting facts. Note uncertainty briefly if needed.\n"
        "- Remove duplicates and product-level entries if a parent company is the actual entity.\n"
        "- It is fine to collect more than {top_n} candidates at this stage, but keep it tight and relevant.\n"
        "- Make sure to include all relevant companies in the search query and the final list."
        "Tooling note: When using the Serper search tool, pass a plain string to search_query (not a dict). Example: 'fintech sub-industry map US last 12 months'.\n"
    ).format(industry="{industry}", min_sources=MIN_SIGNAL_SOURCES, top_n=TOP_N_OVERALL),
    expected_output=(
        #"A JSON array named `candidates` where each item includes:\n"
        #"{\n"
        #'  "company": "<name>", "url": "<homepage>", "sub_industry": "<from map>",\n'
        #'  "description": "<one line>",\n'
        #'  "signals": {"funding_stage_or_round":"<text>", "employees":"<int or null>", "valuation_or_revenue":"<text or null>", "notable_products_or_share":"<text or null>"},\n'
        #'  "sources": [{"url":"<url>", "last_updated":"<YYYY-MM or YYYY-MM-DD>", "why_trustworthy":"<short>"}]\n'
        #"}\n"
        #"Deliver as JSON plus a compact Markdown table for a quick skim."
        "Deliver as a compact Markdown table for a quick skim."
    ),
    agent=research_analyst,
    tools=[search_tool, scrape_tool],
)

classify_and_rank = Task(
    description=(
        "Take the candidate companies and produce the single ranked list for {industry}. "
        "Apply the classification rubric and output at most " + str(TOP_N_OVERALL) + " rows overall. "
        "Each row must include a stage label and a confidence score.\n\n"
        "Do the following in order:\n"
        "1) Canonicalize and dedupe entities. Fix parent vs product labeling.\n"
        "2) Assign stage_label using the rubric below. Use available signals. If signals conflict, use the priority order.\n"
        "3) Score importance across the whole industry with a simple blend: scale (employees or revenue), traction or market share, funding stage, and mindshare. "
        "   Break ties by confidence and data recency. Keep the method simple and explain it in one sentence.\n"
        "4) Enforce hard cap of " + str(TOP_N_OVERALL) + ". Do not exceed it under any circumstance.\n"
        "5) QA pass: each company must have at least " + str(MIN_SIGNAL_SOURCES) + " credible sources. Remove rows that do not meet the bar.\n"
        "6) Produce final JSON and a short Markdown table.\n\n"
        "Classification rubric:\n"
        + CLASSIFICATION_RUBRIC + "\n\n"
        "Output format guide:\n"
        + OUTPUT_SCHEMA_GUIDE + "\n"
    ),
    expected_output=(
        "Two parts:\n"
        "1) Final JSON array named `top_list` with at most TOP_N_OVERALL items matching the schema guide.\n"
        "2) A concise Markdown table with columns: Rank, Company, Sub-industry, Stage\n"
    ),
    agent=classifier_ranker,
)

# -----------------------------
# Crew - runs tasks sequentially with these three agents
# -----------------------------

crew = Crew(
    agents=[industry_taxonomist, research_analyst, classifier_ranker],
    tasks=[map_subindustries, mine_companies, classify_and_rank],
    verbose=True,
    memory=True,
)

# Example of how you might kick it off at runtime:
result = crew.kickoff(
     inputs={
         "industry": "fintech",
         "region": "US",
         "time_window": "last 12 months",
     }
 )
print(result)
