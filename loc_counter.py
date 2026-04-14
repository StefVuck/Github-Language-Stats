import os
from collections import defaultdict
from typing import Dict

EXTENSION_MAP = {
    '.py': 'Python', '.pyw': 'Python', '.pyi': 'Python',
    '.js': 'JavaScript', '.mjs': 'JavaScript', '.cjs': 'JavaScript', '.jsx': 'JavaScript',
    '.ts': 'TypeScript', '.tsx': 'TypeScript', '.mts': 'TypeScript',
    '.java': 'Java',
    '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++', '.hpp': 'C++', '.hh': 'C++', '.hxx': 'C++',
    '.c': 'C', '.h': 'C',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby', '.rake': 'Ruby', '.gemspec': 'Ruby',
    '.php': 'PHP', '.php3': 'PHP', '.php4': 'PHP', '.php5': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin', '.kts': 'Kotlin',
    '.dart': 'Dart',
    '.sh': 'Shell', '.bash': 'Shell', '.zsh': 'Shell', '.fish': 'Shell',
    '.html': 'HTML', '.htm': 'HTML',
    '.css': 'CSS',
    '.scala': 'Scala', '.sc': 'Scala',
    '.r': 'R',
    '.m': 'Objective-C', '.mm': 'Objective-C',
    '.vue': 'Vue',
    '.ipynb': 'Jupyter Notebook',
    '.lua': 'Lua',
    '.pl': 'Perl', '.pm': 'Perl',
    '.hs': 'Haskell', '.lhs': 'Haskell',
    '.ex': 'Elixir', '.exs': 'Elixir',
    '.clj': 'Clojure', '.cljs': 'Clojure', '.cljc': 'Clojure',
    '.vim': 'Vim Script',
    '.sql': 'SQL',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.groovy': 'Groovy', '.gradle': 'Groovy',
    '.ps1': 'PowerShell', '.psm1': 'PowerShell', '.psd1': 'PowerShell',
    '.coffee': 'CoffeeScript',
    '.el': 'Emacs Lisp',
    '.ml': 'OCaml', '.mli': 'OCaml',
    '.fs': 'F#', '.fsi': 'F#', '.fsx': 'F#',
    '.erl': 'Erlang', '.hrl': 'Erlang',
    '.asm': 'Assembly',
    '.pas': 'Pascal', '.pp': 'Pascal',
    '.f90': 'Fortran', '.f95': 'Fortran', '.f03': 'Fortran', '.for': 'Fortran',
    '.rkt': 'Racket',
    '.scm': 'Scheme', '.ss': 'Scheme',
    '.lisp': 'Common Lisp', '.cl': 'Common Lisp',
    '.jl': 'Julia',
    '.zig': 'Zig',
    '.cr': 'Crystal',
    '.nim': 'Nim',
    '.d': 'D',
    '.sol': 'Solidity',
    '.mk': 'Makefile', '.mak': 'Makefile',
    '.yaml': 'YAML', '.yml': 'YAML',
    '.toml': 'TOML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.md': 'Markdown', '.markdown': 'Markdown',
    '.tex': 'TeX', '.sty': 'TeX',
    '.bat': 'Batchfile', '.cmd': 'Batchfile',
    '.elm': 'Elm',
    '.glsl': 'GLSL', '.vert': 'GLSL', '.frag': 'GLSL',
    '.svelte': 'Svelte',
    '.less': 'Less',
    '.tcl': 'Tcl',
    '.nix': 'Nix',
    '.gd': 'GDScript',
    '.hx': 'Haxe',
    '.mdx': 'MDX',
    '.vhd': 'VHDL', '.vhdl': 'VHDL',
    '.sv': 'SystemVerilog', '.svh': 'SystemVerilog',
    '.pyx': 'Cython', '.pxd': 'Cython',
    '.adb': 'Ada', '.ads': 'Ada',
    '.bicep': 'Bicep',
    '.odin': 'Odin',
    '.gleam': 'Gleam',
    '.wat': 'WebAssembly',
}

FILENAME_MAP = {
    'Makefile': 'Makefile',
    'Dockerfile': 'Dockerfile',
    'Rakefile': 'Ruby',
    'Gemfile': 'Ruby',
}

SKIP_DIRS = {
    'node_modules', 'vendor', '.git', '__pycache__', 'dist', 'build',
    '.tox', 'venv', '.venv', 'env', '.env', 'target', 'out', '.next',
    '.nuxt', 'coverage', '.cache', 'bower_components',
}


def _count_lines(filepath: str) -> int:
    try:
        with open(filepath, 'rb') as f:
            if b'\x00' in f.read(512):
                return 0
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def count_loc(repo_path: str) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            language = FILENAME_MAP.get(filename)
            if language is None:
                ext = os.path.splitext(filename)[1].lower()
                language = EXTENSION_MAP.get(ext)

            if language is None:
                continue

            filepath = os.path.join(root, filename)
            line_count = _count_lines(filepath)
            if line_count > 0:
                counts[language] += line_count

    return dict(counts)
