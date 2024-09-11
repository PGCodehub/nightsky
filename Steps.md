# One step at a time 

1. Take example in langgraph course , try to build the same functionality of langgraph but with your code base - #Done
    
    context_history(agentic memories) - should only contain the messages in the list of dict that are feed to ai models (dict with role and content). This will be per agent - #Done
    graph_state - comman place to acess data between boxes - #Done
    meta_history - all the data results(output + metadata) we get from the each box , also should contain the index of messsage length with key as unique identifier - #Done
    openai support - write inference fucntions - #Done
    Add conditional edges -- added two types of conditional edges, one that only runs next node if condtion is met , second is branching edge which will take to node/nodes based on the condition - #Done
    claude support - extend the inference functions from openai to claude - #DoneHopefully
1.1. multi node input - #Done and fixed most of bugs of update1
    by default all the edges are required and if user specifies the edge as not required like optional , then it will not trigger the next node , only required edge will trigger the next node
    Bydefault we need make conditional edges to next node as not required edges , as they only get riggered in some cases - if i donot add to required list , then its fine i guess
2. Graph Communincation funtionality - #Done
3. Interept and Human in loop - #Done
    Human as a tool can be done , but this means llm is decided to call the human support
    Human approval before function call - yet to be done
4. GUI first version
    Create Basic UI setup - #Done
    Add the agent config json system to be able to create a graph from graph - ##Done
5. Replicate real world examples
    graph_websearch_agent
        While building i got a feeling that goal i want to achieve is create a sharable agentic flow space that anyone imporve on if it is on public space 
    SuperMemory
        Basic Rag -- llama index maybe
        Mem0
        Copali version
    TexttoSQL
        TelcoGPT
    Claude and Ollama support
    Code Change Reviewer
    Stock market helper
6. GUI second version
    code for deploy graph as api endpoint option 
    function calls to send and recieve from frontend
    Functional UI
5. multi workflow versioning
6. Add streaming 
7. 
8. RAG examples
9. parellel exectution , Asyc funcionality