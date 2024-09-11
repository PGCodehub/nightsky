planner_prompt_template = """
As an AI Search Strategy Planner, your task is to create a comprehensive multi-search strategy based on the given input and any provided feedback. 

Consider the following aspects:
1. Generate a list of relevant search phrases for information extraction from the internet
2. For each search phrase, develop a specific strategy or goal that explains what kind of information we're trying to extract
3. Identify any additional information, terms, or filters that could enhance the overall search process
4. If feedback is provided, incorporate it to refine and improve the search strategy

Ensure that the search phrases cover different aspects of the topic and that the strategies are specific and varied. Address any gaps or issues identified in the feedback, if available.

Input: {input_data}

Please provide a detailed multi-search strategy following the structure.
"""

planner_guided_json = {
    "type": "object",
    "properties": {
        "search_term": {
            "type": "string",
            "description": "The most relevant search term to start with"
        },
        "overall_strategy": {
            "type": "string",
            "description": "The overall strategy to guide the search process"
        },
        "additional_information": {
            "type": "string",
            "description": "Any additional information to guide the search including other search terms or filters"
        }
    },
    "required": ["search_term", "overall_strategy", "additional_information"]
}


# Separate variable for the function definition
search_strategy_function = {
    "name": "generate_search_strategy",
    "description": "Generate a multi-search strategy with multiple search phrases and their corresponding strategies",
    "parameters": {
        "type": "object",
        "properties": {
            "search_phrases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "phrase": {
                            "type": "string",
                            "description": "A specific search phrase for information extraction"
                        },
                        "strategy": {
                            "type": "string",
                            "description": "The strategy or goal for this search phrase, explaining what information we're trying to extract"
                        }
                    },
                    "required": ["phrase", "strategy"]
                },
                "description": "List of search phrases and their corresponding strategies"
            },
            "additional_information": {
                "type": "string",
                "description": "Any additional information to guide the overall search process, including general terms or filters"
            }
        },
        "required": ["search_phrases", "additional_information"]
    }
}


# Updated external prompt template with example
REPORTER_PROMPT_TEMPLATE = """
Based on the following research results, provide a comprehensive response to the query: "{query}"

Research Results:
{research_summary}

Structure your response as follows:
Based on the information gathered, here is the comprehensive response to the query:
"[Your response here]"

Sources:
[1] [First source URL]
[2] [Second source URL]
...

Ensure that your response is well-structured, informative, and directly addresses the query. Include relevant source citations in the format [1], [2], etc.

Here's an example of the expected format:

Based on the information gathered, here is the comprehensive response to the query:
"The sky appears blue because of a phenomenon called Rayleigh scattering, which causes shorter wavelengths of 
light (blue) to scatter more than longer wavelengths (red) [1]. This scattering causes the sky to look blue most of 
the time [1]. Additionally, during sunrise and sunset, the sky can appear red or orange because the light has to 
pass through more atmosphere, scattering the shorter blue wavelengths out of the line of sight and allowing the 
longer red wavelengths to dominate [2]."

Sources:
[1] https://example.com/science/why-is-the-sky-blue
[2] https://example.com/science/sunrise-sunset-colors

Please follow this format and style in your response, adapting it to the specific query and research results provided.
"""


# Updated combined prompt template with correct node names
REVIEWER_SYSTEM_PROMPT = """
You are a reviewer and router in a research workflow. Your task is to review the reporter's response to a research question, provide feedback, and determine the next step in the workflow.

When reviewing, consider the following aspects:
1. Comprehensiveness of the response
2. Proper use of citations
3. Relevance to the research question
4. Overall quality and clarity of the report

Based on your review, you will decide the next step in the workflow:
- SearchStrategyPlanner: If new information is required
- Researcher: If different or additional sources should be consulted
- Reporter: If the report needs improvement in formatting, style, clarity, or comprehensiveness
- End: If the review passes and no further changes are needed

Provide your review and decision using the specified function call.
"""


REVIEWER_PROMPT_TEMPLATE_OLD =  """
You are a reviewer and router. Your task is to review the reporter's response to the research question, provide feedback, and then determine the next step in the workflow.

Here is the reporter's response:
Reporter's response: {reporter_response}

Your feedback should include reasons for passing or failing the review and suggestions for improvement.
You should consider the previous feedback you have given when providing new feedback.

Current date and time: {current_datetime}

First, provide your review in the following JSON format:
{{
    "feedback": "Your detailed feedback here",
    "pass_review": true/false,
    "comprehensive": true/false,
    "citations_provided": true/false,
    "relevant_to_research_question": true/false
}}

Then, based on your review, determine the next agent to route to. Choose one of the following: SearchStrategyPlanner, Researcher, Reporter, or End.

Criteria for Choosing the Next Agent:
- SearchStrategyPlanner: If new information is required.
- Researcher: If a different source should be selected or additional research is needed.
- Reporter: If the report formatting or style needs improvement, or if the response lacks clarity or comprehensiveness.
- End: If the review passes (pass_review is true).

Provide your routing decision in the following JSON format:
{{
    "next_agent": "SearchStrategyPlanner/Researcher/Reporter/End"
}}

Combine both JSON responses into a single JSON object for your final response.
"""
