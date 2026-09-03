# codepack

A simple CLI tool to pack a project into a clean, LLM-ready context (for Claude, ChatGPT, Gemini, etc.) and copy it straight to your clipboard.

I got tired of manually copying and pasting multiple files, dealing with `.gitignore` junk, and accidentally pasting `.env` keys into LLMs. This tool handles all of that in one command.

---

## What it does

- Copies your project straight to your clipboard with `codepack -c`.
- Automatically respects `.gitignore` and skips `.git`, `node_modules`, `venv`, lock files, and binaries.
- Compact mode (`--compact`): extracts classes, functions, and type hints while omitting function bodies. Saves ~70% of tokens while letting the LLM see your whole project structure.
- Redacts secrets: catches OpenAI, Anthropic, Google, GitHub, and AWS keys before they leave your machine.
- Generates an ASCII project tree and calculates estimated tokens.
- Supports Markdown, Claude-style XML, and JSON.
- Zero dependencies: runs with standard library Python 3.8+.

---

## Quickstart

Run directly:
```bash
python codepack.py -c
```

Or on Windows, double-click `codepack.bat` for an interactive menu.

### Common commands

Pack entire folder into clipboard:
```bash
python codepack.py -c
```

Compact mode (signatures only, minimal tokens):
```bash
python codepack.py --compact -c
```

Pack without test files:
```bash
python codepack.py --skip-tests -c
```

Filter by extensions and limit tree depth:
```bash
python codepack.py --only py,ts --max-depth 2 -c
```

Output to file instead of clipboard:
```bash
python codepack.py -o prompt.md
```

Format for Claude (XML documents schema):
```bash
python codepack.py -f xml -c
```

---

## Installation

Clone the repo and install it locally:
```bash
git clone https://github.com/Frozen-starTony/codepack.git
cd codepack
pip install -e .
```

Once installed, you can just run `codepack` anywhere:
```bash
codepack -c
```

Optional terminal colors:
```bash
pip install "codepack-cli[full]"
```

---

## Options

- `-c`, `--clipboard`: Copy output directly to clipboard.
- `--compact`: Keep only signatures/classes, skip function bodies.
- `--skip-tests`: Exclude test folders and files.
- `--max-depth <int>`: Limit directory tree depth.
- `-o`, `--output <path>`: Write to file.
- `-f`, `--format [markdown|xml|json]`: Output format (default: markdown).
- `--only <exts>`: Filter file extensions (e.g. `py,ts,json`).
- `--exclude <patterns>`: Custom glob patterns to ignore.
- `--tree-only`: Print only the project tree.
- `-i`, `--instructions <text>`: Prepend prompt instructions.
- `--no-security`: Disable secret redaction.

---

## Tests

```bash
python -m unittest discover -s tests
```

---

## License

MIT
