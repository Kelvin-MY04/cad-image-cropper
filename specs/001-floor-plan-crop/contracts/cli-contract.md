# CLI Contract: cad-crop

**Branch**: `001-floor-plan-crop` | **Date**: 2026-03-04

---

## Command

```
cad-crop [OPTIONS] INPUT_PATH
```

---

## Arguments

| Name | Required | Description |
|------|----------|-------------|
| `INPUT_PATH` | Yes | Path to a single PNG file or a directory of PNG files |

---

## Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output-dir` | `-o` | `Path` | `/export` | Directory where cropped output files are written |
| `--input-dir` | `-i` | `Path` | `/import` | Default input directory (used when INPUT_PATH not supplied) |
| `--verbose` | `-v` | `bool` flag | `False` | Print per-file success messages in addition to warnings |
| `--help` | | | | Show usage and exit |

---

## Invocation Modes

### Single file

```bash
cad-crop /import/floor_plan_A.png
# Output written to /export/floor_plan_A.png
```

### Single file with explicit output

```bash
cad-crop /import/floor_plan_A.png --output-dir /results
# Output written to /results/floor_plan_A.png
```

### Batch (directory)

```bash
cad-crop /import
# Processes every *.png in /import; outputs to /export/
```

### Batch with explicit output

```bash
cad-crop /import --output-dir /results
```

---

## Output Filename Rules

1. Output filename equals the input filename.
2. If the output file already exists:
   - Insert an incrementing numeric suffix before the extension.
   - `floor_plan.png` → `floor_plan_1.png` → `floor_plan_2.png` → …

---

## Standard Output (stdout)

Verbose mode only (`--verbose`):
```
OK: floor_plan_A.png -> /export/floor_plan_A.png
OK: floor_plan_B.png -> /export/floor_plan_B.png
```

Non-verbose (default): no stdout on success.

---

## Standard Error (stderr)

Warnings and errors are always written to stderr.

### Model unavailable (once per run)

```
WARNING: HuggingFace model could not be loaded — running in classical detection mode only.
```

### No border detected (per file)

```
WARNING: No border detected in floor_plan_C.png — skipped.
```

### Corrupt or unreadable file (per file)

```
WARNING: Could not open floor_plan_D.png as a valid PNG — skipped.
```

### Unexpected error (per file)

```
ERROR: floor_plan_E.png failed — <descriptive message>.
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All files processed (some may have been skipped with warnings) |
| `1` | Fatal error: INPUT_PATH does not exist or is not a PNG/directory |
| `2` | Fatal error: output directory could not be created |

---

## Batch Summary (always printed to stdout at end of batch)

```
Processed: 48 | Skipped: 2 | Failed: 0
```

Single-file mode prints no summary.

---

## Constraints

- The tool MUST NOT modify, rename, or delete any input file.
- The tool MUST create the output directory if it does not exist.
- The tool MUST process all files in a batch even if individual files produce warnings.
- The tool exits with code `0` when skips occur; skips are not failures.
