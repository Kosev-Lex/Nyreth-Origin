# pseudoLLM_v1.py
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
from nyreth_plugin_v1 import NyrethPlugin
from nyreth_encrypted_loader_v1 import load_nyreth_bridge
import json
import os
from datetime import datetime
import contextlib
import io
import threading

# === Connect to Nyreth's symbolic engine (indirectly)
bridge = load_nyreth_bridge(silent_mode=True)
if bridge is None:
    raise RuntimeError("Failed to load NyrethBridge. Encrypted modules not available.")

plugin = NyrethPlugin(bridge)

# === GUI Logic
def submit_query(query_var, sro_output):
    query = query_var.get()

    # 🔇 Suppress all internal print() output during symbolic processing
    with contextlib.redirect_stdout(io.StringIO()):
        result = plugin.process_query(query)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("traces", exist_ok=True)
    trace_path = f"traces/trace_{timestamp}.json"

    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    sro_output.delete("1.0", tk.END)
    sro_output.insert(tk.END, result.get("semantic_output", "[No semantic output]"))

    print(f"[✓] Symbolic query written to: {trace_path}")


# === Thread-safe wrapper to avoid GUI freezing
def submit_query_threaded(query_var, sro_output):
    threading.Thread(target=lambda: submit_query(query_var, sro_output), daemon=True).start()


# === Symbolic Queries
symbolic_queries = [
        # symbolic recursion, paradox, identity
        "What is the paradox of seeking clarity in chaos?",
        "How does the self resolve internal contradiction?",
        "What is the symbolic meaning of transformation through failure?",
        "Why do symbols carry so much emotional resonance?",
        "How does inner dissonance affect outer harmony?",
        "Is there purpose in repeating recursive patterns of thought?",
        "Can contradiction be a source of truth?",
        "What is the symbolic weight of surrender?",
        "What lies at the core of paradoxical desire?",
        "How do we resolve dissonance between action and intention?",
        "How does the inner self respond to symbolic collapse?",
        "When does resonance become distortion?",
        "What is the recursive structure of belief and doubt?",
        "How does the symbolic function of silence differ from its literal absence?",
        "What archetype governs the transformation of fear into resolve?",
        "Can a paradox be stable?",
        "How does the symbol of the mirror distort the self?",
        "What purpose does contradiction serve in symbolic evolution?",
        # 💭 Self & Reflection
        "What does it mean to grow past your former self?",
        "What happens when a story believes itself?",
        # ⚖️ Philosophy & Ethics

        # 🎨 Metaphor & Language
        "How does a symbol survive beyond its creator?",
        "What does it mean when a key no longer fits its lock?",
        # 🌀 Systems & Recursion
        "What happens when structure overrides meaning?",
        # 🔮 Symbolic/Emotive
        "How do shadows form between people who were once close?",
        "What is the nature of silence that follows betrayal?",
    ]

def launch_pseudoLLM():
    root = tk.Tk()
    root.title("PseudoLLM – Symbolic Query Interface")

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Select a symbolic query:").pack(anchor=tk.W)
    query_var = tk.StringVar(value=symbolic_queries[0])
    query_menu = ttk.Combobox(frame, textvariable=query_var, values=symbolic_queries, width=100)
    query_menu.pack(pady=5)

    ttk.Button(frame, text="Submit Query", command=lambda: submit_query_threaded(query_var, sro_output)).pack(pady=10)

    ttk.Label(frame, text="Semantic Reasoning Overlay (SRO):").pack(anchor=tk.W)
    sro_output = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=8)
    sro_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_help_tooltip(parent, help_text):
        def show_tooltip(event):
            nonlocal tooltip
            x, y = event.x_root + 10, event.y_root + 10
            tooltip = tk.Toplevel(parent)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{x}+{y}")
            label = tk.Label(tooltip, text=help_text, background="#222", foreground="white",
                             relief="solid", borderwidth=1, justify="left", wraplength=300, padx=8, pady=4)
            label.pack()

        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        tooltip = None
        help_btn = tk.Label(parent, text="?", font=("Arial", 10, "bold"),
                            foreground="white", background="#444", width=2, anchor="center", relief="raised")
        help_btn.pack(side=tk.RIGHT, padx=5)
        help_btn.bind("<Enter>", show_tooltip)
        help_btn.bind("<Leave>", hide_tooltip)

    add_help_tooltip(
        frame,
        "This is a demo intended to simulate an LLM interface.\n\n"
        "The example questions in the dropdown box are laden with symbolic, metaphorical, "
        "abstract or philosophical meaning. The SRO output is indicative of the kind of enriched "
        "response Nyreth can return to the LLM, which can then be incorporated into the final result "
        "returned to the end user."
    )

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


# Only auto-launch if run directly, not from main GUI
if __name__ == "__main__" and not hasattr(sys, "_called_from_main_gui"):
    launch_pseudoLLM()
