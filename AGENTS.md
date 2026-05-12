# Agent Guidelines for Vintage Hunter

## Project Facts
- Vintage Hunter is a Django application for cataloging and auctioning vintage musical instruments.
- Main Django project directory: `vintage_hunter/`.
- Apps: `auction`, `catalog`, `commons`, `payments`, `users`.
- Stack: Python 3.x, Django 6.x, PostgreSQL with `pgvector`, Redis, Celery, Django templates, Bootstrap 5.3.0, vanilla CSS, vanilla JavaScript.
- Verify version-sensitive assumptions from local files or commands. The local venv currently reports Django `6.0.3`.
- Locale setup includes English and Ukrainian. Keep Ukrainian translations current in `vintage_hunter/locale/uk/LC_MESSAGES/django.po`.

## Workflow Rules
- Do not install dependencies without explicit user approval and a clear technical justification.
- Use the project virtual environment for Python commands. Prefer `.venv/`; if no venv exists, ask before running Python tooling.
- Use `docker-compose.yaml` for local PostgreSQL and Redis.
- After model changes, check whether migrations are required.
- Ask for approval only when a change introduces a meaningful product, schema, architecture, dependency, or cross-module design decision. Do not stop for routine edits just because multiple files are touched.
- Do not invent production details such as secrets, endpoints, schemas, configs, versions, or test results.

## Django Conventions
- Prefer simple, idiomatic Django and Python over custom abstractions.
- Prefer function-based views with explicit HTTP method decorators.
- Use `django.contrib.messages` for user feedback.
- Put reusable queryset logic in managers or querysets.
- Use type hints where they improve clarity.
- Avoid comments unless they explain non-obvious behavior.
- Prefer single quotes for Python strings unless double quotes avoid escaping or match existing surrounding style.
- Use lazy model references like `'app.Model'` or `'self'` for circular model relationships before considering dynamic field attachment.

## Models And Queries
- New project models should inherit from `commons.models.Base` unless there is a specific reason not to.
- Use `models.PROTECT` for sensitive foreign keys such as `Category`, `Brand`, and purchased instruments.
- Prevent N+1 queries in list views that render related data.
- Use `select_related` for single-valued relations and `prefetch_related` or `Prefetch` for multi-valued relations.
- Prefer database aggregation and annotations over Python loops through querysets.
- Use `only`, `defer`, `values`, or `values_list` when model instances or large fields are unnecessary.

## Internationalization
- Wrap user-facing Python strings with `gettext` or `gettext_lazy`.
- Use `{% trans %}` or `{% blocktrans %}` for user-facing template strings.
- When adding or changing user-facing strings, update the Ukrainian `.po` file.
- Validate translation updates with Django's standard `makemessages` and `compilemessages` workflow when possible.

## Frontend
- Preserve the existing Bootstrap 5.3.0 and Inter-based visual system.
- Use existing CSS variables from `base.html`: `--vt-dark`, `--vt-gold`, and `--vt-gray`.
- Use Bootstrap Icons only.
- Use Bootstrap toasts for success and error feedback.
- Use Bootstrap modals for complex interactions that should not require a page reload.
- Keep views mobile-first and responsive with Bootstrap grid utilities.
- Put app-specific CSS in `static/<app>/css/` and app-specific JavaScript in `static/<app>/js/`.
- App templates belong under `<app>/templates/`; shared/global templates may live under `vintage_hunter/templates/`.

## AI And Search
- Use `pgvector.django.VectorField` for embeddings.
- Use `HnswIndex` for vector indexes.
- Run long-running embedding or search maintenance work through Celery.
