import os
from nyseal_blackbox import NysealBlackboxLoader


def load_nyreth_bridge(silent_mode=False):
    # === Initialize BlackBox Loader with explicit key path ===
    loader = NysealBlackboxLoader(key_path="./models/.cache/.sig..x")

    try:
        recursive_engine_mod = loader.load_encrypted_module(
            "recursive_engine", "encrypted/recursive_engine_v1.nyrethenc", ["RecursiveEngine"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load recursive_engine module: {e}")

    try:
        symbolic_memory_mod = loader.load_encrypted_module(
            "symbolic_memory", "encrypted/symbolic_memory_v1.nyrethenc", ["SymbolicMemory"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load symbolic_memory module: {e}")

    try:
        symbolic_network_mod = loader.load_encrypted_module(
            "symbolic_network", "encrypted/symbolic_network_v1.nyrethenc", ["SymbolicMemoryNetwork"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load symbolic_network module: {e}")

    try:
        insight_synthesizer_mod = loader.load_encrypted_module(
            "insight_synthesizer", "encrypted/insight_synthesizer_v1.nyrethenc", ["InsightSynthesizer"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load insight_synthesizer module: {e}")

    try:
        traversal_engine_mod = loader.load_encrypted_module(
            "traversal_engine", "encrypted/traversal_engine_v1.nyrethenc", ["TraversalEngine"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load traversal_engine module: {e}")

    try:
        nyreth_bridge_mod = loader.load_encrypted_module(
            "nyreth_bridge", "encrypted/nyreth_bridge_v1.nyrethenc", ["NyrethBridge"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load nyreth_bridge module: {e}")

    try:
        ic_mod = loader.load_encrypted_module(
            "interpretive_compression", "encrypted/interpretive_compression_v1.nyrethenc", ["InterpretiveCompressor"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load interpretive_compression module: {e}")

    try:
        sro_mod = loader.load_encrypted_module(
            "semantic_reasoning_overlay", "encrypted/semantic_reasoning_overlay_v1.nyrethenc", ["SemanticReasoningOverlay"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load semantic_reasoning_overlay module: {e}")

    try:
        distiller_mod = loader.load_encrypted_module(
            "querydistiller", "encrypted/querydistiller_v1.nyrethenc", ["QueryDistiller"]
        )
    except Exception as e:
        raise RuntimeError(f"[✘] Failed to load querydistiller module: {e}")

    # === Load Glyph Library (not encrypted) ===
    from glyph_library_v1 import GlyphLibrary
    glyph_library = GlyphLibrary("encrypted/glyphset4c_v1.nyrethenc")
    glyph_library.load()

    # === Instantiate Classes from Modules ===
    SymbolicMemory = symbolic_memory_mod["SymbolicMemory"]
    SymbolicMemoryNetwork = symbolic_network_mod["SymbolicMemoryNetwork"]
    InsightSynthesizer = insight_synthesizer_mod["InsightSynthesizer"]
    RecursiveEngine = recursive_engine_mod["RecursiveEngine"]
    TraversalEngine = traversal_engine_mod["TraversalEngine"]
    NyrethBridge = nyreth_bridge_mod["NyrethBridge"]

    symbolic_memory = SymbolicMemory(glyph_library=glyph_library)
    symbolic_network = SymbolicMemoryNetwork()
    insight_synthesizer = InsightSynthesizer(symbolic_memory)

    from glyph_graph_v1 import GlyphGraph
    glyph_graph = GlyphGraph()
    glyph_graph.build_from_library(glyph_library)

    recursive_engine = RecursiveEngine(
        graph=glyph_graph,
        symbolic_network=symbolic_network,
        symbolic_memory=symbolic_memory,
        insight_synthesizer=insight_synthesizer
    )

    traversal_engine = TraversalEngine(
        recursive_engine=recursive_engine,
        memory=symbolic_memory,
        insight_synthesizer=insight_synthesizer,
        glyph_library=glyph_library,
        universe_canvas=None,
        output_widget=None,
        status_var=None,
        ic_output_widget=None,
        sro_output_widget=None
    )

    bridge = NyrethBridge(
        symbolic_memory=symbolic_memory,
        symbolic_network=symbolic_network,
        insight_synthesizer=insight_synthesizer
    )

    bridge.bind_runtime(
        traversal_engine=traversal_engine,
        glyph_library=glyph_library
    )

    return bridge


def load_encrypted_symbols(module_key, symbol):
    from nyseal_blackbox import NysealBlackboxLoader
    loader = NysealBlackboxLoader(key_path="./models/.cache/.sig..x")
    mod = loader.load_encrypted_module(module_key, f"encrypted/{module_key}_v1.nyrethenc", [symbol])
    if symbol not in mod:
        raise KeyError(f"[✘] Symbol '{symbol}' not found in decrypted module '{module_key}'.")
    return mod[symbol]
