import tkinter as tk
from tkinter import ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.cm as cm
import numpy as np
import json
import os
from datetime import datetime
from sklearn.cluster import KMeans

# === Load encrypted bridge ===
from nyreth_encrypted_loader_v1 import load_nyreth_bridge


class GraphViewer:
    def __init__(self, glyph_library, glyph_graph, trace_path=None):
        self.library = glyph_library
        self.glyph_graph = glyph_graph

        # === Load symbolic components via encrypted bridge ===
        self.bridge = load_nyreth_bridge()
        self.recursive_engine = self.bridge.traversal_engine.recursive_engine
        self.symbolic_memory = self.bridge.symbolic_memory
        self.symbolic_network = self.bridge.symbolic_network

        self.graph = self.recursive_engine.graph.graph  # Extract NetworkX graph

        self.node_metadata = {g.data["Glyph Name"]: g.unfold() for g in glyph_library.glyphs}
        self.selected_nodes = []

        self.window = tk.Toplevel()
        self.window.title("Glyph Graph Viewer")
        self.window.geometry("1100x750")

        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.path_trace = trace_path or []

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.window, textvariable=self.status_var, anchor="w", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(self.button_frame, text="Export View", command=self.export_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Export Metadata", command=self.export_metadata).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Highlight Path", command=self.highlight_path_prompt).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Show Recursive Path", command=self.refresh_recursive_path).pack(side=tk.LEFT, padx=5)

        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Search Glyph:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", self.search_node)

        ttk.Button(control_frame, text="Cluster View", command=lambda: self.apply_cluster_view(n_clusters=4)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh Path", command=self.draw_graph).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Trace Path (A,B,C):").pack(side=tk.LEFT, padx=(20, 5))
        self.path_entry = ttk.Entry(control_frame, width=30)
        self.path_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Trace Path", command=self.trace_path_between_nodes).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Zoom:").pack(side=tk.LEFT, padx=(20, 5))
        self.zoom_var = tk.DoubleVar(value=1.0)
        zoom_slider = ttk.Scale(control_frame, from_=0.5, to=2.0, value=1.0,
                                variable=self.zoom_var, orient=tk.HORIZONTAL, length=150,
                                command=self.apply_zoom)
        zoom_slider.pack(side=tk.LEFT)

        self.draw_graph()
        self.canvas.mpl_connect("button_press_event", self.on_click)



    def draw_graph(self, highlight_nodes=None, highlight_edges=None):
        self.ax.clear()
        self.pos = nx.spring_layout(self.graph, seed=42)

        # Determine categories for color mapping
        categories = list(set(self.node_metadata[n]["category"]
                              for n in self.graph.nodes
                              if n in self.node_metadata))
        cmap = cm.get_cmap("tab10", len(categories))
        node_colors = []

        for node in self.graph.nodes:
            meta = self.node_metadata.get(node, {})
            category = meta.get("category", "")
            color_idx = categories.index(category) if category in categories else 0
            node_colors.append(cmap(color_idx))

        # Draw base nodes
        nx.draw_networkx_nodes(self.graph, self.pos,
                               nodelist=list(self.graph.nodes),
                               node_color=node_colors,
                               node_size=200,
                               ax=self.ax)

        # ----------------------------
        # Draw multi-path trace logic
        # ----------------------------
        traced_nodes = set()
        traced_edges = []

        if self.path_trace:
            if isinstance(self.path_trace[0], list):
                # path_trace is a list of paths
                for subpath in self.path_trace:
                    traced_nodes.update(subpath)
                    for i in range(len(subpath) - 1):
                        traced_edges.append((subpath[i], subpath[i + 1]))
            else:
                # path_trace is a single path
                traced_nodes.update(self.path_trace)
                for i in range(len(self.path_trace) - 1):
                    traced_edges.append((self.path_trace[i], self.path_trace[i + 1]))

            # Draw highlighted path nodes
            nx.draw_networkx_nodes(self.graph, self.pos,
                                   nodelist=list(traced_nodes),
                                   node_color='red',
                                   node_size=300,
                                   ax=self.ax)

            # Draw directional arrows for traced edges
            nx.draw_networkx_edges(self.graph, self.pos,
                                   edgelist=traced_edges,
                                   width=2.5,
                                   edge_color='red',
                                   arrowstyle='->',
                                   arrows=True,
                                   arrowsize=12,
                                   connectionstyle='arc3,rad=0.15',
                                   ax=self.ax)

        # Optional highlight overlays
        if highlight_nodes:
            nx.draw_networkx_nodes(self.graph, self.pos,
                                   nodelist=highlight_nodes,
                                   node_color='yellow',
                                   node_size=600,
                                   ax=self.ax)
        if highlight_edges:
            nx.draw_networkx_edges(self.graph, self.pos,
                                   edgelist=highlight_edges,
                                   edge_color='blue',
                                   width=2,
                                   ax=self.ax)

        # Draw all base edges
        nx.draw_networkx_edges(self.graph, self.pos,
                               edgelist=self.graph.edges,
                               width=0.8,
                               edge_color='gray',
                               alpha=0.5,
                               ax=self.ax)

        # Draw node labels
        nx.draw_networkx_labels(self.graph, self.pos,
                                labels={node: node for node in self.graph.nodes},
                                font_size=7,
                                font_color='black',
                                ax=self.ax)

        self.ax.set_title("Glyph Graph Visualization with Path Traces", fontsize=12)
        self.ax.axis('off')
        self.figure.tight_layout()
        self.canvas.draw()

    def on_click(self, event):
        if not event.inaxes:
            return
        click_x, click_y = event.xdata, event.ydata
        threshold = 0.05
        for node, (x, y) in self.pos.items():
            distance = np.sqrt((click_x - x) ** 2 + (click_y - y) ** 2)
            if distance < threshold:
                meta = self.node_metadata.get(node)
                if meta:
                    self.show_metadata(meta)
                    self.selected_nodes.append(node)
                break

    def show_metadata(self, meta):
        label = f"{meta['glyph']} | Category: {meta['category']} | Domain: {meta['domain']} | Class: {meta['class']} | Polarity: {meta['polarity']}"
        self.status_var.set(label)

    def highlight_path_prompt(self):
        if len(self.selected_nodes) < 2:
            self.status_var.set("Select at least 2 nodes to find path.")
            return
        start, end = self.selected_nodes[-2], self.selected_nodes[-1]
        try:
            path = nx.shortest_path(self.graph, source=start, target=end)
            edge_list = list(zip(path[:-1], path[1:]))
            self.draw_graph(highlight_nodes=path, highlight_edges=edge_list)
            self.status_var.set(f"Highlighted path: {start} → {end}")
        except nx.NetworkXNoPath:
            self.status_var.set(f"No path found from {start} to {end}.")

    def export_view(self):
        os.makedirs("graph_exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"graph_exports/graph_view_{timestamp}.png"
        self.figure.savefig(filepath)
        self.status_var.set(f"Graph image saved to {filepath}")

    def export_metadata(self):
        if not self.selected_nodes:
            self.status_var.set("No nodes selected to export metadata.")
            return
        metadata = [self.node_metadata[n] for n in self.selected_nodes if n in self.node_metadata]
        os.makedirs("graph_exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"graph_exports/graph_metadata_{timestamp}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        self.status_var.set(f"Metadata exported to {filepath}")

    def search_node(self, event=None):
        query = self.search_var.get().strip().lower()
        matched = [n for n in self.graph.nodes if query in n.lower()]
        if matched:
            node = matched[0]
            self.selected_nodes.append(node)
            self.draw_graph(highlight_nodes=[node])
            self.status_var.set(f"Found: {node}")
        else:
            self.status_var.set("No matching glyph found.")

    def apply_zoom(self, event=None):
        zoom = self.zoom_var.get()
        if not hasattr(self, "pos"):
            return
        scaled_pos = {node: (x * zoom, y * zoom) for node, (x, y) in self.pos.items()}
        self.ax.clear()

        categories = list(set(self.node_metadata[n]["category"] for n in self.graph.nodes if n in self.node_metadata))
        cmap = cm.get_cmap("tab10", len(categories))
        node_colors = []

        for node in self.graph.nodes:
            meta = self.node_metadata.get(node, {})
            category = meta.get("category", "")
            color_idx = categories.index(category) if category in categories else 0
            node_colors.append(cmap(color_idx))

        nx.draw(self.graph, pos=scaled_pos, ax=self.ax, with_labels=True, node_size=500,
                node_color=node_colors, edge_color="gray", font_size=8)
        self.figure.tight_layout()
        self.canvas.draw()

    def apply_cluster_view(self, n_clusters=4):
        """Cluster nodes using KMeans on tensor vectors and recolor them."""
        tensors = []
        node_ids = []

        for node in self.graph.nodes(data=True):
            node_id, attrs = node
            tensor = attrs.get("tensor", None)
            if tensor and isinstance(tensor, list) and len(tensor) == 10:
                node_ids.append(node_id)
                tensors.append(tensor)

        if not tensors:
            self.status_var.set("No tensor data available for clustering.")
            return

        kmeans = KMeans(n_clusters=n_clusters, n_init=10)
        labels = kmeans.fit_predict(tensors)

        for node_id, label in zip(node_ids, labels):
            self.graph.nodes[node_id]['cluster'] = label

        self.color_nodes_by_cluster(labels)

    def color_nodes_by_cluster(self, labels):
        """Assign cluster-based colors to nodes and redraw."""
        cluster_colors = cm.get_cmap('tab10', len(set(labels)))

        self.node_colors = []
        for node in self.graph.nodes():
            label = self.graph.nodes[node].get("cluster", 0)
            self.node_colors.append(cluster_colors(label))

        self.draw_graph()

    def trace_path_between_nodes(self):
        input_text = self.path_entry.get()
        if not input_text:
            self.status_var.set("Enter a comma-separated sequence of glyphs.")
            return

        # Normalize input and build lookup map from lowercase name → actual name
        lookup = {n.lower(): n for n in self.glyph_graph.graph.nodes}
        input_names = [name.strip().lower() for name in input_text.split(",")]
        resolved_names = []

        for name in input_names:
            if name in lookup:
                resolved_names.append(lookup[name])
            else:
                self.status_var.set(f"Glyph not found: '{name}'")
                return

        if len(resolved_names) < 2:
            self.status_var.set("Enter at least two valid glyph names.")
            return

        # Construct full path between glyphs
        full_path = []
        for i in range(len(resolved_names) - 1):
            start = resolved_names[i]
            end = resolved_names[i + 1]
            try:
                path_segment = nx.shortest_path(self.glyph_graph.graph, source=start, target=end)
                if i != 0:
                    path_segment = path_segment[1:]  # remove duplicate overlap
                full_path.extend(path_segment)
            except nx.NetworkXNoPath:
                self.status_var.set(f"No path found between {start} and {end}.")
                return

        self.path_trace = full_path
        self.draw_graph()
        self.status_var.set(f"Path traced through {len(full_path)} glyphs.")

    def refresh_recursive_path(self):
        self.path_trace = self.recursive_engine.summarize_trace()
        self.draw_graph()
        self.status_var.set("Recursive path highlighted.")




