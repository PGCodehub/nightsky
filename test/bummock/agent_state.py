# agent_state.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional , List

class TavilySearchState(BaseModel):
    search_depth: str = "basic"
    requests_remaining: int = 100
    last_search_time: Optional[float] = None
    cache: Dict[str, Any] = Field(default_factory=dict)

class FirecrawlState(BaseModel):
    requests_remaining: int = 100
    last_scrape_time: Optional[float] = None
    cache: Dict[str, Any] = Field(default_factory=dict)
    scrapelist: List[str] = Field(default_factory=list)
    

class SearchPhrase(BaseModel):
    phrase: str
    strategy: str

class SearchStrategy(BaseModel):
    search_phrases: List[SearchPhrase]
    additional_information: str


class ResearchResult(BaseModel):
    url: str
    content: str
    title: str
    context: Optional[str] = None

class AgentState(BaseModel):
    input_query: str
    search_strategy: SearchStrategy
    tavily_state: TavilySearchState
    firecrawl_state: FirecrawlState
    research_results: Dict[str, ResearchResult] = Field(default_factory=dict)
    final_report: Optional[str] = None
    review_feedback: Optional[str] = None
    review_pass: Optional[bool] = None
    next_agent: Optional[str] = None

