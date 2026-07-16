# Dependency pitfalls

Use this reference to explain the doctor's findings without overstating them.
The script identifies focused manifest problems. It does not replace a resolver
or vulnerability database.

## Standard-library shadowing

A requirement can have the same name as a Python standard-library module. Pip
then places a separately maintained distribution on the import path, where it
can shadow or conflict with the runtime's own module.

Two concrete examples:

```text
pathlib==1.0.1
dataclasses
```

`pathlib` has shipped with Python since 3.4. The old PyPI backport should not be
installed on modern Python. `dataclasses` has shipped with Python since 3.7; its
backport exists for Python 3.6. On supported modern runtimes, remove these lines
and import the standard-library modules directly.

When a project intentionally supports an older Python release, use an explicit
environment marker instead of installing the backport everywhere. Confirm the
project's supported Python range before editing.

## Abandoned and obsolete backports

Backports such as `typing`, `enum34`, `futures`, and `singledispatch` solved real
gaps in older Python versions. They become liabilities when pinned for runtimes
that already provide the feature. They may be unmaintained, constrain other
packages, or expose an implementation that no longer matches the standard
library.

The right fix is usually removal. If an old runtime remains supported, add a
Python-version marker and test both sides of the marker.

## Yanked releases

PyPI can mark release files as yanked when a version is broken, unsafe, or
published by mistake. Yanked files remain available so existing exact pins can
still resolve, which means an old manifest may keep installing a bad release.

The doctor's online check is deliberately opt-in. It queries only exact pins
and reports a release as yanked only when every file for that version is marked
yanked. A yank is not automatically a CVE, and a CVE does not require a yank.
Use a dedicated security scanner for vulnerability coverage.

## Pin hygiene

A bare dependency such as `requests` can resolve differently on two machines
or two dates. Before creating an exact pin:

1. Inspect the version installed in the project's working environment.
2. Confirm that version is intentional and supported.
3. Run the project's tests with the proposed pin.
4. Preserve environment markers and extras from the original requirement.

Do not invent a version from memory. Lockfiles and constraint files may already
be the project's chosen source of reproducibility, so inspect them before
changing a manifest.

## Duplicates and conflicts

Identical repeated lines create two places to maintain one decision. Compatible
ranges on separate lines can usually be combined. Different exact pins, such as
`urllib3==1.26.18` and `urllib3==2.2.2`, cannot both be satisfied and require a
deliberate version choice.

Before resolving a conflict, inspect which direct dependency introduced each
constraint. Choosing the newest number without checking dependents can turn a
clear resolver failure into a runtime regression.
