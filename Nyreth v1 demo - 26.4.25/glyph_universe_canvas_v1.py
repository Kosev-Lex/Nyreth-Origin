import tkinter as tk
from tkinter import Menu
import random
import math
import json
import os
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class GlyphUniverseCanvas:
    def __init__(self, parent, glyphs, on_left_click, on_right_click, get_trace_path, symbolic_network2=None):
        self.parent = parent
        self.glyphs = glyphs  # List[Glyph]
        self.on_left_click = on_left_click  # callback(glyph_name)
        self.on_right_click = on_right_click  # callback(glyph_name, x, y)
        self.get_trace_path = get_trace_path  # returns List[glyph_name] for trace overlay
        self.symbolic_network = symbolic_network2

        # === Load default layout before any rendering ===
        layout_path = "layouts/custom_layout1.json"
        self.initial_layout = {}
        self.glyph_positions = {}

        if os.path.exists(layout_path):
            with open(layout_path, "r", encoding="utf-8") as f:
                self.initial_layout = json.load(f)
                self.glyph_positions = dict(self.initial_layout)  # Ensure default positions are applied
            print(f"[✓] Default layout loaded from {layout_path} ({len(self.initial_layout)} glyphs)")
        else:
            print(f"[!] Default layout not found at {layout_path} — using procedural layout")


        self.canvas = tk.Canvas(parent, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.glyph_items = {}  # glyph_name: (id, x, y)
        self.trace_lines = []
        self.hover_label = None
        self.selection_box = None
        self.selection_start = None
        self.selected_glyphs = set()
        self.group_drag_box = None

        self.canvas.bind("<Motion>", self.on_mouse_motion)

        # Unified handler for left click press
        self.canvas.bind("<ButtonPress-1>", self.handle_left_click_start)
        self.canvas.bind("<B1-Motion>", self.handle_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.handle_left_release)

        self.canvas.bind("<Shift-ButtonPress-1>", self.start_drag_box)
        self.canvas.bind("<Shift-B1-Motion>", self.update_drag_box)
        self.canvas.bind("<Shift-ButtonRelease-1>", self.finalize_drag_box)

        self.scale = 0.2
        self.offset_x = 300
        self.offset_y = 200
        self.pan_start = None

        self.canvas.bind("<MouseWheel>", self.handle_zoom)  # Windows/macOS
        self.canvas.bind("<ButtonPress-2>", self.start_pan)  # Middle click
        self.canvas.bind("<B2-Motion>", self.do_pan)
        self.canvas.bind("<ButtonRelease-2>", self.end_pan)

        self.dragging_glyph = None
        self.drag_offset = (0, 0)
        self.glyph_positions_history = []  # for undo

        self.layout_glyphs()
        self.canvas.bind("<Button-3>", self.handle_right_click)

    def layout_glyphs(self):
        import math
        import random
        from collections import defaultdict

        try:
            self.canvas.delete("glyph_node")
            self.canvas.delete("glyph_text")
            self.canvas.delete("glyph_hitbox")
        except Exception as e:
            print(f"[!] Error clearing canvas glyph tags: {e}")

        # === Initialize or reset internal tracking ===
        if not hasattr(self, 'glyph_items'):
            self.glyph_items = {}
        else:
            self.glyph_items.clear()

        if not hasattr(self, 'glyph_positions'):
            self.glyph_positions = {}

        if not hasattr(self, 'initial_layout'):
            layout_path = "layouts/custom_layout1.json"
            if os.path.exists(layout_path):
                try:
                    with open(layout_path, "r", encoding="utf-8") as f:
                        self.initial_layout = json.load(f)
                    print(f"[✓] Initial layout loaded from {layout_path}")
                    self.glyph_positions.update(self.initial_layout)
                except Exception as e:
                    print(f"[!] Failed to load layout from {layout_path}: {e}")
                    self.initial_layout = {}
            else:
                print(f"[!] No layout file found at {layout_path}. Using procedural layout.")
                self.initial_layout = {}

        # === Defensive: Ensure selected_glyphs exists ===
        if not hasattr(self, "selected_glyphs"):
            self.selected_glyphs = set()

        # === Group glyphs by category ===
        category_map = defaultdict(list)
        for glyph in self.glyphs:
            category = glyph.data.get("Category", "Uncategorized")
            category_map[category].append(glyph)

        # === Layout Configuration ===
        universe_width = 1400
        spacing_x = 220
        spacing_y = 200
        cluster_radius = 80
        glyph_jitter = 20
        cols = 6
        rows = math.ceil(len(category_map) / cols)

        categories = list(category_map.keys())

        for idx, category in enumerate(categories):
            row = idx // cols
            col = idx % cols

            center_x = col * spacing_x + 150 + random.randint(-80, 80)
            center_y = row * spacing_y + 150 + random.randint(-60, 60)

            glyphs = category_map[category]

            for g in glyphs:
                name = g.data.get("Glyph Name", "UNKNOWN")
                if not name or name == "UNKNOWN":
                    print(f"[⏩] Skipping glyph with invalid name: {name}")
                    continue

                # Position from saved layout or generate new
                if name not in self.glyph_positions:
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(0, cluster_radius)
                    jitter_x = random.uniform(-glyph_jitter, glyph_jitter)
                    jitter_y = random.uniform(-glyph_jitter, glyph_jitter)

                    x = center_x + radius * math.cos(angle) + jitter_x
                    y = center_y + radius * math.sin(angle) + jitter_y

                    self.glyph_positions[name] = (x, y)
                    self.initial_layout[name] = (x, y)  # update layout in memory

                x, y = self.glyph_positions[name]
                x_disp = x * self.scale + self.offset_x
                y_disp = y * self.scale + self.offset_y

                # === Hitbox for hover & drag ===
                hitbox_id = self.canvas.create_oval(
                    x_disp - 30, y_disp - 30, x_disp + 30, y_disp + 30,
                    fill="", outline="", tags=("glyph", "glyph_hitbox")
                )
                self.canvas.tag_bind(hitbox_id, "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
                self.canvas.tag_bind(hitbox_id, "<Leave>", lambda e: self.canvas.config(cursor=""))

                # === Node circle ===
                oval_id = self.canvas.create_oval(
                    x_disp - 15, y_disp - 15, x_disp + 15, y_disp + 15,
                    fill="white",
                    outline="cyan" if name in self.selected_glyphs else "black",
                    width=2 if name in self.selected_glyphs else 1,
                    tags=("glyph", "glyph_node")
                )

                # === Label text (shortened glyph name) ===
                text_id = self.canvas.create_text(
                    x_disp, y_disp,
                    text=name[:4],
                    fill="black",
                    font=("Consolas", 9),
                    tags="glyph_text"
                )

                self.glyph_items[name] = (oval_id, text_id, x, y, hitbox_id)

    def handle_left_click_start(self, event):
        self.last_drag_x = event.x
        self.last_drag_y = event.y
        self.dragging_glyph = None

        overlapping = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)

        for item in overlapping:
            tags = self.canvas.gettags(item)
            if "glyph_hitbox" in tags:
                for name, (oval_id, text_id, x, y, hitbox_id) in self.glyph_items.items():
                    if hitbox_id == item:
                        if name in self.selected_glyphs:
                            # Group drag (already selected)
                            self.dragging_glyph = None
                            return
                        else:
                            # New individual selection
                            self.selected_glyphs = {name}
                            self.dragging_glyph = name
                            self.drag_offset = (event.x - x, event.y - y)
                            self.on_left_click(name)  # ✅ Restore metadata callback
                            return

        # Clicked empty space → deselect all
        self.selected_glyphs.clear()
        self.redraw_all()

    def handle_left_drag(self, event):
        dx = event.x - self.last_drag_x
        dy = event.y - self.last_drag_y
        self.last_drag_x = event.x
        self.last_drag_y = event.y

        for name in self.selected_glyphs:
            if name in self.glyph_positions:
                x, y = self.glyph_positions[name]
                new_x, new_y = x + dx / self.scale, y + dy / self.scale
                self.glyph_positions[name] = (new_x, new_y)

        self.redraw_all()
        self.draw_group_bounding_box()

    def handle_left_release(self, event):
        if self.selected_glyphs:
            self.save_layout("layouts/custom_layout1.json")

    def handle_right_click(self, event):
        closest = self.canvas.find_closest(event.x, event.y)
        for name, (oval_id, text_id, x, y, hitbox_id) in self.glyph_items.items():
            if closest[0] in (oval_id, hitbox_id):
                self.show_context_menu(name, event.x_root, event.y_root)
                return

    def show_context_menu(self, glyph_name, x_root, y_root):
        menu = Menu(self.canvas, tearoff=0)
        menu.add_command(label="Trace from here", command=lambda: self.on_right_click(glyph_name, x_root, y_root))
        menu.add_command(label="Morph", command=lambda: print(f"Morph: {glyph_name}"))
        menu.add_command(label="Synthesize", command=lambda: print(f"Synthesize: {glyph_name}"))
        menu.tk_popup(x_root, y_root)

    def draw_trace_overlay(self, trace_path: Optional[List[str]] = None):
        """Draws the symbolic trace pathway with arrows and glow, auto-clearing after timeout."""

        # Cancel existing timer if active
        if hasattr(self, "trace_timer"):
            try:
                self.canvas.after_cancel(self.trace_timer)
            except Exception as e:
                print(f"[!] Failed to cancel previous trace timer: {e}")

        # Initialize overlay tracking
        self.trace_lines = getattr(self, "trace_lines", [])
        self.resonance_glows = getattr(self, "resonance_glows", [])

        # Clear previous visual overlays
        for line in self.trace_lines:
            try:
                self.canvas.delete(line)
            except Exception as e:
                print(f"[!] Error removing trace line: {e}")
        self.trace_lines.clear()

        for glow in self.resonance_glows:
            try:
                self.canvas.delete(glow)
            except Exception as e:
                print(f"[!] Error removing glow overlay: {e}")
        self.resonance_glows.clear()

        # Resolve trace path
        path = trace_path or getattr(self, "latest_trace_path", [])
        print(f"[DEBUG] draw_trace_overlay() input: {trace_path}")
        print(f"[DEBUG] Resolved path: {path}")

        if not path or len(path) < 2:
            if trace_path:
                print("[↪] No valid trace path to draw (too short).")
            return

        self.latest_trace_path = path
        print(f"[🌀] Drawing symbolic trace path of length {len(path)}")

        # Ensure glyph_items are available
        if not hasattr(self, "glyph_items") or not self.glyph_items:
            print("[!] glyph_items is missing or empty — calling redraw_all() to rebuild.")
            if hasattr(self, "redraw_all"):
                self.redraw_all()
            else:
                print("[⛔] redraw_all() not found — cannot proceed.")
                return

        # Verify all glyphs exist before drawing
        missing = [name for name in path if name not in self.glyph_items]
        if missing:
            print(f"[!] Trace aborted — missing glyphs in canvas: {missing}")
            return

        # === Drawing Parameters ===
        arrow_color = "#00FFFF"
        arrow_thickness = 6.0
        arrow_shape = (10, 12, 5)

        glow_color = "#FFD700"
        glow_size = 32
        glow_width = 4
        min_width = 2

        # === Draw Arrows Between Glyphs ===
        for i in range(len(path) - 1):
            start_name = path[i]
            end_name = path[i + 1]
            start = self.glyph_items.get(start_name)
            end = self.glyph_items.get(end_name)

            try:
                x1_logical, y1_logical = start[2], start[3]
                x2_logical, y2_logical = end[2], end[3]

                x1 = x1_logical * self.scale + self.offset_x
                y1 = y1_logical * self.scale + self.offset_y
                x2 = x2_logical * self.scale + self.offset_x
                y2 = y2_logical * self.scale + self.offset_y

                width = max(arrow_thickness - (i * 0.5), min_width)

                arrow = self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=arrow_color,
                    arrow=tk.LAST,
                    width=width,
                    arrowshape=arrow_shape,
                    tags="trace_line"
                )
                self.trace_lines.append(arrow)
                print(f"  → Arrow {i + 1}: {start_name} → {end_name}")
            except Exception as e:
                print(f"[!] Error drawing arrow ({start_name} → {end_name}): {e}")

        # === Glow Each Glyph in Path ===
        for idx, name in enumerate(path):
            item = self.glyph_items.get(name)
            try:
                x_logical, y_logical = item[2], item[3]
                x = x_logical * self.scale + self.offset_x
                y = y_logical * self.scale + self.offset_y

                # Start/end special markers
                highlight_color = "#00FF00" if idx == 0 else "#FF0000" if idx == len(path) - 1 else glow_color

                glow = self.canvas.create_oval(
                    x - glow_size, y - glow_size,
                    x + glow_size, y + glow_size,
                    outline=highlight_color,
                    width=glow_width,
                    dash=(3, 3),
                    tags="trace_glow"
                )
                self.resonance_glows.append(glow)
                print(f"  ✨ Glow: {name} at ({x_logical}, {y_logical})")
            except Exception as e:
                print(f"[!] Error drawing glow for {name}: {e}")

        # === Auto-Clear Timer ===
        try:
            self.trace_timer = self.canvas.after(180000, self.clear_trace_overlay)
            print("[⏳] Trace overlay will clear in 180 seconds.")
        except Exception as e:
            print(f"[!] Failed to start auto-clear timer: {e}")

    def clear_trace_overlay(self):
        """Clears all arrows and glows from the trace overlay."""
        for line in getattr(self, "trace_lines", []):
            self.canvas.delete(line)
        self.trace_lines = []

        for glow in getattr(self, "resonance_glows", []):
            self.canvas.delete(glow)
        self.resonance_glows = []

        self.latest_trace_path = []
        print("[⏱] Trace overlay auto-cleared.")

    def animate_resonance(self):
        """Optional: pulse glyphs based on resonance score."""
        pass  # Placeholder for future animated resonance effects

    def on_mouse_motion(self, event):
        closest = self.canvas.find_closest(event.x, event.y)
        if not closest:
            self.hide_hover_label()
            return

        tags = self.canvas.gettags(closest)
        if "glyph_node" not in tags and "glyph_hitbox" not in tags:
            self.hide_hover_label()
            return

        # Safely iterate through glyphs, handling both 4-tuple and 5-tuple formats
        for name, item in self.glyph_items.items():
            if len(item) == 5:
                oval_id, text_id, x, y, hitbox_id = item
                if closest[0] in (oval_id, text_id, hitbox_id):
                    self.show_hover_label(name, event.x, event.y)
                    return
            elif len(item) == 4:
                oval_id, text_id, x, y = item
                if closest[0] in (oval_id, text_id):
                    self.show_hover_label(name, event.x, event.y)
                    return

        self.hide_hover_label()

    def show_hover_label(self, glyph_name, x, y):
        glyph = self.get_glyph_by_name(glyph_name)
        if not glyph:
            return

        tensor = glyph.unfold()["tensor"]
        labels = ["Val", "Per", "Dis", "Cha", "Grv", "Cla", "Uti", "Dep", "Rec", "Ten"]

        # Format into wrapped rows (3 per line)
        lines = []
        for i in range(0, len(tensor), 3):
            group = zip(labels[i:i + 3], tensor[i:i + 3])
            line = "   ".join(f"{lbl}: {val:.1f}" for lbl, val in group)
            lines.append(line)

        summary = "\n".join(lines)

        # Clear existing label
        self.hide_hover_label()

        padding = 6
        font = ("Consolas", 9)

        text_id = self.canvas.create_text(
            x + 12, y - 20,
            text=summary,
            font=font,
            anchor="nw",
            fill="white",
            tags="hover",
            justify=tk.LEFT
        )

        bbox = self.canvas.bbox(text_id)
        rect_id = self.canvas.create_rectangle(
            bbox[0] - padding, bbox[1] - padding,
            bbox[2] + padding, bbox[3] + padding,
            fill="#222222", outline="#555555", width=1,
            tags="hover"
        )

        self.canvas.tag_raise(text_id, rect_id)
        self.hover_label = [rect_id, text_id]

    def hide_hover_label(self):
        if self.hover_label:
            for item in self.hover_label:
                self.canvas.delete(item)
            self.hover_label = None

    def get_glyph_by_name(self, name: str):
        for g in self.glyphs:
            if g.data.get("Glyph Name") == name:
                return g
        return None

    def start_drag(self, event):
        overlapping = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in overlapping:
            tags = self.canvas.gettags(item)
            if "glyph_hitbox" in tags:
                for name, (oval_id, text_id, x, y, hitbox_id) in self.glyph_items.items():
                    if hitbox_id == item:
                        self.dragging_glyph = name
                        self.drag_offset = (event.x - x, event.y - y)
                        self.glyph_positions_history.append((name, x, y))
                        return

    def do_drag(self, event):
        if not self.dragging_glyph:
            return

        name = self.dragging_glyph
        oval_id, text_id, _, _, hitbox_id = self.glyph_items[name]

        # Convert canvas coords to logical coords (reverse pan/zoom)
        x_display = event.x
        y_display = event.y
        x = (x_display - self.offset_x) / self.scale
        y = (y_display - self.offset_y) / self.scale

        # Prevent overlap (check against logical positions)
        for other, item in self.glyph_items.items():
            if other != name:
                _, _, ox, oy = item[:4]  # Handles both 4-tuple and 5-tuple cases
                dist = ((x - ox) ** 2 + (y - oy) ** 2) ** 0.5
                if dist < 40:
                    return

        # Update logical position
        self.glyph_positions[name] = (x, y)

        # Convert to display coordinates for drawing
        x_disp = x * self.scale + self.offset_x
        y_disp = y * self.scale + self.offset_y

        # Move glyph visually
        self.canvas.coords(oval_id, x_disp - 15, y_disp - 15, x_disp + 15, y_disp + 15)
        self.canvas.coords(text_id, x_disp, y_disp)
        self.canvas.coords(hitbox_id, x_disp - 30, y_disp - 30, x_disp + 30, y_disp + 30)

        # Update internal display position reference
        self.glyph_items[name] = (oval_id, text_id, x, y, hitbox_id)

        # Redraw overlays
        self.redraw_all()

        #ring_counts = self.compute_ring_counts()
        #self.draw_importance_rings(ring_counts)

    def end_drag(self, event):
        if self.dragging_glyph:
            self.on_left_click(self.dragging_glyph)
            self.save_layout("layouts/custom_layout1.json")  # Auto-save layout on drag end
        self.dragging_glyph = None

    def save_layout(self, path=None):
        layout = {name: (x, y) for name, (_, _, x, y, _) in self.glyph_items.items()}
        os.makedirs("layouts", exist_ok=True)

        if path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"layouts/custom_layout_{timestamp}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2)
        print(f"[✓] Layout saved to {path}")

    def load_layout(self, path=None):
        import glob

        if path is None:
            # Match timestamped layout files like: custom_layout_20240415_193042.json
            layout_files = glob.glob("layouts/custom_layout_*.json")
            if layout_files:
                path = max(layout_files, key=os.path.getmtime)
            else:
                path = "layouts/custom_layout1.json"  # Fallback to default if no timestamped found

        if not os.path.exists(path):
            print(f"[!] Layout file not found: {path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # Reset zoom and pan
        self.scale = 0.20
        self.offset_x = 300
        self.offset_y = 200

        # Update internal positions
        for name, (x, y) in layout.items():
            self.glyph_positions[name] = (x, y)

        self.redraw_all()
        print(f"[✓] Layout loaded from {path}")

    def reset_layout(self):
        default_path = "layouts/custom_layout1.json"

        if not os.path.exists(default_path):
            print(f"[!] Default layout file not found: {default_path}")
            return

        with open(default_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # Reset zoom and pan
        self.scale = 0.20
        self.offset_x = 300
        self.offset_y = 200

        # Update internal logical positions
        for name, (x, y) in layout.items():
            self.glyph_positions[name] = (x, y)

        self.redraw_all()
        print("[↺] Layout reset to default (custom_layout1.json).")

    def save_as_default_layout(self):
        self.initial_layout = {name: (x, y) for name, (_, _, x, y, _) in self.glyph_items.items()}
        with open("layouts/custom_layout1.json", "w", encoding="utf-8") as f:
            json.dump(self.initial_layout, f, indent=2)
        print("[✓] Default layout overwritten.")

    def draw_importance_rings(self, glyph_importance: Dict[str, int]):
        # Clear previous rings
        if hasattr(self, "importance_rings"):
            for ring in self.importance_rings:
                self.canvas.delete(ring)
            self.importance_rings.clear()
        else:
            self.importance_rings = []

        # Polarity-based fallback colors
        polarity_colors = {
            "Positive": "#22FF66",
            "Negative": "#FF4444",
            "Neutral": "#CCCCCC",
            "Ambiguous": "#8888FF",
            "": "#AAAAAA"
        }

        for name, num_rings in glyph_importance.items():
            if name not in self.glyph_items:
                continue

            try:
                _, _, x, y, _ = self.glyph_items[name]
                x_disp = x * self.scale + self.offset_x
                y_disp = y * self.scale + self.offset_y

                glyph = self.get_glyph_by_name(name)
                polarity = glyph.data.get("Polarity", "") if glyph else ""
                category = glyph.data.get("Category", "") if glyph else ""
                color = polarity_colors.get(polarity, "#AAAAAA")

                # 🔥 Handle resonance safely
                resonance = 0.0
                ring_width = 1
                if self.symbolic_network:
                    try:
                        resonance = self.symbolic_network.calculate_resonance(name)
                    except ZeroDivisionError:
                        print(f"[⚠️] Resonance calc failed for {name} — defaulting to 0.")
                        resonance = 0.0

                    if resonance >= 0.75:
                        color = "#FF2222"
                        ring_width = 4
                    elif resonance >= 0.5:
                        color = "#FF5555"
                        ring_width = 3
                    elif resonance >= 0.25:
                        color = "#CC8888"
                        ring_width = 2
                    else:
                        color = "#996666"
                        ring_width = 1

                # 🔁 Draw importance rings
                for i in range(num_rings):
                    radius = 18 + (i + 1) * 7
                    ring = self.canvas.create_oval(
                        x_disp - radius, y_disp - radius,
                        x_disp + radius, y_disp + radius,
                        outline=color, dash=(3, 3), width=ring_width,
                        tags="importance_ring"
                    )
                    self.importance_rings.append(ring)

                # 🟣 Composite glyph indicator
                if category.strip().lower() == "composite":
                    ring = self.canvas.create_oval(
                        x_disp - 22, y_disp - 22,
                        x_disp + 22, y_disp + 22,
                        outline="#AA66FF", width=3,
                        tags="importance_ring"
                    )
                    self.importance_rings.append(ring)

            except Exception as e:
                print(f"[!] Failed to draw importance ring for '{name}': {e}")

        def resonance_to_color(resonance):
            """Map resonance [0,1] to hex color from brown to red."""
            from colorsys import hsv_to_rgb
            hue = 0.05 - (0.05 * resonance)  # brown (~30°) to red (0°)
            r, g, b = hsv_to_rgb(hue, 0.8, 1.0)
            return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))

        for name, num_rings in glyph_importance.items():
            if name not in self.glyph_items:
                continue

            # Logical position
            _, _, x, y, _ = self.glyph_items[name]

            # Convert to display coordinates
            x_disp = x * self.scale + self.offset_x
            y_disp = y * self.scale + self.offset_y

            # Get glyph polarity and category
            glyph = self.get_glyph_by_name(name)
            polarity = glyph.data.get("Polarity", "") if glyph else ""
            category = glyph.data.get("Category", "") if glyph else ""
            polarity_color = polarity_colors.get(polarity, "#AAAAAA")

            # Calculate resonance-based rim color
            resonance = self.symbolic_network.calculate_resonance(name) if self.symbolic_network else 0.0
            resonance_color = resonance_to_color(resonance)

            # Draw concentric dashed rings using polarity color
            for i in range(num_rings):
                radius = 18 + (i + 1) * 7
                ring = self.canvas.create_oval(
                    x_disp - radius, y_disp - radius,
                    x_disp + radius, y_disp + radius,
                    outline=polarity_color,
                    dash=(3, 3), width=1,
                    tags="importance_ring"
                )
                self.importance_rings.append(ring)

            # 🔴 Resonance rim (solid glow layer)
            if num_rings > 0:
                rim = self.canvas.create_oval(
                    x_disp - 16, y_disp - 16,
                    x_disp + 16, y_disp + 16,
                    outline=resonance_color, width=2,
                    tags="importance_ring"
                )
                self.importance_rings.append(rim)

            # 🟣 Solid inner ring for composite glyphs
            if category.strip().lower() == "composite":
                ring = self.canvas.create_oval(
                    x_disp - 22, y_disp - 22,
                    x_disp + 22, y_disp + 22,
                    outline="#AA66FF", width=2,
                    tags="importance_ring"
                )
                self.importance_rings.append(ring)

    def compute_ring_counts(self):
        ring_counts = {}
        max_score = 1  # avoid division by zero

        # You may replace this with live data
        for glyph in self.glyphs:
            name = glyph.data.get("Glyph Name", "")
            freq = glyph.data.get("Trace Frequency", 1)
            conn = glyph.data.get("Connection Count", 1)
            score = freq * 0.6 + conn * 0.4
            ring_counts[name] = score
            max_score = max(max_score, score)

        # Normalize and map to 0–3 rings
        for name in ring_counts:
            norm = ring_counts[name] / max_score
            ring_counts[name] = min(3, math.ceil(norm * 3))
        return ring_counts

    def handle_zoom(self, event):
        zoom_factor = 1.2 if event.delta > 0 else 0.85
        new_scale = self.scale * zoom_factor
        new_scale = max(0.1, min(5.0, new_scale))  # Clamp zoom

        # Cursor position before scaling
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Convert to logical coordinates (before scale)
        logical_x = (x - self.offset_x) / self.scale
        logical_y = (y - self.offset_y) / self.scale

        # Update scale
        self.scale = new_scale

        # Recalculate offset so cursor remains on same logical point
        self.offset_x = x - logical_x * self.scale
        self.offset_y = y - logical_y * self.scale

        self.redraw_all()

    def start_pan(self, event):
        self.pan_start = (event.x, event.y)

    def do_pan(self, event):
        if not self.pan_start:
            return
        dx = event.x - self.pan_start[0]
        dy = event.y - self.pan_start[1]
        self.offset_x += dx
        self.offset_y += dy
        self.pan_start = (event.x, event.y)
        self.redraw_all()

    def end_pan(self, event):
        self.pan_start = None

    def redraw_all(self):
        """Clear and redraw all glyphs and overlays on the canvas."""
        try:
            self.canvas.delete("all")
            self.glyph_items.clear()
        except Exception as e:
            print(f"[!] Failed to clear canvas: {e}")
            return

        # Recalculate layout and redraw glyphs
        try:
            self.layout_glyphs()
        except Exception as e:
            print(f"[!] Failed to layout glyphs: {e}")
            return

        # Re-draw decorative overlays (resonance rings etc.)
        try:
            ring_counts = self.compute_ring_counts()
            self.draw_importance_rings(ring_counts)
        except Exception as e:
            print(f"[!] Failed to draw importance rings: {e}")

        # ✅ Always reapply trace overlay last
        if hasattr(self, "latest_trace_path") and len(self.latest_trace_path) >= 2:
            print("[↻] Re-drawing trace overlay after canvas update.")
            try:
                self.draw_trace_overlay(self.latest_trace_path)
            except Exception as e:
                print(f"[!] Failed to draw trace overlay: {e}")

    def calculate_glyph_importance(self, symbolic_network) -> Dict[str, int]:
        scores = {}

        # Step 1: Compute raw scores based on usage + connection strength
        for name, node in symbolic_network.nodes.items():
            total_strength = sum(node.connections.values())
            score = node.usage_count + total_strength
            scores[name] = score

        if not scores:
            return {}

        # Step 2: Normalize scores
        max_score = max(scores.values())
        normalized = {k: v / max_score for k, v in scores.items()}

        # Step 3: Map normalized score to ring count (0–3)
        ring_map = {}
        for name, score in normalized.items():
            if score >= 0.75:
                ring_map[name] = 3
            elif score >= 0.5:
                ring_map[name] = 2
            elif score >= 0.25:
                ring_map[name] = 1
            else:
                ring_map[name] = 0

        return ring_map

    def start_drag_box(self, event):
        self.selection_start = (event.x, event.y)
        if self.selection_box:
            self.canvas.delete(self.selection_box)
        self.selection_box = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="#00FFFF", dash=(3, 3), width=2, tags="selection_box"
        )

    def update_drag_box(self, event):
        if self.selection_box and self.selection_start:
            x0, y0 = self.selection_start
            self.canvas.coords(self.selection_box, x0, y0, event.x, event.y)

    def finalize_drag_box(self, event):
        if not self.selection_box:
            return

        x0, y0, x1, y1 = self.canvas.coords(self.selection_box)
        x_min, x_max = sorted([x0, x1])
        y_min, y_max = sorted([y0, y1])

        self.selected_glyphs.clear()

        for name, (oval_id, text_id, x, y, hitbox_id) in self.glyph_items.items():
            x_disp = x * self.scale + self.offset_x
            y_disp = y * self.scale + self.offset_y
            if x_min <= x_disp <= x_max and y_min <= y_disp <= y_max:
                self.selected_glyphs.add(name)
                self.canvas.itemconfig(oval_id, outline="cyan", width=2)

        self.canvas.delete(self.selection_box)
        self.selection_box = None
        self.selection_start = None
        self.draw_group_bounding_box()

    def start_group_drag(self, event):
        self.last_drag_x = event.x
        self.last_drag_y = event.y

    def perform_group_drag(self, event):
        dx = (event.x - self.last_drag_x) / self.scale
        dy = (event.y - self.last_drag_y) / self.scale
        self.last_drag_x = event.x
        self.last_drag_y = event.y

        for name in self.selected_glyphs:
            if name in self.glyph_positions:
                x, y = self.glyph_positions[name]
                new_x, new_y = x + dx, y + dy
                self.glyph_positions[name] = (new_x, new_y)

                # Update canvas position
                x_disp = new_x * self.scale + self.offset_x
                y_disp = new_y * self.scale + self.offset_y

                oval_id, text_id, _, _, hitbox_id = self.glyph_items[name]
                self.canvas.coords(oval_id, x_disp - 15, y_disp - 15, x_disp + 15, y_disp + 15)
                self.canvas.coords(text_id, x_disp, y_disp)
                self.canvas.coords(hitbox_id, x_disp - 30, y_disp - 30, x_disp + 30, y_disp + 30)

                self.glyph_items[name] = (oval_id, text_id, new_x, new_y, hitbox_id)

        self.draw_trace_overlay()

        self.draw_group_bounding_box()

    def draw_group_bounding_box(self):
        if self.group_drag_box:
            self.canvas.delete(self.group_drag_box)
            self.group_drag_box = None

        if not self.selected_glyphs:
            return

        x_vals, y_vals = [], []
        for name in self.selected_glyphs:
            x, y = self.glyph_positions[name]
            x_disp = x * self.scale + self.offset_x
            y_disp = y * self.scale + self.offset_y
            x_vals.append(x_disp)
            y_vals.append(y_disp)

        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)

        self.group_drag_box = self.canvas.create_rectangle(
            x_min - 20, y_min - 20, x_max + 20, y_max + 20,
            outline="#00FFFF", dash=(4, 2), width=2, tags="group_drag_box"
        )

