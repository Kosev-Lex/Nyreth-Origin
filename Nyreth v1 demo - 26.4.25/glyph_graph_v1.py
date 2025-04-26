from typing import Dict, List, Optional
import networkx as nx
import os
import json
from datetime import datetime

class GlyphGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_glyph(self, glyph_id: str, attributes: Optional[Dict] = None):
        attributes = attributes or {}
        self.graph.add_node(glyph_id, **attributes)

    def add_edge(self, glyph1: str, glyph2: str, relation: str, weight: float = 1.0):
        self.graph.add_edge(glyph1, glyph2, relation=relation, weight=weight)

    def connect_similar_glyphs(self, glyphs: List[Dict], threshold: float = 2.5):
        for i in range(len(glyphs)):
            for j in range(i + 1, len(glyphs)):
                g1, g2 = glyphs[i], glyphs[j]
                id1, id2 = g1["glyph"], g2["glyph"]
                t1, t2 = g1["tensor"], g2["tensor"]
                dist = sum((a - b) ** 2 for a, b in zip(t1, t2)) ** 0.5
                if dist < threshold:
                    self.add_edge(id1, id2, relation="tensor_similarity", weight=1 - dist)

        print(f"Connected: {id1} <-> {id2} (dist={dist:.3f})")

    def build_from_library(self, glyph_library):
        """
        Constructs graph from a GlyphLibrary instance.
        """
        glyphs_data = []
        for glyph in glyph_library.glyphs:
            data = glyph.unfold()
            self.add_glyph(data["glyph"], data)
            glyphs_data.append(data)

        self.connect_similar_glyphs(glyphs_data)

    def find_path(self, start: str, end: str) -> Optional[List[str]]:
        try:
            return nx.shortest_path(self.graph, source=start, target=end, weight='weight')
        except nx.NetworkXNoPath:
            return None

    def get_neighbors(self, glyph_id: str) -> List[str]:
        return list(self.graph.neighbors(glyph_id))

    def export_graph(self, path: str = "glyph_graph.json"):
        data = nx.readwrite.json_graph.node_link_data(self.graph)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_graph(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.graph = nx.readwrite.json_graph.node_link_graph(data)

    def get_metadata(self) -> Dict:
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "timestamp": datetime.now().isoformat()
        }
