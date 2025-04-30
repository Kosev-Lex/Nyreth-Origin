# -- Nyreth_v1.spec --
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['Nyreth_v1.py'],
    pathex=['.'],
binaries=[('C:\\Program Files\\Python312\\python312.dll', '.')],
datas=[
    ('layouts/custom_layout1.json', 'layouts'),
    ('models/.cache/.sig..x', 'models/.cache'),
    ('logs/*.json', 'logs'),
    ('encrypted/glyphset4c_v1.nyrethenc', 'encrypted'),
    ('encrypted/nyreth_loader_v1.nyrethenc', 'encrypted'),
    ('encrypted/querydistiller_v1.nyrethenc', 'encrypted'),
    ('encrypted/semantic_reasoning_overlay_v1.nyrethenc', 'encrypted'),
    ('encrypted/interpretive_compression_v1.nyrethenc', 'encrypted'),
    ('encrypted/nyreth_bridge_v1.nyrethenc', 'encrypted'),
    ('encrypted/traversal_engine_v1.nyrethenc', 'encrypted'),
    ('encrypted/insight_synthesizer_v1.nyrethenc', 'encrypted'),
    ('encrypted/symbolic_network_v1.nyrethenc', 'encrypted'),
    ('encrypted/symbolic_memory_v1.nyrethenc', 'encrypted'),
    ('encrypted/recursive_engine_v1.nyrethenc', 'encrypted'),
    ('symbolic_memory/*.json', 'symbolic_memory'),
    ('symbolic_memory_v1/*.json', 'symbolic_memory_v1'),
    ('symbolic_memory_v1/*.log', 'symbolic_memory_v1'),
    ('trace_logs/*.json', 'trace_logs'),
    ('traces/*.json', 'traces'),
    ('Glyphdef.json', '.'),
    ('symbolic_query_log.jsonl', '.')
],


    hiddenimports=[
        'nyreth_encrypted_loader_v1',
        'nyseal_blackbox',
        'glyph_graph_v1',
        'glyph_library_v1',
        'pseudoLLM_v1',
        'cognitive_memory_v1',
        'glyph_synthesizer_v1',
        'graph_viewer_v1',
        'nyreth_plugin_v1',
        'glyph_universe_canvas_v1',
        'morph_interpolator_v1',
        'glyph_core_v1',
        'morph_engine_v1',
        'symbolic_network_viewer_v1',
        'sentence_transformers',
        'sentence_transformers.SentenceTransformer',
        'sentence_transformers.models',
        'sentence_transformers.util'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Nyreth_v1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Nyreth_v1'
)

