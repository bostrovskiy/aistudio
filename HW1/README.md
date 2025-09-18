# Description

This assignment is a to create a crew of agents that would assist me with company research for networking purposes. The user enters a common industry name (e.g. fintech) and agents provide a list of the most prominent companies in its industry and sub-industries

# AI usage notice
AI tools like ChatGPT and Cursor have been used to produce this work. Specifically, ChatGPT was used to refine descriptions of AI agent crew (configuration, agents and tasks), whereas Cursor was used to debug the code and add certain features

# Learnings and limitations

**Learnings:**
* I have no technical backgrounds whatsoever, so while doing this exercies, I learned how to use GitHub, typical file structures (readme, utils, env, etc.) and how to code with Cursor
* I found the CrewAI course on DeepLearning.ai (https://learn.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai) particularly useful to understand the way CrewAI works
* I was able to autonomously run a crew of agents that helps me to identify importnat companies for networking outreach

**Limitations**
* I found that precision level of Agent/Tasks description significantly affects the output -- to the point that a longer and more detailed descripton can actually make results worse
* Output can be very fuzzy and uncertain -- during industry research the crew ommited important companies or highed unimportant ones higher then needed
* I was surprised by how slow the Agent Crew is and how many Serper requests they do -- up to 10 per run
* API usage costs should be closely monitored on OpenAI / Serper dashboards, costs add up pretty quickly (~10 cents per run for in OpenAI costs only) 

# Technical notes

## Installing the environment

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

Finally, install Crew AI python package (https://github.com/crewAIInc/crewAI):

```bash
pip install 'crewai[tools]'
```

## Connecting to your OpenAI / Cursor API

You need:
* API keys for OpenAI and Serper
* `.env file` that contains environment-specific data
* `utils.py` file that defines functions that call .env file

### How to get API keys

For OpenAI go to https://platform.openai.com/settings/organization/api-keys, create a new secret key, and don't forget to add money

For Serper go to http://serper.dev/api-keys, and create a new secret key

### How to add API keys to the script

Create an .env file to handle your API keys and add the following data:
* Your preferred `MODEL`
* Your `OPENAI_API_KEY`
* Your `SERPER_API_KEY`


```python
#Example of .env file
MODEL=gpt-5-nano
OPENAI_API_KEY=sk-....
SERPER_API_KEY=ec....
```
To make sure your .env file is seen by the environment, Install python-dotenv in the same environment as your notebook:
```python
from pathlib import Path
from dotenv import load_dotenv

# point to the .env file. Adjust the path if your .env is elsewhere
load_dotenv(dotenv_path=Path.cwd() / ".env")   # loads into os.environ
```

## Making sure there's a correct `utils.py` file
```python
import os
import json

def get_openai_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    return key

def get_serper_api_key():
    key = os.getenv("SERPER_API_KEY")
    if not key:
        raise ValueError("SERPER_API_KEY not found in environment variables.")
    return key

def get_openai_model_name():
    key = os.getenv("OPENAI_MODEL_NAME")
    if not key:
        raise ValueError("OPENAI_MODEL_NAME not found in environment variables.")
    return key

def pretty_print_result(result):
    import json
    print(json.dumps(result, indent=2))
```

# Agent code
```python
# pip install crewai

# Warning control
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew

import os
import importlib
import utils
importlib.reload(utils)
from utils import get_openai_api_key, get_serper_api_key, get_openai_model_name, pretty_print_result

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = get_openai_model_name()
os.environ["SERPER_API_KEY"] = get_serper_api_key()

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
#MIN_SIGNAL_SOURCES = 2  # require at least this many sources per company
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
        #"- At least {min_sources} credible sources with URLs and last-updated dates\n\n"
        "Quality rules:\n"
        "- Prefer primary sources and recent data. Avoid low-credibility blogs.\n"
        "- Reconcile conflicting facts. Note uncertainty briefly if needed.\n"
        "- Remove duplicates and product-level entries if a parent company is the actual entity.\n"
        "- It is fine to collect more than {top_n} candidates at this stage, but keep it tight and relevant.\n"
        "- Make sure to include all relevant companies in the search query and the final list."
        "Tooling note: When using the Serper search tool, pass a plain string to search_query (not a dict). Example: 'fintech sub-industry map US last 12 months'.\n"
    ).format(industry="{industry}", top_n=TOP_N_OVERALL),
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
        "5) Product a short Markdown table as a final result"
        #"5) QA pass: each company must have at least " + str(MIN_SIGNAL_SOURCES) + " credible sources. Remove rows that do not meet the bar.\n"
        #"6) Produce final JSON and a short Markdown table.\n\n"
        "Classification rubric:\n"
        + CLASSIFICATION_RUBRIC + "\n\n"
        "Output format guide:\n"
        + OUTPUT_SCHEMA_GUIDE + "\n"
    ),
    expected_output=(
        #"Two parts:\n"
        #"1) Final JSON array named `top_list` with at most TOP_N_OVERALL items matching the schema guide.\n"
        "A concise Markdown table with columns: Rank, Company, Sub-industry, Stage\n"
        "Not a JSON array"
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

# -----------------------------
# Inputs - asks for user inputs (make sure to locate the input window)
# -----------------------------

industry = input("Enter an industry you'd like to research: ")
if not industry.strip():
        industry = "fintech"  # Default industry
        print(f"Using default industry: {industry}")
else:
        print(f"Researching {industry}")

region = input("Enter the region you'd like to focus on: ")
if not region.strip():
        region = "United States"  # Default region
        print(f"Using default region: {region}")
else:
        print(f"Looking for companies in {region}")

time_window = input("Enter the time window you'd like to consider: ")
if not time_window.strip():
        time_window = "last 12 months"  # Default time_window
        print(f"Using default timeframe: {time_window}")
else:
        print(f"Timeframe: {time_window}")

#industry = "WealthTech & Goal‑Based Advisors"  # Change this to your desired industry
#region = "United States"  # Change this to your desired region
#time_window = "last 12 months"  # Change this to your desired time window

# Kick-off with error/timeout handling
import signal
import time

def timeout_handler(signum, frame):
    raise TimeoutError("CrewAI execution timed out after 10 minutes")

# Set a 10-minute timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(600)  # 10 minutes

try:
    print(f"Starting research for {industry} in {region} over {time_window}...")
    print("This may take several minutes. Please be patient...")
    
    result = crew.kickoff(
         inputs={
             "industry": industry,
             "region": region,
             "time_window": time_window,
         }
     )
    print("Research completed successfully!")
    print(result)
    
except TimeoutError:
    print("Research timed out after 10 minutes. Try reducing the scope or simplifying the tasks.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    signal.alarm(0)  # Cancel the alarm
