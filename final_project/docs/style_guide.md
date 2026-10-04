# Project Style Guide

This project should read like careful work by a researcher who understands the analysis. The reference notebook at `/home/luis-enrique/Desktop/Machine_learning/1. Model_sample.ipynb` is used only for its human workflow style: clear sections, direct code, short Markdown, and a natural progression from preparation to evaluation.

Do not copy code, models, features, or scope from the reference notebook.

## General style

Keep the project small, explicit, and finishable. Prefer clear names and direct logic over compact tricks or artificial architecture. Add files only when they have a real responsibility.

Before finishing a file, check whether a person could read it from top to bottom without getting lost. Remove anything that looks like it is trying to impress rather than solve the project.

## Code

Prioritize clarity over cleverness. Avoid hard-to-read one-liners, unnecessary helpers, classes when a function is enough, and patterns that do not make the analysis clearer.

Use explicit variable names. Keep functions small, but do not split code into extra modules just for appearance.

## Comments and docstrings

Comment decisions, assumptions, and scientific risks. Do not comment every line.

Docstrings should be brief and natural. Include inputs, outputs, units, and assumptions when those details matter.

## Markdown

The notebook is the narrative layer. Before important blocks, use short Markdown that explains why the step is needed. After figures or results, include a brief interpretation only when real results exist.

Never invent results.

## SQL

SQL should show the cohort and feature construction from top to bottom. Use readable CTE names, few nesting levels, and comments only for important clinical or temporal logic.

Every feature must respect the leakage rule:

```text
feature_timestamp <= index_date
```

## Tests

Tests should be small and focused. Each test should check one main idea with descriptive names and simple inputs.

For leakage and temporal logic, comments should make clear what scientific error the test prevents.

## Project layers

Keep responsibilities separate:

- `notebooks/` tells the analysis story.
- `sql/` defines cohorts and features.
- `src/` contains reusable logic.
- `tests/` validates behavior.
- `README.md` explains how to reproduce the work.

Do not duplicate logic between layers.
