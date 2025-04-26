from typing import List, Optional, Dict
import json
from glyph_core_v1 import Glyph
from jsonschema import validate, ValidationError
import re
import os

class GlyphLibrary:
    def __init__(self, dataset_path: str, schema_path: Optional[str] = None):
        self.dataset_path = dataset_path
        self.schema_path = schema_path
        self.schema = self.load_schema(schema_path)
        self.glyphs: List[Glyph] = []
        self.read_only = True  # 🔒

    def load_schema(self, path: Optional[str]) -> Dict:
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def reformat_for_schema(self, glyph: Dict) -> Dict:
        return {
            "glyph": glyph.get("Glyph Name", ""),
            "translation": glyph.get("Translation", ""),
            "category": glyph.get("Category", ""),
            "class": glyph.get("Class", ""),
            "resonance_tag": glyph.get("Resonance Tag", ""),
            "tensor": {
                "valence": glyph.get("Valence", 0),
                "persistence": glyph.get("Persistence", 0),
                "disruption": glyph.get("Disruption", 0),
                "charge": glyph.get("Charge", 0),
                "gravity": glyph.get("Gravity", 0),
                "clarity": glyph.get("Clarity", 0),
                "utility": glyph.get("Utility", 0),
                "depth": glyph.get("Depth", 0),
                "recursivity": glyph.get("Recursivity", 0),
                "tensionality": glyph.get("Tensionality", 0)
            }
        }

    def load(self):
        if self.dataset_path.endswith(".nyrethenc"):
            from nyreth_encrypted_loader_v1 import load_encrypted_symbols

            # Remove _v1 if present to avoid duplication in filename
            base = os.path.splitext(os.path.basename(self.dataset_path))[0]  # e.g. 'glyphset4c_v1'
            module_key = base.removesuffix("_v1")  # yields 'glyphset4c'

            decrypted_json = load_encrypted_symbols(module_key, "glyph_list")
            raw_data = json.loads(decrypted_json)
        else:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)


        validated = []
        for entry in raw_data:
            try:
                if self.schema:
                    validate(instance=self.reformat_for_schema(entry), schema=self.schema)
                validated.append(Glyph(entry))
            except ValidationError as e:
                print(f"[Validation Error] Glyph '{entry.get('Glyph Name', 'UNKNOWN')}' skipped: {e.message}")
        self.glyphs = validated

    def get_glyph_names(self) -> List[str]:
        return [glyph.data.get("Glyph Name", "UNKNOWN") for glyph in self.glyphs]

    def get_glyph_by_name(self, name: str) -> Optional[Glyph]:
        """
        Attempts to find a glyph by exact name. If no exact match, tries to extract and match parts from composite trace entries.
        """
        name_clean = name.strip().lower()

        # Try exact match first
        for glyph in self.glyphs:
            glyph_name = glyph.data.get("Glyph Name", "").strip().lower()
            if glyph_name == name_clean:
                return glyph

        # Try partial match from composite names (e.g., "Threnos_Sore_Link")
        parts = re.split(r'[_\s]+', name_clean)
        for part in parts:
            for glyph in self.glyphs:
                glyph_name = glyph.data.get("Glyph Name", "").strip().lower()
                if glyph_name == part:
                    return glyph

        return None

    def draw_glyph_universe(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600

        spacing = 150
        cols = max(1, width // spacing)

        for i, glyph in enumerate(self.glyph_library.glyphs):
            row = i // cols
            col = i % cols
            base_x = col * spacing + 100
            base_y = row * spacing + 100

            # Apply scale and pan
            x = base_x * self.scale + self.offset_x
            y = base_y * self.scale + self.offset_y

            # Draw node
            oval_id = self.canvas.create_oval(
                x - 30, y - 30, x + 30, y + 30,
                fill="#3A8", outline="#222", width=2,
                tags=("glyph",)
            )

            # Draw label
            self.canvas.create_text(
                x, y,
                text=glyph.name[:8],  # Limit name length to avoid overflow
                fill="white",
                font=("Arial", 10),
                tags=("glyph",)
            )

            # Bind left click
            self.canvas.tag_bind(oval_id, "<Button-1>", lambda e, g=glyph: self.on_glyph_selected(g))

    def on_glyph_selected(self, glyph):
        self.glyph_dropdown.set(glyph.name)
        self.on_select()
        self.status_var.set(f"Selected: {glyph.name}")

    def zoom_universe(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor
        self.draw_glyph_universe()

    def drag_universe(self, event):
        self.offset_x += event.x - self.canvas.winfo_width() / 2
        self.offset_y += event.y - self.canvas.winfo_height() / 2
        self.draw_glyph_universe()

    def save(self):
        raise PermissionError(
            "🔒 Saving is disabled.")


