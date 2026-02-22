import pathlib

CURRENT_DIR = pathlib.Path(__file__).parent

TEMP_DIR = CURRENT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

SAVES_DIR = CURRENT_DIR / "saves"
SAVES_DIR.mkdir(exist_ok=True)

ASSETS_DIR = CURRENT_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

HTML_ASSETS_DIR = ASSETS_DIR / "html"
HTML_ASSETS_DIR.mkdir(exist_ok=True)

IMAGES_ASSETS_DIR = ASSETS_DIR / "img"
IMAGES_ASSETS_DIR.mkdir(exist_ok=True)
