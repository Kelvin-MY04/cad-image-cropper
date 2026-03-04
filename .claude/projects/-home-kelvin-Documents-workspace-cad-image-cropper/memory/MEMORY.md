# CAD Image Cropper — Project Memory

## Project Overview
- **Name**: cad-image-cropper
- **Purpose**: Image cropping tool for floor plan images
- **Language**: Python (>= 3.10)
- **Constitution**: `.specify/memory/constitution.md` — v1.0.0, ratified 2026-03-04

## Constitution Summary (v1.0.0)
Six non-negotiable core principles:
1. Object-Oriented Design — all code in classes, encapsulation enforced
2. SOLID Principles — strictly enforced (SRP, OCP, LSP, ISP, DIP)
3. DRY — no duplication; extract shared logic
4. Clean Code & Naming — snake_case/PascalCase/UPPER_SNAKE_CASE; no comments
5. Single Responsibility per Method — one operation per method, ≤20 lines, CQS
6. Error Handling — try/except on all I/O, custom exceptions from CadImageCropperError

## Quality Gates
- `flake8` and `mypy --strict` must pass with zero errors
- Type annotations required on all signatures
- Cyclomatic complexity ≤ 5 per method
- All custom exceptions inherit from `CadImageCropperError`

## User Preferences
- No comments in code
- Strict Python naming conventions
- Error handling in every method
- Descriptive variable/method names
