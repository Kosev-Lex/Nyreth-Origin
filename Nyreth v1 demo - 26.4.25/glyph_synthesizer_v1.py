import random
from typing import List, Optional
from nyseal_blackbox import NysealBlackboxLoader
from glyph_core_v1 import Glyph

# === Load Encrypted Modules ===
loader = NysealBlackboxLoader()
symbolic_memory_mod = loader.load_encrypted_module("symbolic_memory", "encrypted/symbolic_memory_v1.nyrethenc", ["SymbolicMemory", "SymbolicTrace"])

SymbolicMemory = symbolic_memory_mod["SymbolicMemory"]
SymbolicTrace = symbolic_memory_mod["SymbolicTrace"]

class GlyphSynthesizer:
    def __init__(self, memory: SymbolicMemory):
        self.memory = memory

    def synthesize_glyph(self, label: str = "Synthesized Glyph") -> Optional[Glyph]:
        traces = self.memory.traces
        if not traces:
            return None

        # Pick 2–3 traces at random
        source_traces = random.sample(traces, min(3, len(traces)))
        glyph_names = [glyph for trace in source_traces for glyph in trace.glyph_sequence]

        # Basic frequency analysis (could evolve to clustering or semantics)
        glyph_counts = {}
        for g in glyph_names:
            glyph_counts[g] = glyph_counts.get(g, 0) + 1

        # Pick top glyphs
        top_glyphs = sorted(glyph_counts.items(), key=lambda x: -x[1])[:3]
        selected_names = [name for name, _ in top_glyphs]

        # Construct mock tensor (average of components)
        synthesized_tensor = [round(random.uniform(0.3, 0.7), 2) for _ in range(10)]

        new_glyph_data = {
            "Glyph Name": f"{label}",
            "Translation": "Auto-generated synthesis",
            "Category": "Synthesized",
            "Class": "Composite",
            "Polarity": "Mixed",
            "Domain": "Meta-symbolic",
            "Function": f"Derived from: {', '.join(selected_names)}",
            "Symbolic Potential": "Emergent from prior symbolic traversals.",
            "Valence": synthesized_tensor[0],
            "Persistence": synthesized_tensor[1],
            "Disruption": synthesized_tensor[2],
            "Charge": synthesized_tensor[3],
            "Gravity": synthesized_tensor[4],
            "Clarity": synthesized_tensor[5],
            "Utility": synthesized_tensor[6],
            "Depth": synthesized_tensor[7],
            "Recursivity": synthesized_tensor[8],
            "Tensionality": synthesized_tensor[9],
            "Resonance Tag": "synth",
            "Vector Intensity": round(sum(synthesized_tensor) / len(synthesized_tensor), 3)
        }

        return Glyph(new_glyph_data)
