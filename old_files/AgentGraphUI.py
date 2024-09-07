import flet as ft
from flet.canvas import Canvas, Paint, PaintingStyle, Path
import math
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# Assuming you have these imports from your AgentGraph.py
from AgentGraph import AgenticGraph, Node, MessageDict

class GraphVisualization(ft.UserControl):
    def __init__(self, graph: AgenticGraph):
        super().__init__()
        self.graph = graph
        self.node_positions = {}
        self.active_node = None
        self.dragging_node = None
        self.connection_start = None
        self.connection_end = None
        self.node_radius = 40
        self.canvas = None
        print(f"Initializing GraphVisualization with {len(self.graph.nodes)} nodes")
        self.update_layout()

    def build(self):
        print("Building GraphVisualization")
        self.canvas = Canvas(
            width=600,
            height=400,
            on_paint=self.paint_graph
        )
        return ft.Container(
            content=self.canvas,
            bgcolor=ft.colors.BLACK,
            width=600,
            height=400,
            border=ft.border.all(1, ft.colors.WHITE),
        )

    def paint_graph(self, canvas):
        print("Painting graph")
        canvas.clean()

        # Draw edges
        for source, edge_container in self.graph.edges.items():
            for target_graph_id, target_id, _, _ in edge_container.regular_edges:
                if target_graph_id is None:  # Only draw edges within the same graph
                    start = self.node_positions[source]
                    end = self.node_positions[target_id]
                    canvas.draw_line(
                        start[0], start[1], end[0], end[1],
                        Paint(stroke_width=2, color=ft.colors.GREY_400)
                    )
                    print(f"Drew edge from {source} to {target_id}")

        # Draw nodes
        for node_id, pos in self.node_positions.items():
            color = ft.colors.PURPLE_400 if node_id == self.active_node else ft.colors.BLUE_400
            canvas.fill_circle(pos[0], pos[1], self.node_radius, Paint(color=color))
            canvas.draw_text(node_id, pos[0], pos[1], Paint(color=ft.colors.WHITE), ft.TextStyle(size=14))
            print(f"Drew node {node_id} at position {pos}")

    def update_layout(self):
        print("Updating layout")
        nodes = list(self.graph.nodes.keys())
        for i, node in enumerate(nodes):
            if node not in self.node_positions:
                x = 100 + (i % 3) * 200
                y = 100 + (i // 3) * 100
                self.node_positions[node] = (x, y)
                print(f"Set position for node {node}: ({x}, {y})")
        
        if self.canvas:
            self.update()

    def highlight_node(self, node_id):
        self.active_node = node_id
        self.update()

    def add_node(self, node_id):
        if node_id not in self.graph.nodes:
            self.graph.add_node(Node(node_id, lambda x: x))  # Add a placeholder function
            x = 100 + len(self.node_positions) * 100
            y = 200
            self.node_positions[node_id] = (x, y)
            self.update()
            print(f"Added node: {node_id}")

# The rest of the code (GraphUI class and main function) remains the same

def main(page: ft.Page):
    page.title = "AgenticGraph UI"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.colors.GREY_900
    page.padding = 0

    # Create a sample graph
    graph = AgenticGraph(graph_id="example_graph")
    graph.add_node(Node("start", lambda x: f"Start: {x}"))
    graph.add_node(Node("process", lambda x: f"Process: {x.upper()}"))
    graph.add_node(Node("end", lambda x: f"End: {x}"))
    graph.add_edge("start", "process")
    graph.add_edge("process", "end")

    print(f"Created graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

    graph_ui = GraphUI(graph)
    page.add(graph_ui)
    
    # Force a redraw of the graph visualization
    graph_ui.graph_viz.update_layout()
    
    page.update()

    print("Page updated")

if __name__ == "__main__":
    print("Starting AgenticGraph UI. Please open http://localhost:8080 in your web browser if it doesn't open automatically.")
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)