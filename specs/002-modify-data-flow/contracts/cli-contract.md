# CLI Contract: cad-crop (v2)

**Branch**: `002-modify-data-flow` | **Date**: 2026-03-04
**Supersedes**: `specs/001-floor-plan-crop/contracts/cli-contract.md`

---

## Command

```
cad-crop [OPTIONS] [INPUT_PATH]
```

`INPUT_PATH` is now **optional**. When omitted, the tool defaults to `/import`.

---

## Arguments

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `INPUT_PATH` | No | `/import` | Path to a single PNG file or a directory of PNG files |

---

## Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output-dir` | `-o` | `Path` | `/export` | Directory where cropped output files are written |
| `--verbose` | `-v` | `bool` flag | `False` | Print per-file success messages in addition to warnings |
| `--help` | | | | Show usage and exit |

---

## Invocation Modes

### Zero-argument (new)

```bash
cad-crop
# Equivalent to: cad-crop /import --output-dir /export
# Processes every *.png in /import; outputs to /export/
```

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

### Verbose mode (`--verbose`)

```
OK: floor_plan_A.png -> /export/floor_plan_A.png
OK: floor_plan_B.png -> /export/floor_plan_B.png
```

### No-PNG-files message (new, always printed to stdout)

```
No PNG files found in /import.
```

### Batch summary (always printed to stdout at end of batch, only when ≥1 file found)

```
Processed: 48 | Skipped: 2 | Failed: 0
```

Single-file mode prints no summary.

---

## Standard Error (stderr)

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

### Write failure (per file)

```
ERROR: floor_plan_E.png failed — <descriptive message>.
```

### Input path does not exist (fatal)

```
ERROR: /import does not exist.
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All files processed (some may have been skipped or failed with warnings) |
| `0` | No PNG files found in input directory (informative message printed) |
| `1` | Fatal error: resolved INPUT_PATH does not exist or is not a valid PNG/directory |

---

## Constraints

- The tool MUST NOT modify, rename, or delete any input file.
- The tool MUST create the output directory if it does not exist.
- The tool MUST process all files in a batch even if individual files fail.
- The tool exits with code `0` when skips or write failures occur; they are not fatal.
- Only top-level PNG files are processed — subdirectories are not scanned recursively.
