# WARPSimLab Coding Standards

These standards apply to all Python code written or modified in WARPSimLab, including production code, tests, examples, and maintenance changes.

**Compliance is mandatory.** These are project requirements, not stylistic suggestions.

## 1. General Principles

- Favor straightforward, readable, maintainable Python.
- Keep code compact and information-dense.
- Prefer simple implementations over clever abstractions.
- Avoid unnecessary complexity, indirection, and helper functions.
- Make only changes relevant to the assigned task.
- Preserve existing behavior unless explicitly authorized to change it.
- Use only ASCII characters in Python source code.

## 2. Mandatory Code Formatting

WARPSimLab strongly favors compact, information-dense Python.

**Treat this as a hard requirement.**

- Keep expressions, function calls, assertions, argument lists, and dictionary entries on **one line** whenever reasonably readable.
- Target approximately **100–120 characters per line**. Exceeding that somewhat is preferable to gratuitously expanding straightforward code vertically.
- Do not use Black-style vertical formatting merely because an expression contains several arguments.
- Do not wrap straightforward pytest assertions in parentheses across multiple lines.
- Do not expand compact calls or expressions into numerous lines unless the one-line form would genuinely be difficult to understand.
- Avoid excessive blank lines within functions.
- Optimize for seeing the algorithm and control flow within approximately one screen of code.
- Do not follow poorly formatted surrounding code. These standards take precedence over existing formatting conventions.
- Do not reformat unrelated code.

### Preferred formatting

```python
assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(0.0)
```

### Unacceptable formatting

```python
assert (
    results["breakdown_by_class"]["withdrawal"][0, 1]
    == pytest.approx(0.0)
)
```

Another preferred example:

```python
simulation_results = run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)
```

Avoid expanding the call into separate lines for every argument unless readability genuinely requires it.

## 3. Control Flow

Compact formatting must not obscure control flow.

- Do not write `for` loops on one line.
- Do not write `if/else` statements or conditional branches on one line.
- Use ordinary, explicit control structures when they improve clarity.
- Avoid deeply nested logic when a straightforward alternative exists.
- Use simple comprehensions when they are clear. Do not use complicated comprehensions to compress multi-step logic.

### Preferred

```python
if calculate_taxes:
    taxes = calculate_income_taxes(income)
else:
    taxes = 0.0

for year in range(years_to_simulate):
    portfolio_balance += annual_return[year]
```

### Unacceptable

```python
taxes = calculate_income_taxes(income) if calculate_taxes else 0.0

for year in range(years_to_simulate): portfolio_balance += annual_return[year]
```

## 4. Functions and Abstractions

- Keep functions focused on clearly defined responsibilities.
- Do not create trivial helper functions solely to reduce line count or avoid a straightforward expression.
- Do not introduce classes, wrappers, properties, inheritance, or design patterns without a concrete need.
- Avoid unnecessary intermediate variables.
- Use intermediate variables when they clarify complex expressions or document important financial concepts.
- Prefer explicit code over unnecessarily clever Python idioms.
- Avoid introducing additional architectural layers without authorization.

## 5. Code Changes

- Keep changes focused, limited in scope, and testable.
- Do not perform unrelated refactoring or cleanup.
- Do not change financial algorithms or numerical behavior unless explicitly authorized.
- Preserve public interfaces and existing behavior unless the assignment specifies otherwise.
- Follow the approved architecture when working on architectural changes.
- Report architectural ambiguities rather than independently inventing solutions.
- Do not introduce temporary compatibility mechanisms or additional abstractions without justification.

## 6. Comments and Documentation

- Use comments to explain non-obvious behavior, financial assumptions, dependencies, and important implementation decisions.
- Avoid comments that merely restate what the code obviously does.
- Keep comments and docstrings concise.
- Preserve meaningful existing documentation.
- Do not add large explanatory comment blocks around straightforward code.

## 7. Testing Code

The same formatting standards apply to pytest code.

- Prefer compact, direct assertions.
- Do not vertically expand straightforward assertions or fixture calls.
- Keep tests readable and focused on the behavior being verified.
- Avoid unnecessary helpers and abstractions in tests.
- Do not weaken assertions merely to make failing tests pass.
- Do not change expected numerical results without identifying and justifying the reason.

## 8. Mandatory Compliance Review

Before completing any coding assignment:

1. Review all added and modified code for compliance with these standards.
2. Specifically inspect for unnecessary vertical expansion.
3. Compact expressions, calls, assertions, and argument lists wherever reasonably readable.
4. Verify that control flow remains clear and explicit.
5. Remove unnecessary intermediate variables, helpers, and abstractions introduced by the changes.
6. Verify that unrelated code has not been reformatted.
7. Run any applicable automated coding-standard checks.
8. Correct identified violations before declaring the task complete.

Passing pytest does **not** establish compliance with coding standards.

If a requirement cannot reasonably be satisfied, report the exception and explain why.

## 9. Authority

These standards apply regardless of how existing code is formatted.

Existing source files may contain legacy formatting that does not meet these requirements. Do not reproduce those patterns simply for consistency.

When modifying code, newly written or changed code must comply with this document.

Do not reformat unrelated legacy code without explicit authorization.

**The objective is compact, readable, maintainable Python that exposes the algorithm and control flow without unnecessary vertical expansion.**