import json
import os
from collections import defaultdict
from typing import Dict

SKIP_DIRS = {
    'node_modules', 'vendor', '.git', '__pycache__', 'dist', 'build',
    '.tox', 'venv', '.venv', 'env', '.env', 'target', 'out', '.next',
    '.nuxt', 'coverage', '.cache', 'bower_components', 'output',
}

# Pure data/config/markup formats — never meaningfully "code".
# HTML, CSS etc. are intentionally excluded from this list.
NON_CODE_LANGUAGES = {
    'Markdown', 'MDX', 'YAML', 'TOML', 'JSON', 'XML', 'TeX', 'Batchfile',
}


def _build_maps():
    languages_path = os.path.join(os.path.dirname(__file__), 'languages.json')
    with open(languages_path, 'r', encoding='utf-8') as f:
        languages = json.load(f)

    ext_map = {}
    filename_map = {}

    for lang, config in languages.items():
        for ext in config.get('extensions', []):
            if ext not in ext_map:
                ext_map[ext] = lang
        for filename in config.get('filenames', []):
            if filename not in filename_map:
                filename_map[filename] = lang

    return ext_map, filename_map


EXTENSION_MAP, FILENAME_MAP = _build_maps()


def _count_lines(filepath: str) -> int:
    try:
        with open(filepath, 'rb') as f:
            if b'\x00' in f.read(512):
                return 0
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def count_loc(repo_path: str, excluded_languages: set = None) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    skip = {l.lower() for l in NON_CODE_LANGUAGES | (excluded_languages or set())}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            language = FILENAME_MAP.get(filename)
            if language is None:
                ext = os.path.splitext(filename)[1].lower()
                language = EXTENSION_MAP.get(ext)

            if language is None or language.lower() in skip:
                continue

            filepath = os.path.join(root, filename)
            line_count = _count_lines(filepath)
            if line_count > 0:
                counts[language] += line_count

    return dict(counts)
