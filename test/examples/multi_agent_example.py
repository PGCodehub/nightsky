"""
NightSky AgentGraph - Multi-Agent Collaboration Example
=======================================================

This example demonstrates:
1. Multiple agents working together
2. Agent memory persistence across executions
3. Conversational context building
4. Information passing between agents
"""

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from NightSky.AgentGraph import AgenticGraph, StartNode, EndNode, MessageDict


# Define data schema
class ResearchProject(BaseModel):
    """Schema for research project workflow"""
    topic: str
    research_notes: List[str] = Field(default_factory=list)
    analysis: str = ""
    recommendations: List[str] = Field(default_factory=list)
    final_report: str = ""


# Agent 1: Research Agent
def research_agent(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Research agent that gathers information on a topic.
    Maintains memory of previous research.
    """
    start_data = input_data.get("Start", {})
    project = ResearchProject(**start_data)
    
    # Check memory for previous research
    if agentic_memory:
        context = f"Building on {len(agentic_memory)} previous research interactions"
        print(f"🔍 Research Agent: {context}")
    else:
        print(f"🔍 Research Agent: Starting fresh research on '{project.topic}'")
    
    # Simulate research (in real scenario, this would call APIs, databases, etc.)
    new_findings = [
        f"Finding 1: {project.topic} has significant market potential",
        f"Finding 2: Key competitors in {project.topic} space identified",
        f"Finding 3: Recent trends show 40% growth in {project.topic}"
    ]
    
    project.research_notes.extend(new_findings)
    
    print(f"   ✓ Gathered {len(new_findings)} new findings")
    print(f"   ✓ Total research notes: {len(project.research_notes)}")
    
    # Build metahistory for agent memory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=project.dict(),
        agent_msgs=[
            {"role": "user", "content": f"Research topic: {project.topic}"},
            {"role": "assistant", "content": f"Completed research. Found {len(new_findings)} key insights."}
        ]
    )
    
    return {"graph_data": project.dict(), "metahistory": metahistory}


# Agent 2: Analysis Agent
def analysis_agent(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analysis agent that processes research findings.
    Builds on its own analytical history.
    """
    research_data = input_data.get("ResearchAgent", {})
    project = ResearchProject(**research_data)
    
    # Check memory for previous analyses
    if agentic_memory:
        context = f"Continuing analysis thread with {len(agentic_memory)} previous insights"
        print(f"📊 Analysis Agent: {context}")
    else:
        print(f"📊 Analysis Agent: Fresh analysis of research findings")
    
    # Analyze research notes
    analysis_text = f"""
    Analysis of {project.topic}:
    - Data points analyzed: {len(project.research_notes)}
    - Market viability: High
    - Risk level: Medium
    - Recommendation: Proceed with further investigation
    """
    
    project.analysis = analysis_text.strip()
    
    print(f"   ✓ Completed analysis of {len(project.research_notes)} research notes")
    
    # Build metahistory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=project.dict(),
        agent_msgs=[
            {"role": "user", "content": f"Analyze research on: {project.topic}"},
            {"role": "assistant", "content": f"Analysis complete. {project.analysis[:100]}..."}
        ]
    )
    
    return {"graph_data": project.dict(), "metahistory": metahistory}


# Agent 3: Strategy Agent
def strategy_agent(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Strategy agent that creates recommendations.
    Uses memory to refine strategies over time.
    """
    analysis_data = input_data.get("AnalysisAgent", {})
    project = ResearchProject(**analysis_data)
    
    # Check memory for previous strategies
    if agentic_memory:
        context = f"Refining strategy based on {len(agentic_memory)} previous recommendations"
        print(f"💡 Strategy Agent: {context}")
    else:
        print(f"💡 Strategy Agent: Creating initial strategic recommendations")
    
    # Generate recommendations
    recommendations = [
        f"Recommendation 1: Invest in {project.topic} development",
        f"Recommendation 2: Build partnerships in {project.topic} ecosystem",
        f"Recommendation 3: Monitor competitor activities closely",
        f"Recommendation 4: Allocate budget for pilot program"
    ]
    
    project.recommendations.extend(recommendations)
    
    print(f"   ✓ Generated {len(recommendations)} strategic recommendations")
    print(f"   ✓ Total recommendations: {len(project.recommendations)}")
    
    # Build metahistory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=project.dict(),
        agent_msgs=[
            {"role": "user", "content": f"Create strategy for: {project.topic}"},
            {"role": "assistant", "content": f"Strategy developed with {len(recommendations)} recommendations"}
        ]
    )
    
    return {"graph_data": project.dict(), "metahistory": metahistory}


# Agent 4: Report Writer Agent
def report_writer_agent(input_data: Dict[str, Any], agentic_memory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Report writing agent that synthesizes all information.
    Maintains style consistency through memory.
    """
    strategy_data = input_data.get("StrategyAgent", {})
    project = ResearchProject(**strategy_data)
    
    # Check memory for previous reports
    if agentic_memory:
        context = f"Writing report with awareness of {len(agentic_memory)} previous reports"
        print(f"📝 Report Writer Agent: {context}")
    else:
        print(f"📝 Report Writer Agent: Creating first comprehensive report")
    
    # Generate report
    report = f"""
    ═══════════════════════════════════════════════════════════
    RESEARCH PROJECT REPORT: {project.topic}
    ═══════════════════════════════════════════════════════════
    
    RESEARCH SUMMARY
    ───────────────────────────────────────────────────────────
    Total findings: {len(project.research_notes)}
    
    Key Research Notes:
    {chr(10).join(f"  • {note}" for note in project.research_notes[:3])}
    
    ANALYSIS
    ───────────────────────────────────────────────────────────
    {project.analysis}
    
    STRATEGIC RECOMMENDATIONS
    ───────────────────────────────────────────────────────────
    {chr(10).join(f"  {i}. {rec}" for i, rec in enumerate(project.recommendations, 1))}
    
    CONCLUSION
    ───────────────────────────────────────────────────────────
    Based on comprehensive research and analysis, we recommend
    proceeding with the proposed initiatives for {project.topic}.
    
    Report generated by Multi-Agent Research System
    ═══════════════════════════════════════════════════════════
    """
    
    project.final_report = report.strip()
    
    print(f"   ✓ Report generated ({len(report)} characters)")
    
    # Build metahistory
    metahistory = MessageDict(
        role="assistant",
        input_data=input_data,
        toolcall_in_output=False,
        output_state=project.dict(),
        agent_msgs=[
            {"role": "user", "content": f"Write comprehensive report for: {project.topic}"},
            {"role": "assistant", "content": "Comprehensive report completed successfully"}
        ]
    )
    
    return {"graph_data": project.dict(), "metahistory": metahistory}


async def main():
    """Main function demonstrating multi-agent collaboration"""
    
    print("=" * 70)
    print("NightSky AgentGraph - Multi-Agent Collaboration Example")
    print("=" * 70)
    
    # Create the graph
    print("\n📊 Creating multi-agent research workflow...")
    graph = AgenticGraph(
        graph_id="research_collaboration",
        data_schema=ResearchProject
    )
    
    # Add agent nodes
    print("➕ Adding agents...")
    graph.add_node(StartNode())
    graph.add_node("ResearchAgent", research_agent, is_agent=True)
    graph.add_node("AnalysisAgent", analysis_agent, is_agent=True)
    graph.add_node("StrategyAgent", strategy_agent, is_agent=True)
    graph.add_node("ReportWriterAgent", report_writer_agent, is_agent=True)
    graph.add_node(EndNode())
    
    print(f"   ✓ {len(graph.agent_ids)} agents initialized")
    
    # Connect agents in sequence
    print("🔗 Connecting agents in workflow...")
    graph.add_edge("Start", "ResearchAgent")
    graph.add_edge("ResearchAgent", "AnalysisAgent")
    graph.add_edge("AnalysisAgent", "StrategyAgent")
    graph.add_edge("StrategyAgent", "ReportWriterAgent")
    graph.add_edge("ReportWriterAgent", "End")
    
    # First execution
    print("\n" + "=" * 70)
    print("🚀 First Execution: AI-Powered Healthcare")
    print("=" * 70)
    print("-" * 70)
    
    initial_data = {
        "topic": "AI-Powered Healthcare",
        "research_notes": [],
        "recommendations": []
    }
    
    await graph.execute(initial_data, chat_id="research_session")
    
    print("-" * 70)
    
    # Get results
    result = graph.get_graph_data()
    final_project = ResearchProject(**result.get("ReportWriterAgent", {}))
    
    print("\n📋 First Execution Results:")
    print(final_project.final_report)
    
    # Show agent memories after first run
    print("\n🧠 Agent Memory Status After First Run:")
    print("-" * 70)
    for i, agent_id in enumerate(graph.agent_ids, 1):
        memory = graph.get_agentic_memory(agent_id)
        agent_node = [n for n in graph.nodes.values() if hasattr(n, 'agent_id') and n.agent_id == agent_id][0]
        print(f"   Agent {i} ({agent_node.name}): {len(memory)} messages in memory")
    
    # Second execution with same chat_id (agents remember previous interaction)
    print("\n" + "=" * 70)
    print("🚀 Second Execution: Quantum Computing Applications")
    print("=" * 70)
    print("   (Same session - agents will remember previous work)")
    print("-" * 70)
    
    second_data = {
        "topic": "Quantum Computing Applications",
        "research_notes": [],
        "recommendations": []
    }
    
    await graph.execute(second_data, chat_id="research_session")
    
    print("-" * 70)
    
    # Get results
    result2 = graph.get_graph_data()
    final_project2 = ResearchProject(**result2.get("ReportWriterAgent", {}))
    
    print("\n📋 Second Execution Results:")
    print(final_project2.final_report)
    
    # Show updated agent memories
    print("\n🧠 Agent Memory Status After Second Run:")
    print("-" * 70)
    for i, agent_id in enumerate(graph.agent_ids, 1):
        memory = graph.get_agentic_memory(agent_id)
        agent_node = [n for n in graph.nodes.values() if hasattr(n, 'agent_id') and n.agent_id == agent_id][0]
        print(f"   Agent {i} ({agent_node.name}): {len(memory)} messages in memory")
        print(f"      Latest: {memory[-1]['content'][:60]}..." if memory else "      (empty)")
    
    # Third execution with different chat_id (fresh start)
    print("\n" + "=" * 70)
    print("🚀 Third Execution: Renewable Energy Solutions")
    print("=" * 70)
    print("   (NEW session - agents start fresh)")
    print("-" * 70)
    
    third_data = {
        "topic": "Renewable Energy Solutions",
        "research_notes": [],
        "recommendations": []
    }
    
    await graph.execute(third_data, chat_id="new_research_session")
    
    print("-" * 70)
    
    # Show execution history
    print("\n📜 Execution History Summary:")
    print("-" * 70)
    
    # Session 1
    metahistory1, entries1 = graph.get_metahistory(chat_id="research_session")
    print(f"   Session 'research_session': {len(entries1)} execution entries")
    
    # Session 2
    metahistory2, entries2 = graph.get_metahistory(chat_id="new_research_session")
    print(f"   Session 'new_research_session': {len(entries2)} execution entries")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print("\nThis example demonstrated:")
    print("  ✓ 4 specialized agents working in sequence")
    print("  ✓ Agent memory persistence across executions")
    print("  ✓ Information flow from research → analysis → strategy → report")
    print("  ✓ Context building within agent conversations")
    print("  ✓ Session isolation with different chat_ids")
    print("  ✓ Complete workflow automation with agents")
    
    print("\n💡 Key Insights:")
    print("  • Each agent maintains its own conversation memory")
    print("  • Agents can build context across multiple executions")
    print("  • Different chat_ids create isolated sessions")
    print("  • Data flows seamlessly between agents")
    print("  • Each execution gets a unique execution_id for tracking")
    
    print("\n" + "=" * 70)
    print("✅ Multi-Agent Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

