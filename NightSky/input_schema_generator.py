import json
from typing import get_origin, get_args, Optional, Union
from pydantic import BaseModel



def get_type_info(field_type):
    origin = get_origin(field_type)
    if origin is Union:
        # Handle Optional types (Union[T, None])
        args = get_args(field_type)
        if len(args) == 2 and args[1] is type(None):
            return get_type_info(args[0])
    if origin is dict:
        key_type, value_type = get_args(field_type)
        return {
            "type": "object",
            "additionalProperties": get_type_info(value_type),
            "propertyNames": {
                "type": "string"
            }
        }
    elif origin is list:
        item_type = get_args(field_type)[0]
        return {
            "type": "array",
            "items": get_type_info(item_type)
        }
    elif isinstance(field_type, type):
        if issubclass(field_type, BaseModel):
            return parse_pydantic_model(field_type)
        elif field_type is str:
            return {"type": "string"}
        elif field_type is int:
            return {"type": "integer"}
        elif field_type is float:
            return {"type": "number"}
        elif field_type is bool:
            return {"type": "boolean"}
    return {"type": "object"}  # Default to object for unknown types

def parse_pydantic_model(model_class):
    properties = {}
    required = []
    for name, field in model_class.model_fields.items():
        properties[name] = get_type_info(field.annotation)
        if field.is_required():
            required.append(name)
    
    schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    
    return schema

def generate_input_schema(agent_state_class):
    return parse_pydantic_model(agent_state_class)

if __name__ == "__main__":

    # agent_state.py
    from pydantic import BaseModel, Field
    from typing import Dict, Any, Optional, List

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


    input_schema = generate_input_schema(AgentState)
    
    with open("input_schema.json", "w") as f:
        json.dump(input_schema, f, indent=2)
    
    print("input_schema.json has been generated successfully.")
