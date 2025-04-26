import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SymbolicNetworkViewer:
    def __init__(self, symbolic_network):
        self.network = symbolic_network
        self.window = tk.Toplevel()
        self.window.title("Symbolic Network Viewer")
        self.window.geometry("800x600")
        self.draw_graph()

    def draw_graph(self):
        G = nx.Graph()

        # Add nodes and edges from symbolic memory network
        for name, node in self.network.nodes.items():
            G.add_node(name, weight=node.usage_count)
            for neighbor, strength in node.connections.items():
                G.add_edge(name, neighbor, weight=strength)

        pos = nx.spring_layout(G, seed=42)

        # Extract drawing parameters
        node_sizes = [300 + 80 * G.nodes[n].get("weight", 1) for n in G.nodes]
        edge_weights = [G[u][v].get("weight", 0.1) for u, v in G.edges]

        # Set up Matplotlib figure
        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, node_color="lightblue")
        nx.draw_networkx_edges(G, pos, ax=ax, width=edge_weights, alpha=0.6)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=9)

        ax.set_title("Symbolic Memory Network")
        ax.axis("off")

        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
