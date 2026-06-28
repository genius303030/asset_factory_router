# AI Asset Factory + Model Router V0.2_DEV

A core system for generating structured prompt packs and model routing plans for AI asset generation.

## Installation
```bash
pip install -e .
```

## CLI Commands
- `asset-factory demo`
- `asset-factory create --brief <path> --out <path>`
- `asset-factory route --task <type> --style <style> --quality <q> --budget <b> --speed <s>`
- `asset-factory validate --brief <path>`
- `asset-factory inspect --pack <path>`
- `asset-factory list-providers`

## Testing
```bash
python -m unittest discover tests
```
