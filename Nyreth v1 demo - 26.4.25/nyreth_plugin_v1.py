# nyreth_plugin_v1.py

class NyrethPlugin:
    def __init__(self, bridge, heuristic_fn=None):
        """
        :param bridge: NyrethBridge instance (preloaded and running)
        :param heuristic_fn: Optional function to decide if query needs symbolic routing
        """
        self.bridge = bridge
        self.should_use_nyreth = heuristic_fn or self.default_heuristic

    def default_heuristic(self, query: str) -> bool:
        """Basic decision rule to use Nyreth for metaphorical or deep reflective questions."""
        keywords = [
            "meaning", "paradox", "contradiction", "self", "purpose", "transformation",
            "symbol", "recursive", "resonance", "inner", "resolve", "archetype", "dissonance",
            "shadow", "doubt", "belief", "loss", "grief", "silence"
        ]

        return any(kw in query.lower() for kw in keywords)

    def build_packet(self, query: str) -> dict:
        """Translate the LLM query into a structured symbolic packet."""
        return {
            "intent": "investigate",
            "focus": self.infer_focus(query),
            "tone": "reflective",
            "depth": "recursive",
            "constraints": {
                "max_steps": 6,
                "avoid": []
            },
            "context": query,
            "mode": "symbolic",
            "return_format": "enriched_summary",
            "origin": "LLM_plugin",
            "user_id": "auto_test"
        }

    def infer_focus(self, query: str) -> list:
        """Rough mapping from language to glyph-seeds."""
        # (This can later be replaced with a GPT-powered semantic mapper)
        if "contradiction" in query:
            return ["Treyl", "Thyrel"]
        if "paradox" in query:
            return ["Treyl", "Elken"]
        if "meaning" in query:
            return ["Elun", "Depth"]
        if "self" in query:
            return ["Self", "Shadow"]
        return ["Elun"]

    def process_query(self, query: str) -> dict:
        """Main LLM → Nyreth dispatch and return."""
        if self.should_use_nyreth(query):
            print(f"[Plugin] Routing query to Nyreth:\n> {query}")
            packet = self.build_packet(query)
            return self.bridge.process_structured_query(packet)
        else:
            return {"status": "bypass", "message": "Query did not require symbolic routing."}
