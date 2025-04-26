# nyseal_blackbox.py

import json, base64, time
from hashlib import sha256
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
from ctypes import memset, addressof, c_char, sizeof
import sys


# Loader
class NysealBlackboxLoader:
    def __init__(self, key_path="./models/.cache/.sig..x"):
        import sys

        # Support PyInstaller --onefile mode
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        key_file = os.path.join(base_path, "models", ".cache", ".sig..x")

        with open(key_file, "r", encoding="cp1252") as f:
            wrapped = f.read().strip()
            if wrapped.startswith("§") and wrapped.endswith("§"):
                b64_key = wrapped.strip("§")
                self.password = base64.b64decode(b64_key)
            else:
                raise ValueError("Key file format is invalid or not properly wrapped.")
        self.modules = {}



    def load_encrypted_module(self, name, path, exposed=None, retries=5, delay=0.5):
        for attempt in range(retries):
            try:
                # Use _MEIPASS-safe path if in a bundled environment
                base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
                full_path = os.path.join(base_path, path)

                print(f"[🔐] Loading: {full_path}")
                with open(full_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                salt = base64.b64decode(payload["salt"])
                iv = base64.b64decode(payload["iv"])
                tag = base64.b64decode(payload["tag"])
                ciphertext = base64.b64decode(payload["encrypted_payload"])

                kdf = PBKDF2HMAC(hashes.SHA256(), 32, salt, 100000, backend=default_backend())
                key = kdf.derive(self.password)

                cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
                decryptor = cipher.decryptor()
                padded_code = decryptor.update(ciphertext) + decryptor.finalize()

                unpadder = padding.PKCS7(128).unpadder()
                code = unpadder.update(padded_code) + unpadder.finalize()
                code_str = code.decode()

                if name == "glyphset4c":
                    self.modules[name] = {
                        k: code_str for k in (exposed or [])
                    }
                    return self.modules[name]

                exec_globals = {"__name__": "__blackbox__"}
                from glyph_core_v1 import Glyph
                from glyph_graph_v1 import GlyphGraph
                exec_globals["Glyph"] = Glyph
                exec_globals["GlyphGraph"] = GlyphGraph

                if "symbolic_memory" in name:
                    exec_globals.update({
                        "SymbolicTrace": self.modules.get("symbolic_memory", {}).get("SymbolicTrace"),
                    })

                exec(code_str, exec_globals)

                self.modules[name] = {
                    k: exec_globals[k] for k in (exposed or []) if k in exec_globals
                }

                return self.modules[name]

            except Exception as e:
                print(f"[!] Retry {attempt + 1}/{retries} failed for {name}: {e}")
                time.sleep(delay)

        raise RuntimeError(f"[✘] Could not load {name} after {retries} attempts.")

    def get(self, module_name, symbol_name):
        return self.modules.get(module_name, {}).get(symbol_name)
