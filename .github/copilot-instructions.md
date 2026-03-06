# Django SSTQ (Super Simple Task Queue)

## Project Overview

**SSTQ** is a Django task framework serving as an alternative to Django's built-in tasks framework, while embracing its patterns and conventions. It provides task scheduling, monitoring, and Django admin integration with planned async execution support.


## Development Philosophy

### Test-Driven Development (TDD)
- **Always write tests first** before implementing features
- Test critical paths pragmatically (not obsessive 100% coverage)
- Use Django's `TestCase` class
- Tests live in `sstq/tests/` and follow `test_*.py` naming

### Code Style & Conventions
- Follow **Django team's coding style** (PEP 8 + Django extensions)
- Use **modern Python type hints** (PEP 695 generics: `Callable[P, R]`, `Optional[...]`)
- Prefer **explicit generic syntax** over `typing.Generic`
- Use `@overload` decorators for type-safe function signatures
- Keep functions focused and readable
- Write comprehensive docstrings in numpydoc style