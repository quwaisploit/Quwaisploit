import os
import importlib.util

class ModuleLoader:
    def __init__(self, base_dir="modules"):
        self.base_dir = base_dir
        self.modules = {}

    def load_modules(self):
        self.modules.clear()
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            return

        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    
                    # Buat nama modul berdasarkan path relatif (misal: exploit/example/sample_exploit)
                    rel_path = os.path.relpath(file_path, self.base_dir)
                    mod_name = os.path.splitext(rel_path)[0].replace(os.sep, '/')
                    
                    # Load module secara dinamis
                    spec = importlib.util.spec_from_file_location(mod_name, file_path)
                    mod = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(mod)
                        if hasattr(mod, 'Module'):
                            self.modules[mod_name] = mod.Module()
                    except Exception as e:
                        print(f"[-] Gagal memuat modul {mod_name}: {e}")

        return self.modules
