<!--
SYNC IMPACT REPORT
==================
Version change: [unversioned template] → 1.0.0
Modified principles: N/A — initial constitution, all sections are new.
Added sections:
  - Core Principles I through VI
  - Code Quality Standards
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ Constitution Check gates derive from this document at runtime; no structural change required.
  - .specify/templates/spec-template.md ✅ No mandatory section conflicts introduced.
  - .specify/templates/tasks-template.md ✅ Error handling infrastructure task (T008) already present in foundational phase; aligns with Principle VI.
Follow-up TODOs: None — all placeholders resolved.
-->

# CAD Image Cropper Constitution

## Core Principles

### I. Object-Oriented Design (NON-NEGOTIABLE)

All production code MUST be structured using object-oriented design. Every logical concept
in the domain is represented as a class with clearly scoped responsibilities. Bare procedural
scripts or top-level logic outside of designated entry-point modules are prohibited.

Classes MUST use encapsulation to hide internal state, expose behavior through a minimal
public interface, and model domain concepts faithfully. Inheritance MUST only be used where a
genuine is-a relationship exists; composition is preferred otherwise.

- Every module MUST expose behavior through classes, not standalone functions.
- Instance attributes MUST be initialized exclusively in `__init__`.
- Internal implementation details MUST be prefixed with a single underscore (`_`).

### II. SOLID Principles (NON-NEGOTIABLE)

All classes and modules MUST conform to the five SOLID principles without exception.

- **S — Single Responsibility**: Each class and each method MUST have exactly one reason to
  change. A class responsible for cropping images MUST NOT also manage file persistence or
  logging configuration.
- **O — Open/Closed**: Classes MUST be open for extension through inheritance or composition
  and closed for modification. New behavior MUST be added by extending existing abstractions,
  not by altering tested code.
- **L — Liskov Substitution**: Every subclass MUST be a valid substitute for its base class.
  Overriding a method MUST not weaken preconditions or strengthen postconditions.
- **I — Interface Segregation**: No class MUST be forced to implement methods irrelevant to
  its role. Abstract base classes MUST be narrow and role-specific.
- **D — Dependency Inversion**: High-level modules MUST depend on abstractions, not concrete
  implementations. Dependencies MUST be injected at construction time, never instantiated
  inside a class body.

### III. DRY — Don't Repeat Yourself (NON-NEGOTIABLE)

Every piece of knowledge MUST have a single, authoritative representation in the codebase.
Duplicated logic is treated as a defect and MUST be resolved before a feature is considered
complete.

- Shared behavior MUST be extracted into a reusable method, class, or utility module.
- Configuration values and domain constants MUST be defined once and referenced everywhere.
- Any pattern repeated more than once MUST be refactored into a named abstraction.

### IV. Clean Code and Naming (NON-NEGOTIABLE)

Code MUST be self-documenting through precise, intention-revealing names. Comments of any
kind — inline, block, or docstring implementation notes — are prohibited. When a comment
feels necessary, the code MUST be refactored until the intent is clear from the names alone.

Python naming conventions MUST be followed without exception:

- `snake_case` for variables, functions, and methods.
- `PascalCase` for class names.
- `UPPER_SNAKE_CASE` for module-level constants.
- Private members MUST use a single leading underscore prefix.

Names MUST convey intent, not mechanism. `calculate_bounding_box` is acceptable;
`calc`, `do_thing`, or `process` are not. Magic numbers and inline string literals MUST
be replaced with named constants.

### V. Single Responsibility per Method (NON-NEGOTIABLE)

Every method MUST perform exactly one operation. A method that both validates input and
transforms data violates this principle and MUST be decomposed.

- Methods exceeding 20 lines of code are a signal of violation and MUST be refactored.
- Method names MUST follow an action-verb + object-noun pattern: `crop_image`, `load_config`,
  `validate_input_path`.
- Methods MUST obey Command-Query Separation: a method either returns a value (query) or
  changes state (command) — never both.

### VI. Error Handling (NON-NEGOTIABLE)

Every method MUST handle errors explicitly. Uncaught exceptions propagating to the caller
without context are defects.

- All I/O operations — file access, external process calls, network requests — MUST be
  wrapped in a `try/except` block.
- Domain-specific failures MUST use custom exception classes that inherit from a single
  project-level base exception.
- Silent suppression of exceptions (`except: pass` or `except Exception: pass`) is
  prohibited.
- Error messages MUST be descriptive and MUST include the source context (method name,
  invalid value, or file path) to aid debugging.
- Raised exceptions MUST use the most specific exception type available; bare `Exception`
  MUST NOT be raised directly.

## Code Quality Standards

These standards define the minimum measurable quality bar for all production code.

- Python version MUST be >= 3.10; type annotations MUST appear on all method and function
  signatures.
- `flake8` and `mypy --strict` MUST pass with zero errors on every commit.
- Every class MUST have at least one corresponding unit test in `tests/unit/`.
- Cyclomatic complexity per method MUST not exceed 5; the extract-method refactoring
  technique MUST be applied to reduce complexity above this threshold.
- All custom exception classes MUST inherit from the project-level `CadImageCropperError`
  base exception.

## Development Workflow

The following workflow MUST be followed for every feature implementation:

1. Define the class hierarchy and abstract interfaces before writing any implementation.
2. Write unit tests describing the intended behavior of each class before implementing it.
3. Implement the smallest class that makes the tests pass, then refactor for quality.
4. Run `flake8` and `mypy` before marking any task complete; zero violations MUST be present.
5. Submit code for review only after all tests pass and all quality gates are green.

## Governance

This constitution supersedes all other coding conventions and verbal agreements. Any deviation
requires a written amendment that MUST include the principle being modified, the rationale for
the change, and an approved migration plan for non-conforming existing code.

- All pull requests MUST include a Constitution Check section confirming compliance with
  Principles I through VI.
- Complexity or naming violations temporarily granted an exception MUST be documented in the
  plan's Complexity Tracking table with explicit justification.
- Amendments MUST increment the version number according to the following semantic versioning
  rules:
  - MAJOR: Removal or fundamental redefinition of any Core Principle.
  - MINOR: Addition of a new principle or a new mandatory section.
  - PATCH: Wording clarification, typo correction, or non-semantic refinement.
- A compliance review MUST be conducted at the start of every sprint by the tech lead or a
  nominated reviewer.

**Version**: 1.0.0 | **Ratified**: 2026-03-04 | **Last Amended**: 2026-03-04
