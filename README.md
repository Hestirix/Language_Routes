# Language Routes

**Developers:** Dennis & Neylan  
**Course:** Engineering in Python

Language Routes is a university Python programming project for exploring
historical connections between Indo-European languages. It uses recorded
linguistic evidence from the Indo-European Cognate Relationships (IE-CoR)
dataset to support learning about data processing, relational databases,
search algorithms, validation, and visualization.

## Development status

**Current stage: Stage 1B — SQLite Database Design.**

Stage 0 dataset inspection is complete. The repository now contains development
instructions, environment setup documentation, Git exclusions, and a minimal
project dependency file. A local Python 3.14.7 virtual environment has been
created for development, with pandas 3.1.1 and pytest 9.2.0 installed locally.

Stage 1B adds a nine-table SQLite schema, documented connection utilities, empty
database initialization, and automated database tests. All eight linguistic source
tables retain every original CSV column; a separate table is reserved for future
import history. See [the database design](docs/database_design.md).

**The application is not functional yet.** No linguistic data has been imported.
There is no dataset importer, word search, Streamlit interface, or map. Each later
development stage requires explicit approval.

## Planned functionality

- Search recorded word forms, with language filtering.
- Explore forms assigned to the same cognate set.
- Display supplied ancestral forms, their language labels, and supporting evidence
  where available. Not every set has a Proto-Indo-European reconstruction.
- Distinguish cognates, shared concepts, and borrowing relationships.
- Visualize language reference locations and dataset relationships geographically.

Shared meaning alone does not establish a historical relationship. The application
will use dataset assignments rather than invented or hardcoded word connections.
Language locations will not be presented as proof of migration routes.

## Technology stack

| Technology | Intended role | Stage 1A dependency status |
| --- | --- | --- |
| Python 3 | Core application logic | Python 3.14.7 verified locally |
| pandas | Dataset loading and processing | Version 3.1.1 installed in `.venv` |
| SQLite through `sqlite3` | Relational storage and queries | Included with Python; no pip package needed |
| Streamlit | Interactive interface | Planned for Stage 3; not installed by this setup |
| pytest | Automated tests | Version 9.2.0 installed in `.venv` |
| Plotly or a suitable mapping library | Geographic visualization | Selection and installation deferred to Stage 4 |

## Dataset and attribution

The original CLDF snapshot is stored in [`data/raw/cldf/`](data/raw/cldf/).
It contains 25,731 word forms, 160 language varieties, 170 concepts, 25,741 cognate
assignments, 4,981 cognate sets, 1,036 loan records, 91 contributors, and 27 clades.
The snapshot also includes metadata, a bibliography, and generation reports.

Citation supplied by the dataset:

> Heggarty, Paul & Anderson, Cormac & Scarborough, Matthew 2024.
> Indo-European Cognate Relationships database (IE-CoR version 1.1).
> Leipzig: Max Planck Institute for Evolutionary Anthropology.

- Dataset website: [IE-CoR](https://iecor.clld.org).
- Source repository: [lexibank/iecor](https://github.com/lexibank/iecor).
- Dataset description: [Anderson et al. (2025)](https://doi.org/10.1038/s41597-025-05445-3).
- Dataset license: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Local provenance: [`cldf-metadata.json`](data/raw/cldf/cldf-metadata.json).

The metadata's citation names version 1.1, while its source repository provenance
records `v1.2-2-g978730b`. Both are retained here as supplied; they should not be
silently collapsed into a single version claim.

The CLDF source files are unchanged by Language Routes. Preserve their attribution,
license information, bibliography, original identifiers, and Unicode text. The
dataset license is separate from any future license chosen for our application.

The complete supplied dataset occupies 8,288,431 bytes (about 7.9 MiB), with a
largest file of about 3.2 MiB. It is intentionally eligible for normal Git tracking
so collaborators can use the same snapshot. Generated databases and environments
are excluded. No dataset files have been committed or pushed by the setup process.

## Windows PowerShell setup

Open PowerShell in the project directory. The local environment was created with
64-bit Python 3.14.7. Check that Python is available:

```powershell
py --version
python --version
where.exe python
```

On a fresh checkout, create the environment once and install project dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `.venv` already exists from Stage 1A, use it directly; recreation is unnecessary.
A virtual environment is a project-specific Python environment with its own
installed packages. It keeps this project's dependencies separate from other
projects and the base Python installation. It is generated locally and should
not be committed. See the [Python venv documentation](https://docs.python.org/3/library/venv.html).

The commands here use the environment's Python explicitly, so activation is not
required and no PowerShell execution-policy changes are needed. Optionally, if
your existing policy permits it, run `.\.venv\Scripts\Activate.ps1`; use
`deactivate` when finished.

Verify the interpreter, environment isolation, dependencies, and SQLite support:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable); print('Virtual environment:', sys.prefix != sys.base_prefix)"
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import pandas, pytest, sqlite3; print('pandas:', pandas.__version__); print('pytest:', pytest.__version__); print('SQLite:', sqlite3.sqlite_version)"
```

These commands check package imports and versions; they do not create a database
or import the linguistic dataset.

## Initialize the database and run tests

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m language_routes.database
.\.venv\Scripts\python.exe -m pytest -q
```

Initialization creates `data/processed/language_routes.sqlite3` with nine empty
tables on a fresh run. Repeating it preserves existing rows; it does not import,
clear, or migrate data. An optional `--database .\data\processed\custom.sqlite3`
argument selects another output path. Paths inside `data/raw` are rejected.
The default path and schema lookup do not depend on the shell's working directory.
Run the module command from the project root so Python can find the package.

Tests use temporary databases and synthetic placeholders. The schema uses STRICT
tables, requiring SQLite 3.37+, and the utilities require Python 3.12+; both are
supported by the project's verified environment. See
[database_design.md](docs/database_design.md) for constraints and transaction details.

### Python launcher troubleshooting

During inspection, Windows aliases failed inside the restricted execution sandbox
but `py` and `python` both worked outside it. The verified base interpreter is:

```text
C:\Users\Garfield\AppData\Local\Python\pythoncore-3.14-64\python.exe
```

On this computer, that interpreter can create `.venv` directly if a launcher is
unavailable:

```powershell
& 'C:\Users\Garfield\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m venv .venv
```

This path is computer-specific. Other contributors should use their own working
Python installation. No Python installation, PATH changes, or system-wide package
installation was needed for this setup.

Use only the **project-level** `requirements.txt` for this environment. The file
at `data/raw/cldf/requirements.txt` documents the upstream dataset-generation
environment and is not the application's dependency list.

The two direct dependencies are pinned to the versions installed during Stage 1A.
Pip also installs their required supporting packages. This minimal requirements
file is not a complete lockfile for every supporting dependency.

## Git setup status

At the beginning of Stage 1B, the project foundation was committed on `main`,
tracking `origin/main`, with a clean working tree. The configured fetch and push
remote is `https://github.com/Hestirix/Language_Routes.git`.

The remote name matches this project, but the developers should confirm that
`Hestirix/Language_Routes` is the intended GitHub destination before publishing.
No remote configuration was changed, and no commit or push was performed.

Inspect the configuration without changing it:

```powershell
git status --short --branch
git remote -v
git ls-remote origin
```

## Development instructions

Read [`AGENTS.md`](AGENTS.md) before making changes. Keep Python modules readable,
document their purpose and important functions, test important functionality, and
work only on the explicitly approved stage. Dataset importing, search, interface
implementation, and mapping remain later work.
