from retype.resource_handler import root_path, getLibraryPath


default_config = {
    "user_dir": root_path,
    "library_paths": [getLibraryPath()],
    "prompt": ">",
    "rdict": {
        "\ufffc": [" "],
        "\u00ae": ["r", "R"],
        "\u00a9": ["c", "C"],
        "\u201c": ["\""],
        "\u201d": ["\""],
        "\u2018": ["'"],
        "\u2019": ["'"]
    },
    "window": {
        "x": None,
        "y": None,
        "w": 600,
        "h": 600,
        "save_on_quit": True
    }
}
