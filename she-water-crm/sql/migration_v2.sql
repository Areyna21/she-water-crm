-- ============================================================
-- SHE Water CRM — Migration v2
-- Adds fields identified from Access system review
-- Safe to run on existing schema — all ALTER TABLE additions
-- ============================================================

-- ============================================================
-- 1. STATUS SYSTEM — add secondary status and status step
-- ============================================================

ALTER TABLE program_enrollment
    ADD COLUMN IF NOT EXISTS status_secondary  VARCHAR(100),
    ADD COLUMN IF NOT EXISTS status_step       VARCHAR(100);

-- ============================================================
-- 2. GSA FUNDING ELIGIBILITY
-- ============================================================

ALTER TABLE apn
    ADD COLUMN IF NOT EXISTS gsa_review_started      DATE,
    ADD COLUMN IF NOT EXISTS gsa_review_completed    DATE,
    ADD COLUMN IF NOT EXISTS gsa_eligibility_reviewer VARCHAR(255),
    ADD COLUMN IF NOT EXISTS eligible_for_gsa_funding BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS date_sent_to_gsa         DATE,
    ADD COLUMN IF NOT EXISTS gsa_decision             VARCHAR(50),   -- approved, denied, pending
    ADD COLUMN IF NOT EXISTS associated_gsa           VARCHAR(255),
    ADD COLUMN IF NOT EXISTS gsa_contact_name         VARCHAR(255);

-- ============================================================
-- 3. RIGHT OF ENTRY
-- ============================================================

ALTER TABLE program_enrollment
    ADD COLUMN IF NOT EXISTS roe_effective_date DATE,
    ADD COLUMN IF NOT EXISTS roe_expires_date   DATE;

-- ============================================================
-- 4. PROGRAM INTEREST FLAGS (on intake / person level)
-- ============================================================

CREATE TABLE IF NOT EXISTS program_interest (
    interest_id             SERIAL PRIMARY KEY,
    pid                     VARCHAR(20) NOT NULL REFERENCES person(pid),
    bw_interest             BOOLEAN DEFAULT FALSE,
    tw_interest             BOOLEAN DEFAULT FALSE,
    wq_interest             BOOLEAN DEFAULT FALSE,
    ww_interest             BOOLEAN DEFAULT FALSE,
    disaster_resiliency     BOOLEAN DEFAULT FALSE,
    intake_date             DATE,
    created_date            TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. SITE ASSESSMENTS — fifth program type
-- ============================================================

CREATE TABLE IF NOT EXISTS site_assessment (
    sa_id                   SERIAL PRIMARY KEY,
    sa_number               VARCHAR(50),                -- SA ID format
    pid                     VARCHAR(20) REFERENCES person(pid),
    structure_id            INT REFERENCES structure(structure_id),
    caseworker_id           INT REFERENCES staff(staff_id),
    field_staff_id          INT REFERENCES staff(staff_id),
    assessment_date         DATE,
    scheduled_date          DATE,
    status                  VARCHAR(50),                -- scheduled, completed, pending, cancelled
    status_secondary        VARCHAR(100),
    well_lat                DECIMAL(10,7),
    well_long               DECIMAL(10,7),
    structure_lat           DECIMAL(10,7),
    structure_long          DECIMAL(10,7),
    survey123_ref           VARCHAR(255),               -- Survey123 submission GUID
    notes                   TEXT,
    created_date            TIMESTAMP DEFAULT NOW(),
    active_flag             BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 6. DEMOGRAPHICS
-- ============================================================

CREATE TABLE IF NOT EXISTS demographics (
    demo_id                 SERIAL PRIMARY KEY,
    pid                     VARCHAR(20) NOT NULL REFERENCES person(pid),
    race                    VARCHAR(100),
    ethnicity               VARCHAR(100),
    english_speaking        BOOLEAN DEFAULT TRUE,
    female_head_of_household BOOLEAN DEFAULT FALSE,
    disability              BOOLEAN DEFAULT FALSE,
    veteran                 BOOLEAN DEFAULT FALSE,
    internet_access         BOOLEAN DEFAULT FALSE,
    internet_type           VARCHAR(100),
    internet_carrier        VARCHAR(100),
    farm_labor              BOOLEAN DEFAULT FALSE,
    created_date            TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. VERIFICATIONS (official use only)
-- ============================================================

CREATE TABLE IF NOT EXISTS verification (
    verification_id             SERIAL PRIMARY KEY,
    pid                         VARCHAR(20) NOT NULL REFERENCES person(pid),
    enrollment_id               INT REFERENCES program_enrollment(enrollment_id),
    application_review_completed BOOLEAN DEFAULT FALSE,
    application_review_date     DATE,
    application_review_by       INT REFERENCES staff(staff_id),
    income_qualified             BOOLEAN DEFAULT FALSE,
    income_qualified_date        DATE,
    income_qualified_by          INT REFERENCES staff(staff_id),
    owner_verified               BOOLEAN DEFAULT FALSE,
    owner_verified_date          DATE,
    owner_verified_by            INT REFERENCES staff(staff_id),
    -- Title information
    name_on_id                   VARCHAR(255),
    dob_on_id                    DATE,
    dl_id_number                 VARCHAR(100),
    created_date                 TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 8. PERSON FLAGS (conflict of interest, prior SHE contact)
-- ============================================================

ALTER TABLE person
    ADD COLUMN IF NOT EXISTS she_employee_relation    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS governing_board_relation BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS swrcb_relation           BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS gsa_relation             BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS relation_detail          TEXT,
    ADD COLUMN IF NOT EXISTS previously_applied       BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS prior_programs           VARCHAR(255);

-- ============================================================
-- 9. WELL INFORMATION — expanded fields
-- ============================================================

ALTER TABLE well
    ADD COLUMN IF NOT EXISTS current_condition        VARCHAR(100),
    ADD COLUMN IF NOT EXISTS submersible_pump         BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS date_issue_first_occurred DATE,
    ADD COLUMN IF NOT EXISTS current_water_source     VARCHAR(255),
    ADD COLUMN IF NOT EXISTS existing_storage_tank    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS storage_tank_gallons     DECIMAL(10,2),
    ADD COLUMN IF NOT EXISTS licensed_inspection      BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS eligible_public_connect  BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS shared_well_agreement    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS media_consent            BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS waitlist_pump_repair      BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS drinking_water_advisory  BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS pump_type                VARCHAR(100),
    ADD COLUMN IF NOT EXISTS number_homes_served      INT,
    ADD COLUMN IF NOT EXISTS number_homes_occupied    INT,
    ADD COLUMN IF NOT EXISTS residency_type           VARCHAR(100),
    ADD COLUMN IF NOT EXISTS owner_occupied           BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS renter_type              VARCHAR(100),
    ADD COLUMN IF NOT EXISTS used_for_business        BOOLEAN DEFAULT FALSE;

-- ============================================================
-- 10. GOVERNMENT ASSISTANCE FLAGS (on eligibility)
-- ============================================================

ALTER TABLE eligibility
    ADD COLUMN IF NOT EXISTS care_enrolled    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS tanf_enrolled    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS snap_enrolled    BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS medi_cal_enrolled BOOLEAN DEFAULT FALSE;

-- ============================================================
-- 11. AUTHORIZED CONTACT and PRIMARY APPLICANT flags
-- ============================================================

ALTER TABLE person_structure
    ADD COLUMN IF NOT EXISTS authorized_contact  BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS primary_applicant   BOOLEAN DEFAULT FALSE;

-- ============================================================
-- 12. PROPERTY — hazard and community fields
-- ============================================================

ALTER TABLE apn
    ADD COLUMN IF NOT EXISTS hazard_flag          BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS hazard_explanation   TEXT,
    ADD COLUMN IF NOT EXISTS pending_consolidation BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS community            VARCHAR(255),
    ADD COLUMN IF NOT EXISTS number_dwellings     INT,
    ADD COLUMN IF NOT EXISTS property_in_escrow   BOOLEAN DEFAULT FALSE;

-- ============================================================
-- 13. DOCUMENT TYPES — add missing types from Access review
-- ============================================================

INSERT INTO document_type (type_name, program_id, required_flag) VALUES
('Right of Entry',                      NULL, TRUE),
('Property Tax Bill',                   NULL, FALSE),
('Tenant Utility Bill',                 NULL, FALSE),
('Rent Limitation Agreement',           NULL, FALSE),
('Drivers License or ID',               NULL, TRUE),
('CARE Enrollment Proof',               NULL, FALSE),
('TANF/SNAP/Medi-Cal Letter',           NULL, FALSE),
('Copy of Will Serve Letter',           4,    FALSE),
('City Fee Estimate',                   4,    FALSE),
('Plumbers Estimate',                   4,    FALSE),
('Drillers Template Requirements',      4,    TRUE),
('Water Well Abandonment Application',  4,    FALSE),
('Disaster Resiliency Application',     NULL, FALSE)
ON CONFLICT DO NOTHING;

-- ============================================================
-- 14. INTEREST LIST — for tracking program waitlist interest
-- ============================================================

CREATE TABLE IF NOT EXISTS interest_list (
    interest_list_id        SERIAL PRIMARY KEY,
    pid                     VARCHAR(20) REFERENCES person(pid),
    program_id              INT REFERENCES program(program_id),
    structure_id            INT REFERENCES structure(structure_id),
    date_added              DATE NOT NULL DEFAULT CURRENT_DATE,
    date_contacted          DATE,
    status                  VARCHAR(50) DEFAULT 'pending',   -- pending, contacted, enrolled, removed
    notes                   TEXT,
    added_by                INT REFERENCES staff(staff_id),
    created_date            TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 15. DISASTER RESILIENCY — fifth program
-- ============================================================

INSERT INTO program (program_name, program_code) VALUES
('Disaster Resiliency', 'DR')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 16. INDEXES on new tables
-- ============================================================

CREATE INDEX IF NOT EXISTS ix_site_assessment_pid    ON site_assessment(pid);
CREATE INDEX IF NOT EXISTS ix_demographics_pid       ON demographics(pid);
CREATE INDEX IF NOT EXISTS ix_verification_pid       ON verification(pid);
CREATE INDEX IF NOT EXISTS ix_program_interest_pid   ON program_interest(pid);
CREATE INDEX IF NOT EXISTS ix_interest_list_pid      ON interest_list(pid);
CREATE INDEX IF NOT EXISTS ix_interest_list_program  ON interest_list(program_id);

-- ============================================================
-- VERIFY
-- ============================================================

SELECT 
    'program_enrollment columns' AS check_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_name = 'program_enrollment'
UNION ALL
SELECT 'apn columns', COUNT(*)
FROM information_schema.columns
WHERE table_name = 'apn'
UNION ALL
SELECT 'well columns', COUNT(*)
FROM information_schema.columns
WHERE table_name = 'well'
UNION ALL
SELECT 'new tables', COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('site_assessment','demographics','verification','program_interest','interest_list');
