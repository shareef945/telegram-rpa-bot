import importlib
import os


def load_plugins():
    plugins = {}
    plugin_dir = os.path.dirname(__file__)
    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            module = importlib.import_module(f"plugins.{module_name}")
            if hasattr(module, "setup"):
                plugins[module_name] = module.setup()
    return plugins
