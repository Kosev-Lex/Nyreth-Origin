from typing import List, Dict, Optional
import logging
from datetime import datetime
import os

from nyseal_blackbox import NysealBlackboxLoader

# === Load Decrypted Modules from Encrypted ===
_loader = NysealBlackboxLoader()
symbolic_memory_mod = _loader.load_encrypted_module(
    "symbolic_memory", "encrypted/symbolic_memory_v1.nyrethenc", ["SymbolicMemory"]
)
symbolic_network_mod = _loader.load_encrypted_module(
    "symbolic_network", "encrypted/symbolic_network_v1.nyrethenc", ["SymbolicMemoryNetwork"]
)

SymbolicMemory = symbolic_memory_mod["SymbolicMemory"]
SymbolicMemoryNetwork = symbolic_network_mod["SymbolicMemoryNetwork"]

# ✅ Logging should be configured at module level (outside class)
LOG_PATH = "symbolic_memory_v1/activity.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class CognitiveMemory:
    def __init__(
        self,
        glyph_library=None,
        trace_path: str = "symbolic_memory_v1/all_traces.json",
        network_path: str = "symbolic_memory_v1/synaptic_memory.json"
    ):
        # ✅ Pass glyph_library into symbolic memory
        self.trace_memory = SymbolicMemory(memory_path=trace_path, glyph_library=glyph_library)
        self.symbolic_network = SymbolicMemoryNetwork(memory_path=network_path)

        # 🔗 Link trace memory to the network
        self.trace_memory.symbolic_network = self.symbolic_network

    def store_trace(self, trace: List[str], metadata: Optional[Dict] = None):
        """
        Store a symbolic trace into both memory systems:
        - Adds to trace memory (avoiding duplicates)
        - Reinforces connections in the network
        - Logs resonance changes and stores both memory types
        """
        glyphs = " → ".join(trace)
        self.trace_memory.store_trace(trace, metadata)
        logging.info(f"[TRACE] Stored trace: {glyphs}")
        print(f"[🧠] Trace stored: {glyphs}")

        if hasattr(self.symbolic_network, "reinforce_trace"):
            # Log resonance scores before reinforcement
            before_scores = {
                g: self.symbolic_network.calculate_resonance(g) for g in trace
            }

            self.symbolic_network.reinforce_trace(trace)
            self.symbolic_network.save()

            # Log resonance scores after
            after_scores = {
                g: self.symbolic_network.calculate_resonance(g) for g in trace
            }

            for g in trace:
                delta = round(after_scores[g] - before_scores[g], 4)
                msg = f"[RES] {g}: {before_scores[g]} → {after_scores[g]} (Δ {delta})"
                logging.info(msg)
                print(f"[⚡] {msg}")

    def get_trace_labels(self) -> List[str]:
        return self.trace_memory.list_trace_labels()

    def find_traces_with_glyph(self, glyph_name: str):
        return self.trace_memory.find_traces_with_glyph(glyph_name)

    def get_core_glyphs(self, top_n=10):
        return self.symbolic_network.get_core_glyphs(top_n)

    def calculate_resonance(self, glyph_id: str) -> float:
        return self.symbolic_network.calculate_resonance(glyph_id)

    def propose_trace(self, start: str, length: int = 5) -> List[str]:
        return self.symbolic_network.propose_trace(start, length)

    def save_all(self):
        self.trace_memory.save()
        self.symbolic_network.save()
