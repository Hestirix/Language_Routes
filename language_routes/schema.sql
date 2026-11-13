-- Language Routes — Dennis & Neylan, Engineering in Python.
-- Preserve the CLDF column names. No source records are inserted by this schema.
-- STRICT tables reject values that cannot be converted to the declared type.
-- Optional fields allow NULL; booleans use 0/1 without treating unknown as false.

CREATE TABLE IF NOT EXISTS languages (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    Name TEXT,
    Glottocode TEXT,
    Glottolog_Name TEXT,
    ISO639P3code TEXT,
    Macroarea TEXT,
    Latitude REAL CHECK (Latitude BETWEEN -90 AND 90),
    Longitude REAL CHECK (Longitude BETWEEN -180 AND 180),
    Family TEXT,
    Author_ID TEXT, -- Original semicolon-separated contributor IDs, not one FK.
    Description TEXT,
    Clade TEXT, -- A list of classification labels, not clades.ID values.
    Color TEXT,
    Variety TEXT,
    clade_name TEXT,
    ascii_name TEXT,
    loc_justification TEXT,
    historical INTEGER CHECK (historical IN (0, 1)),
    distribution TEXT,
    logNormalMean INTEGER,
    logNormalOffset INTEGER,
    logNormalStDev REAL,
    normalMean INTEGER,
    normalStDev INTEGER,
    fossil INTEGER CHECK (fossil IN (0, 1)),
    sort_order INTEGER
) STRICT;

CREATE TABLE IF NOT EXISTS parameters (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    Name TEXT,
    Concepticon_ID TEXT,
    Concepticon_Gloss TEXT,
    Concepticon_Definition TEXT,
    Description_md TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS authors (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    Last_Name TEXT,
    First_Name TEXT,
    URL TEXT,
    Photo TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS clades (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    level0_name TEXT,
    level1_name TEXT,
    level2_name TEXT,
    level3_name TEXT,
    clade_name TEXT,
    short_name TEXT,
    color TEXT,
    clade_level0 INTEGER,
    clade_level1 INTEGER,
    clade_level2 INTEGER,
    clade_level3 INTEGER,
    taxonsetName TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS cognatesets (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    Description TEXT,
    Source TEXT,
    Root_Form TEXT,
    Root_Gloss TEXT,
    Root_Language TEXT, -- Free text: not necessarily a language in languages.csv.
    Comment TEXT,
    Justification TEXT,
    revised_by TEXT,
    Ideophonic INTEGER CHECK (Ideophonic IN (0, 1)),
    Dyen TEXT,
    -- Keep identifier-like fields as text; uncertain semantics are not FKs.
    proposedAsCognateTo_pk TEXT,
    proposedAsCognateToScale INTEGER,
    parallelDerivation INTEGER CHECK (parallelDerivation IN (0, 1)),
    Root_Form_calc TEXT,
    Root_Language_calc TEXT,
    supersetid TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS forms (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    Local_ID TEXT,
    Language_ID TEXT NOT NULL REFERENCES languages(ID),
    Parameter_ID TEXT NOT NULL REFERENCES parameters(ID),
    Value TEXT NOT NULL CHECK (length(trim(Value)) > 0),
    Form TEXT NOT NULL CHECK (length(trim(Form)) > 0),
    Segments TEXT,
    Comment TEXT,
    Source TEXT,
    Cognacy TEXT,
    Loan INTEGER CHECK (Loan IN (0, 1)),
    Gloss TEXT,
    phon_form TEXT,
    Phonemic TEXT,
    Phonemic_Segments TEXT,
    native_script TEXT,
    url TEXT
) STRICT;

-- Separate assignments allow one form to belong to several cognate sets.
-- Only the original assignment ID is unique: do not constrain Form_ID alone.
CREATE TABLE IF NOT EXISTS cognates (
    ID TEXT PRIMARY KEY NOT NULL CHECK (length(trim(ID)) > 0),
    Form_ID TEXT NOT NULL REFERENCES forms(ID),
    Form TEXT, -- Preserve this source field even though this snapshot leaves it empty.
    Cognateset_ID TEXT NOT NULL REFERENCES cognatesets(ID),
    Doubt INTEGER CHECK (Doubt IN (0, 1)),
    Cognate_Detection_Method TEXT DEFAULT 'expert',
    Source TEXT,
    Alignment TEXT,
    Alignment_Method TEXT,
    Alignment_Source TEXT
) STRICT;

-- The target is the source-declared primary key. A donor set may be unknown.
-- These two references are supported by the inspected loan records, although
-- the CLDF metadata does not explicitly declare them as foreign keys.
CREATE TABLE IF NOT EXISTS loans (
    Cognateset_ID TEXT PRIMARY KEY NOT NULL
        CHECK (length(trim(Cognateset_ID)) > 0) REFERENCES cognatesets(ID),
    SourceCognateset_ID TEXT REFERENCES cognatesets(ID),
    Comment TEXT,
    Source_languoid TEXT,
    Source_form TEXT,
    Parallel_loan_event INTEGER CHECK (Parallel_loan_event IN (0, 1))
) STRICT;

-- Application bookkeeping, not invented linguistic fields. Stage 1C will write
-- one record per successful import, in the same transaction as the imported data.
CREATE TABLE IF NOT EXISTS dataset_imports (
    import_id INTEGER PRIMARY KEY,
    imported_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    dataset_title TEXT NOT NULL,
    bibliographic_citation TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_revision TEXT,
    license_url TEXT NOT NULL,
    metadata_sha256 TEXT NOT NULL CHECK (
        length(metadata_sha256) = 64
        AND metadata_sha256 NOT GLOB '*[^0-9a-fA-F]*'
    ),
    notes TEXT
) STRICT;

-- Index the join directions used by future search and relationship queries.
CREATE INDEX IF NOT EXISTS idx_forms_language ON forms(Language_ID);
CREATE INDEX IF NOT EXISTS idx_forms_parameter ON forms(Parameter_ID);
CREATE INDEX IF NOT EXISTS idx_cognates_form ON cognates(Form_ID);
CREATE INDEX IF NOT EXISTS idx_cognates_set ON cognates(Cognateset_ID);
CREATE INDEX IF NOT EXISTS idx_loans_source_set ON loans(SourceCognateset_ID);
