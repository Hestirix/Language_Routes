# Language Routes — Development Instructions

Language Routes is an academic project developed by **Dennis & Neylan** for
**Engineering in Python**. It explores historical relationships between
Indo-European languages using the IE-CoR CLDF dataset.

## Stage boundaries

- Work only on the development stage explicitly approved by the user.
- The currently approved stage is **Stage 1B: SQLite Database Design**.
- Stage 1B permits the schema, connection utilities, empty database initialization,
  automated tests using temporary databases, and supporting documentation.
- Do not import linguistic data, implement search, build the Streamlit interface,
  or begin mapping during Stage 1B. Synthetic test records are permitted only in
  temporary test databases; they are not linguistic evidence.
- Stop after completing the approved stage. Never automatically implement future
  stages. Update this stage note when the user explicitly approves a later stage.
- Do not create commits, push changes, or change Git remotes without authorization.

## Python documentation and learning

- Every project Python file, including tests, must begin with a short module
  docstring identifying Language Routes, Dennis & Neylan, Engineering in Python,
  and the purpose of that file. Third-party files inside `.venv` are excluded.
- Important functions need concise docstrings explaining their purpose, inputs,
  and outputs, including significant exceptions when relevant.
- Add brief educational comments for important or unfamiliar logic, especially
  SQL, data cleaning, validation, search, and geographic processing.
- Avoid comments that merely repeat obvious code.
- Keep code readable, modular, and appropriate for students learning Python.
- Explain significant design decisions and Python concepts in straightforward
  English so both developers can understand and present the work.
- Include the project, developer, and course attribution in relevant project and
  final documentation. Preserve the dataset's separate academic attribution.

## Architecture and dependencies

- Keep data loading, validation, database access, search, geography, and interface
  responsibilities separate as their stages are approved.
- Use Python 3, pandas, SQLite through the standard-library `sqlite3` module,
  Streamlit, and pytest. Add mapping dependencies only when needed.
- Do not add complex frameworks or unnecessary dependencies. Explain additions.
- Use the project-local `.venv`; do not install project packages system-wide.
- Project dependency files are separate from `data/raw/cldf/requirements.txt`,
  which describes the dataset-generation environment and must remain unchanged.

## Data integrity and historical accuracy

- Never modify the original files under `data/raw/cldf/`.
- Inspect actual CSV structures and CLDF metadata before assuming field meanings.
- Preserve original dataset identifiers and Unicode text. Keep any derived search
  normalization separate from the original values.
- Do not invent or hardcode word translations, reconstructions, or historical
  cognate relationships. Obtain relationships from the dataset.
- Distinguish shared concepts from cognacy and borrowing from inheritance.
- Do not assume every cognate set has a Proto-Indo-European root. Preserve root
  language labels, evidence, missing values, and uncertainty.
- Keep calculated root fields separate unless their interpretation is verified.
- Flag suspected dataset errors; never silently correct source values.
- Support multiple cognate memberships per form. Do not treat missing booleans
  as false or language reference coordinates as proven migration routes.
- Preserve citation and license information when documenting or distributing data.

## Tests and validation

- Write automated tests for important implemented functionality using pytest.
- Validate identifiers, references, required fields, record counts, conversions,
  and Unicode preservation when data importing is approved.
- Use temporary databases and small fixtures in tests. Never mutate the raw data.
- Use parameterized SQL, explicit transactions, and foreign-key enforcement when
  database implementation is approved.
- Run checks appropriate to the current change and report results honestly.
- Do not add placeholder application code or tests merely to populate folders.
