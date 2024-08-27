# One step at a time 

1. Take example in langgraph course , try to build the same functionality of langgraph but with your code base - #Done
    
    context_history(agentic memories) - should only contain the messages in the list of dict that are feed to ai models (dict with role and content). This will be per agent - #Done
    graph_state - comman place to acess data between boxes - #Done
    meta_history - all the data results(output + metadata) we get from the each box , also should contain the index of messsage length with key as unique identifier - #Done
    openai support - write inference fucntions - #Done
    Add conditional edges -- added two types of conditional edges, one that only runs next node if condtion is met , second is branching edge which will take to node/nodes based on the condition - #Done
    claude support - extend the inference functions from openai to claude - #DoneHopefully
1.1. multi node input 
2. SubGraph funtionality
3. Interept and Human in loop
4. GUI first version
5. Add streaming 
6. parellel exectution , Asyc funcionality