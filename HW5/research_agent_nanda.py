#!/usr/bin/env python3
"""
Research Agent for NANDA Sandbox
Converts the CrewAI research agent to work with NANDA framework
"""

import os
import warnings
warnings.filterwarnings('ignore')

from nanda_adapter import NANDA
from crewai import Agent, Task, Crew
from langchain_anthropic import ChatAnthropic
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from utils import get_anthropic_api_key, get_serper_api_key, get_claude_model_name

# Configuration
TOP_N_OVERALL = 30
DEFAULT_REGION = "United States"
DEFAULT_TIME_WINDOW = "last 12 months"

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
Provide a human-friendly Markdown table, where companies are sorted from the lowest rank to the highest.
"""

def create_research_improvement():
    """Create the research agent function for NANDA"""
    
    # Get API keys
    anthropic_api_key = get_anthropic_api_key()
    serper_api_key = get_serper_api_key()
    
    # Set environment variables
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["SERPER_API_KEY"] = serper_api_key
    
    # Configure Claude LLM
    claude_llm = ChatAnthropic(
        api_key=anthropic_api_key,
        model=get_claude_model_name()
    )
    
    # Initialize tools
    search_tool = SerperDevTool()
    scrape_tool = ScrapeWebsiteTool()
    
    # Create agents
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
        llm=claude_llm,
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
        llm=claude_llm,
    )
    
    classifier_ranker = Agent(
        role="Stage Classifier and Ranker",
        goal=(
            "Apply the rubric precisely, assign stage labels with confidence scores, rank companies across the whole industry, "
            "enforce the hard cap of " + str(TOP_N_OVERALL) + ", and produce the final JSON plus a compact Markdown table."
        ),
        backstory=(
            "You are a former VC analyst and product manager. You are pragmatic about imperfect data, explain your choices, "
            "and keep results scannable. You do light QA: dedupe entities, fix parent vs product mixups, check that each row "
            "has enough sources, and ensure no more than " + str(TOP_N_OVERALL) +" items make it to the final list."
        ),
        llm=claude_llm,
    )
    
    # Create tasks
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
        expected_output="Deliver as a compact Markdown table for a quick skim.",
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
            "Quality rules:\n"
            "- Prefer primary sources and recent data. Avoid low-credibility blogs.\n"
            "- Reconcile conflicting facts. Note uncertainty briefly if needed.\n"
            "- Remove duplicates and product-level entries if a parent company is the actual entity.\n"
            "- It is fine to collect more than {top_n} candidates at this stage, but keep it tight and relevant.\n"
            "- Make sure to include all relevant companies in the search query and the final list."
            "Tooling note: When using the Serper search tool, pass a plain string to search_query (not a dict). Example: 'fintech sub-industry map US last 12 months'.\n"
        ).format(industry="{industry}", top_n=TOP_N_OVERALL),
        expected_output="Deliver as a compact Markdown table for a quick skim.",
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
            "4) Enforce hard cap of " + str(TOP_N_OVERALL) + " companies. Do not exceed it under any circumstance.\n"
            "5) Product a Markdown table as a final result"
            "Classification rubric:\n"
            + CLASSIFICATION_RUBRIC + "\n\n"
            "Output format guide:\n"
            + OUTPUT_SCHEMA_GUIDE + "\n"
        ),
        expected_output=(
            "A concise Markdown table with columns: Rank, Company, Sub-industry, Stage\n"
            "Not a JSON array"
        ),
        agent=classifier_ranker,
    )
    
    # Create crew
    crew = Crew(
        agents=[industry_taxonomist, research_analyst, classifier_ranker],
        tasks=[map_subindustries, mine_companies, classify_and_rank],
        verbose=True,
        memory=True,
    )
    
    def research_agent(message_text: str) -> str:
        """Research agent function that processes industry queries"""
        try:
            # Extract industry from message
            # For NANDA, the message should contain the industry name
            industry = message_text.strip()
            
            if not industry:
                return "Please provide an industry name to research (e.g., 'fintech', 'healthtech', 'edtech')."
            
            print(f"Starting research for {industry} in {DEFAULT_REGION} over {DEFAULT_TIME_WINDOW}...")
            
            # Run the crew
            result = crew.kickoff(
                inputs={
                    "industry": industry,
                    "region": DEFAULT_REGION,
                    "time_window": DEFAULT_TIME_WINDOW,
                }
            )
            
            return str(result)
            
        except Exception as e:
            error_msg = f"Error in research agent: {str(e)}"
            print(error_msg)
            return error_msg
    
    return research_agent

def main():
    """Main function to start the NANDA agent"""
    # Create the research improvement function
    research_improvement = create_research_improvement()
    
    # Initialize NANDA with the research function
    nanda = NANDA(research_improvement)
    
    # Get environment variables
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    domain = os.getenv("DOMAIN_NAME")
    
    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    if not domain:
        raise ValueError("DOMAIN_NAME environment variable is required")
    
    print("Starting Research Agent on NANDA...")
    print(f"Domain: {domain}")
    
    # Start the server
    nanda.start_server_api(anthropic_key, domain)

if __name__ == "__main__":
    main()
