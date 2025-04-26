
from typing import Dict, List


class Glyph:
    def __init__(self, data: Dict):
        # Normalize key in case of BOM corruption or naming variance
        if "Glyph Name" in data:
            data["Glyph Name"] = data.pop("Glyph Name")

        self.data = data
        self.name: str = data.get("Glyph Name", "UNKNOWN")

        self.translation: str = data.get("Translation", "")
        self.category: str = data.get("Category", "")
        self.cls: str = data.get("Class", "")
        self.polarity: str = data.get("Polarity", "")
        self.domain: str = data.get("Domain", "")
        self.function: str = data.get("Function", "")
        self.symbolic_potential: str = data.get("Symbolic Potential", "")
        self.resonance_tag: str = data.get("Resonance Tag", "")
        self.vector_intensity: float = self.safe_float(data.get("Vector Intensity", 0.0), "Vector Intensity")

        self.tensor: List[float] = self._extract_tensor()

    def safe_float(self, value, field: str = "") -> float:
        """Safely convert values to float, warn if invalid."""
        try:
            return float(value)
        except (ValueError, TypeError):
            print(f"[Warning] Invalid float in field '{field}': {value} — defaulting to 0.0")
            return 0.0

    def _extract_tensor(self) -> List[float]:
        """Returns tensor as a list of 10 floats. Supports full list or axis-based fallback."""
        # Primary: load full tensor list if available
        if "tensor" in self.data and isinstance(self.data["tensor"], list) and len(self.data["tensor"]) == 10:
            return [self.safe_float(v, f"tensor[{i}]") for i, v in enumerate(self.data["tensor"])]

        # Fallback: load by named axes
        labels = [
            "Valence", "Persistence", "Disruption", "Charge", "Gravity",
            "Clarity", "Utility", "Depth", "Recursivity", "Tensionality"
        ]
        tensor = [self.safe_float(self.data.get(label, 0.0), label) for label in labels]

        if all(v == 0.0 for v in tensor):
            print(f"[!] Glyph '{self.name}' has zero tensor. Check source.")

        return tensor

    def unfold(self) -> Dict:
        """Returns a flattened glyph representation suitable for registration or export."""
        return {
            "glyph": self.name,
            "translation": self.translation,
            "category": self.category,
            "class": self.cls,
            "polarity": self.polarity,
            "domain": self.domain,
            "function": self.function,
            "symbolic_potential": self.symbolic_potential,
            "tensor": self.tensor,
            "resonance_tag": self.resonance_tag,
            "vector_intensity": self.vector_intensity,
        }

    def __str__(self):
        return f"{self.name} ({self.translation}) – {self.symbolic_potential}"


