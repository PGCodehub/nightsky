"""
NightSky AgentGraph - Branching Example
========================================

This example demonstrates conditional branching and parallel execution:
1. Branching based on data analysis
2. Parallel execution of multiple paths
3. Converging branches back to a single node
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from NightSky.AgentGraph import AgenticGraph, StartNode, EndNode


# Define data schema
class RequestData(BaseModel):
    """Schema for customer request processing"""
    customer_id: str
    request_type: str
    priority: str = "normal"
    amount: float = 0.0
    description: str = ""
    status: str = "pending"
    processing_path: List[str] = Field(default_factory=list)
    approval_required: bool = False


# Node functions
def classify_request(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify the incoming request"""
    start_data = input_data.get("Start", {})
    request = RequestData(**start_data)
    
    # Classify based on amount and type
    if request.amount > 10000:
        request.priority = "high"
    elif request.amount > 1000:
        request.priority = "medium"
    else:
        request.priority = "low"
    
    if request.amount > 5000 or request.request_type == "refund":
        request.approval_required = True
    
    request.processing_path.append("Classified")
    request.status = "classified"
    
    print(f"✓ Classified request {request.customer_id}: priority={request.priority}")
    
    return {"graph_data": request.dict(), "metahistory": None}


def handle_low_priority(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle low priority requests automatically"""
    classify_data = input_data.get("ClassifyRequest", {})
    request = RequestData(**classify_data)
    
    request.processing_path.append("AutomatedHandling")
    request.status = "auto_processed"
    
    print(f"✓ Auto-processed low priority request {request.customer_id}")
    
    return {"graph_data": request.dict(), "metahistory": None}


def handle_medium_priority(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle medium priority requests with standard process"""
    classify_data = input_data.get("ClassifyRequest", {})
    request = RequestData(**classify_data)
    
    request.processing_path.append("StandardProcessing")
    request.status = "standard_processed"
    
    print(f"✓ Standard processed medium priority request {request.customer_id}")
    
    return {"graph_data": request.dict(), "metahistory": None}


def handle_high_priority(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle high priority requests with expedited process"""
    classify_data = input_data.get("ClassifyRequest", {})
    request = RequestData(**classify_data)
    
    request.processing_path.append("ExpeditedProcessing")
    request.status = "expedited_processed"
    
    print(f"✓ Expedited processed high priority request {request.customer_id}")
    
    return {"graph_data": request.dict(), "metahistory": None}


def approval_required_check(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check if approval is needed"""
    # Get data from any of the previous processing nodes
    data = (input_data.get("HandleLowPriority") or 
            input_data.get("HandleMediumPriority") or 
            input_data.get("HandleHighPriority") or {})
    
    request = RequestData(**data)
    
    if request.approval_required:
        request.processing_path.append("PendingApproval")
        request.status = "pending_approval"
        print(f"⚠ Request {request.customer_id} requires approval")
    else:
        request.processing_path.append("ApprovalNotRequired")
    
    return {"graph_data": request.dict(), "metahistory": None}


def manager_approval(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate manager approval process"""
    approval_data = input_data.get("ApprovalCheck", {})
    request = RequestData(**approval_data)
    
    # Simulate approval decision
    request.processing_path.append("ManagerApproval")
    request.status = "approved"
    
    print(f"✓ Manager approved request {request.customer_id}")
    
    return {"graph_data": request.dict(), "metahistory": None}


def finalize_request(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the request - convergence point"""
    # Can receive data from either ApprovalCheck or ManagerApproval
    data = input_data.get("ManagerApproval") or input_data.get("ApprovalCheck") or {}
    
    request = RequestData(**data)
    request.processing_path.append("Finalized")
    request.status = "completed"
    
    print(f"✅ Finalized request {request.customer_id}")
    
    return {"graph_data": request.dict(), "metahistory": None}


# Branching condition functions
def priority_router(graph_data: Dict[str, Any]) -> str:
    """Route based on priority classification"""
    classify_data = graph_data.get("ClassifyRequest", {})
    priority = classify_data.get("priority", "low")
    print(f"🔀 Routing to {priority} priority handler")
    return priority


def approval_router(graph_data: Dict[str, Any]) -> bool:
    """Route based on approval requirement"""
    approval_data = graph_data.get("ApprovalCheck", {})
    needs_approval = approval_data.get("approval_required", False)
    print(f"🔀 Approval required: {needs_approval}")
    return needs_approval


async def main():
    """Main function demonstrating branching and parallel execution"""
    
    print("=" * 70)
    print("NightSky AgentGraph - Branching Example")
    print("=" * 70)
    
    # Create the graph
    print("\n📊 Creating request processing workflow...")
    graph = AgenticGraph(
        graph_id="request_processing",
        data_schema=RequestData,
        max_parallel=3  # Allow 3 parallel branches
    )
    
    # Add nodes
    print("➕ Adding nodes...")
    graph.add_node(StartNode())
    graph.add_node("ClassifyRequest", classify_request)
    graph.add_node("HandleLowPriority", handle_low_priority)
    graph.add_node("HandleMediumPriority", handle_medium_priority)
    graph.add_node("HandleHighPriority", handle_high_priority)
    graph.add_node("ApprovalCheck", approval_required_check)
    graph.add_node("ManagerApproval", manager_approval)
    graph.add_node("FinalizeRequest", finalize_request)
    graph.add_node(EndNode())
    
    # Add edges
    print("🔗 Connecting nodes with branching logic...")
    
    # Start -> Classify
    graph.add_edge("Start", "ClassifyRequest")
    
    # Classify -> Branch by Priority (3-way branching)
    graph.add_branching_edge(
        source_id="ClassifyRequest",
        condition=priority_router,
        branches={
            "low": "HandleLowPriority",
            "medium": "HandleMediumPriority",
            "high": "HandleHighPriority"
        }
    )
    
    # All priority handlers -> ApprovalCheck (convergence)
    graph.add_edge("HandleLowPriority", "ApprovalCheck")
    graph.add_edge("HandleMediumPriority", "ApprovalCheck")
    graph.add_edge("HandleHighPriority", "ApprovalCheck")
    
    # ApprovalCheck -> Branch by approval requirement
    graph.add_branching_edge(
        source_id="ApprovalCheck",
        condition=approval_router,
        branches={
            True: "ManagerApproval",
            False: "FinalizeRequest"
        }
    )
    
    # ManagerApproval -> FinalizeRequest
    graph.add_edge("ManagerApproval", "FinalizeRequest")
    
    # FinalizeRequest -> End
    graph.add_edge("FinalizeRequest", "End")
    
    print(f"   Graph configured with {len(graph.nodes)} nodes")
    
    # Test different scenarios
    test_cases = [
        {
            "name": "Low Priority (Auto-processed)",
            "data": {
                "customer_id": "CUST001",
                "request_type": "inquiry",
                "amount": 500.0,
                "description": "Simple product question"
            }
        },
        {
            "name": "Medium Priority (Standard)",
            "data": {
                "customer_id": "CUST002",
                "request_type": "order_change",
                "amount": 2500.0,
                "description": "Modify order details"
            }
        },
        {
            "name": "High Priority (Expedited + Approval)",
            "data": {
                "customer_id": "CUST003",
                "request_type": "refund",
                "amount": 15000.0,
                "description": "Large refund request"
            }
        },
        {
            "name": "Medium Priority + Approval",
            "data": {
                "customer_id": "CUST004",
                "request_type": "refund",
                "amount": 3000.0,
                "description": "Refund for defective product"
            }
        }
    ]
    
    # Process each test case
    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "=" * 70)
        print(f"Test Case {i}: {test_case['name']}")
        print("=" * 70)
        
        # Execute
        print(f"\n🚀 Processing request for {test_case['data']['customer_id']}...")
        print("-" * 70)
        
        chat_id = f"request_{test_case['data']['customer_id']}"
        await graph.execute(test_case['data'], chat_id=chat_id)
        
        # Get results
        print("-" * 70)
        result = graph.get_node_graph_state(chat_id=chat_id)
        final_request = RequestData(**result.get("FinalizeRequest", {}))
        
        print(f"\n📋 Results:")
        print(f"   Customer ID: {final_request.customer_id}")
        print(f"   Priority: {final_request.priority}")
        print(f"   Final Status: {final_request.status}")
        print(f"   Processing Path: {' -> '.join(final_request.processing_path)}")
        print(f"   Required Approval: {final_request.approval_required}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print("\nThis example demonstrated:")
    print("  ✓ 3-way branching based on priority classification")
    print("  ✓ Convergence of multiple branches to a single node")
    print("  ✓ Conditional routing based on approval requirements")
    print("  ✓ Different execution paths for different inputs")
    print("  ✓ Parallel execution capability (configured for 3 concurrent branches)")
    
    print("\n" + "=" * 70)
    print("✅ Branching Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

