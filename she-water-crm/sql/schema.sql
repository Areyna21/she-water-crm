-- ============================================================
-- Self-Help Enterprises Water Assistance CRM
-- PostgreSQL Schema — Supabase Compatible
-- Converted from T-SQL prototype v1.0
-- ============================================================

-- ============================================================
-- LOOKUP TABLES
-- ============================================================

CREATE TABLE county (
    county_id           SERIAL PRIMARY KEY,
    county_name         VARCHAR(100) NOT NULL,
    fips_code           VARCHAR(10),
    state               VARCHAR(2) DEFAULT 'CA',
    active_flag         BOOLEAN DEFAULT TRUE
);

CREATE TABLE program (
    program_id          SERIAL PRIMARY KEY,
    program_name        VARCHAR(100) NOT NULL,
    program_code        VARCHAR(5) NOT NULL,
    active_flag         BOOLEAN DEFAULT TRUE
);

CREATE TABLE activity_type (
    activity_type_id    SERIAL PRIMARY KEY,
    program_id          INT REFERENCES program(program_id),
    activity_name       VARCHAR(100) NOT NULL,
    activity_category   VARCHAR(50),
    triggers_next_step  BOOLEAN DEFAULT FALSE,
    active_flag         BOOLEAN DEFAULT TRUE
);

CREATE TABLE document_type (
    document_type_id    SERIAL PRIMARY KEY,
    type_name           VARCHAR(100) NOT NULL,
    program_id          INT REFERENCES program(program_id),
    required_flag       BOOLEAN DEFAULT FALSE
);

CREATE TABLE vendor_type (
    vendor_type_id      SERIAL PRIMARY KEY,
    type_name           VARCHAR(100) NOT NULL
);

CREATE TABLE role_type (
    role_type_id        SERIAL PRIMARY KEY,
    role_name           VARCHAR(50) NOT NULL
);

CREATE TABLE enrollment_status (
    status_id           SERIAL PRIMARY KEY,
    status_name         VARCHAR(50) NOT NULL
);

CREATE TABLE sample_point_type (
    point_type_id       SERIAL PRIMARY KEY,
    point_type_name     VARCHAR(50) NOT NULL
);

-- ============================================================
-- SPATIAL / ORGANIZATIONAL
-- ============================================================

CREATE TABLE region (
    region_id           SERIAL PRIMARY KEY,
    region_name         VARCHAR(100) NOT NULL,
    subbasin_name       VARCHAR(100),
    gsa_boundary_ref    VARCHAR(100),
    region_manager_id   INT,
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- PROPERTY
-- ============================================================

CREATE TABLE property (
    property_id         SERIAL PRIMARY KEY,
    property_lat        DECIMAL(10,7),
    property_long       DECIMAL(10,7),
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- APN
-- ============================================================

CREATE TABLE apn (
    apn_id                      SERIAL PRIMARY KEY,
    property_id                 INT REFERENCES property(property_id),
    apn_number                  VARCHAR(50) NOT NULL,
    county_id                   INT NOT NULL REFERENCES county(county_id),
    dmpid                       VARCHAR(50),
    regrid_uuid                 VARCHAR(100),
    authoritative_apn           VARCHAR(50),
    mailing_apn                 VARCHAR(50),
    mailing_address             VARCHAR(255),
    gsa_zone                    VARCHAR(100),
    management_zone             VARCHAR(100),
    floodplain_flag             BOOLEAN DEFAULT FALSE,
    region_id                   INT REFERENCES region(region_id),
    region_assignment_method    VARCHAR(20) DEFAULT 'unassigned',
    region_assigned_by          INT,
    region_assigned_date        TIMESTAMP,
    apn_lat                     DECIMAL(10,7),
    apn_long                    DECIMAL(10,7),
    active_flag                 BOOLEAN DEFAULT TRUE,
    created_date                TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_apn_county UNIQUE (apn_number, county_id)
);

-- ============================================================
-- STRUCTURE
-- ============================================================

CREATE TABLE structure (
    structure_id        SERIAL PRIMARY KEY,
    apn_id              INT NOT NULL REFERENCES apn(apn_id),
    structure_type      VARCHAR(50),
    unit_number         VARCHAR(20),
    structure_lat       DECIMAL(10,7),
    structure_long      DECIMAL(10,7),
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- STAFF (before person so created_by FK works)
-- ============================================================

CREATE TABLE staff (
    staff_id            SERIAL PRIMARY KEY,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255),
    phone               VARCHAR(20),
    role                VARCHAR(50),
    region_id           INT REFERENCES region(region_id),
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- Add manager FK now that staff exists
ALTER TABLE region ADD CONSTRAINT fk_region_manager
    FOREIGN KEY (region_manager_id) REFERENCES staff(staff_id);

-- Add staff FK to APN
ALTER TABLE apn ADD CONSTRAINT fk_apn_staff
    FOREIGN KEY (region_assigned_by) REFERENCES staff(staff_id);

-- ============================================================
-- PERSON
-- ============================================================

CREATE TABLE person (
    pid                 VARCHAR(20) PRIMARY KEY,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    middle_name         VARCHAR(100),
    dob                 DATE,
    phone_primary       VARCHAR(20),
    phone_secondary     VARCHAR(20),
    email               VARCHAR(255),
    preferred_language  VARCHAR(50) DEFAULT 'English',
    interpreter_needed  BOOLEAN DEFAULT FALSE,
    created_date        TIMESTAMP DEFAULT NOW(),
    created_by          INT REFERENCES staff(staff_id),
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- PERSON <-> STRUCTURE
-- ============================================================

CREATE TABLE person_structure (
    id                  SERIAL PRIMARY KEY,
    pid                 VARCHAR(20) NOT NULL REFERENCES person(pid),
    structure_id        INT NOT NULL REFERENCES structure(structure_id),
    role_type_id        INT NOT NULL REFERENCES role_type(role_type_id),
    household_size      INT,
    start_date          DATE NOT NULL,
    end_date            DATE,
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- VENDOR
-- ============================================================

CREATE TABLE vendor (
    vendor_id           SERIAL PRIMARY KEY,
    vendor_name         VARCHAR(255) NOT NULL,
    vendor_type_id      INT REFERENCES vendor_type(vendor_type_id),
    phone               VARCHAR(20),
    email               VARCHAR(255),
    service_counties    VARCHAR(255),
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- WELL
-- ============================================================

CREATE TABLE well (
    well_id             SERIAL PRIMARY KEY,
    apn_id              INT NOT NULL REFERENCES apn(apn_id),
    well_number         VARCHAR(50),
    well_type           VARCHAR(50),
    well_lat            DECIMAL(10,7),
    well_long           DECIMAL(10,7),
    depth_ft            DECIMAL(10,2),
    static_water_level  DECIMAL(10,2),
    drill_date          DATE,
    driller_id          INT REFERENCES vendor(vendor_id),
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- WELL <-> STRUCTURE
-- ============================================================

CREATE TABLE well_structure (
    id                  SERIAL PRIMARY KEY,
    well_id             INT NOT NULL REFERENCES well(well_id),
    structure_id        INT NOT NULL REFERENCES structure(structure_id),
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- TANK
-- ============================================================

CREATE TABLE tank (
    tank_id             SERIAL PRIMARY KEY,
    vendor_id           INT REFERENCES vendor(vendor_id),
    capacity_gallons    INT,
    install_date        DATE,
    removal_date        DATE,
    tank_lat            DECIMAL(10,7),
    tank_long           DECIMAL(10,7),
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- TANK <-> STRUCTURE
-- ============================================================

CREATE TABLE tank_service_area (
    id                  SERIAL PRIMARY KEY,
    tank_id             INT NOT NULL REFERENCES tank(tank_id),
    structure_id        INT NOT NULL REFERENCES structure(structure_id),
    apn_id              INT NOT NULL REFERENCES apn(apn_id),
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- SAMPLE POINT
-- ============================================================

CREATE TABLE sample_point (
    sample_point_id     SERIAL PRIMARY KEY,
    point_type_id       INT NOT NULL REFERENCES sample_point_type(point_type_id),
    well_id             INT REFERENCES well(well_id),
    structure_id        INT REFERENCES structure(structure_id),
    location_description VARCHAR(255),
    sample_lat          DECIMAL(10,7),
    sample_long         DECIMAL(10,7),
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- WATER QUALITY RESULT
-- ============================================================

CREATE TABLE water_quality_result (
    result_id           SERIAL PRIMARY KEY,
    sample_point_id     INT NOT NULL REFERENCES sample_point(sample_point_id),
    vendor_id           INT REFERENCES vendor(vendor_id),
    contaminant         VARCHAR(100) NOT NULL,
    value               DECIMAL(18,6),
    unit                VARCHAR(20),
    mcl_value           DECIMAL(18,6),
    exceeds_mcl_flag    BOOLEAN DEFAULT FALSE,
    sample_date         DATE NOT NULL,
    result_date         DATE,
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- EQUIPMENT
-- ============================================================

CREATE TABLE equipment (
    equipment_id        SERIAL PRIMARY KEY,
    sample_point_id     INT NOT NULL REFERENCES sample_point(sample_point_id),
    equipment_type      VARCHAR(50),
    make                VARCHAR(100),
    model               VARCHAR(100),
    serial_number       VARCHAR(100),
    install_date        DATE,
    last_service_date   DATE,
    next_service_date   DATE,
    active_flag         BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- ELIGIBILITY
-- ============================================================

CREATE TABLE eligibility (
    eligibility_id      SERIAL PRIMARY KEY,
    pid                 VARCHAR(20) NOT NULL REFERENCES person(pid),
    household_size      INT,
    monthly_income      DECIMAL(10,2),
    income_verified     BOOLEAN DEFAULT FALSE,
    verified_by         INT REFERENCES staff(staff_id),
    verified_date       DATE,
    effective_date      DATE NOT NULL,
    expiration_date     DATE
);

-- ============================================================
-- PROGRAM ENROLLMENT
-- ============================================================

CREATE TABLE program_enrollment (
    enrollment_id       SERIAL PRIMARY KEY,
    pid                 VARCHAR(20) NOT NULL REFERENCES person(pid),
    program_id          INT NOT NULL REFERENCES program(program_id),
    structure_id        INT NOT NULL REFERENCES structure(structure_id),
    program_specific_id VARCHAR(50),
    caseworker_id       INT REFERENCES staff(staff_id),
    status_id           INT REFERENCES enrollment_status(status_id),
    enrollment_date     DATE NOT NULL,
    exit_date           DATE,
    exit_reason         VARCHAR(255),
    waitlist_date       DATE,
    active_flag         BOOLEAN DEFAULT TRUE,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- CASE
-- ============================================================

CREATE TABLE case_record (
    case_id             SERIAL PRIMARY KEY,
    enrollment_id       INT NOT NULL REFERENCES program_enrollment(enrollment_id),
    assigned_staff_id   INT REFERENCES staff(staff_id),
    opened_date         DATE NOT NULL,
    closed_date         DATE,
    case_status         VARCHAR(50),
    notes               TEXT,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ACTIVITY
-- ============================================================

CREATE TABLE activity (
    activity_id         SERIAL PRIMARY KEY,
    case_id             INT NOT NULL REFERENCES case_record(case_id),
    activity_type_id    INT NOT NULL REFERENCES activity_type(activity_type_id),
    performed_by        INT REFERENCES staff(staff_id),
    activity_date       TIMESTAMP NOT NULL,
    notes               TEXT,
    next_step_triggered BOOLEAN DEFAULT FALSE,
    survey123_ref       VARCHAR(255),
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- APPROVAL
-- ============================================================

CREATE TABLE approval (
    approval_id         SERIAL PRIMARY KEY,
    case_id             INT NOT NULL REFERENCES case_record(case_id),
    submitted_by        INT REFERENCES staff(staff_id),
    submitted_date      TIMESTAMP,
    reviewed_by         INT REFERENCES staff(staff_id),
    reviewed_date       TIMESTAMP,
    decision            VARCHAR(20),
    decision_notes      TEXT
);

-- ============================================================
-- DELIVERY
-- ============================================================

CREATE TABLE delivery (
    delivery_id         SERIAL PRIMARY KEY,
    enrollment_id       INT NOT NULL REFERENCES program_enrollment(enrollment_id),
    vendor_id           INT REFERENCES vendor(vendor_id),
    scheduled_date      DATE NOT NULL,
    delivered_date      DATE,
    allotment_units     INT,
    delivery_status     VARCHAR(50),
    missed_reason       VARCHAR(255),
    reported_by         VARCHAR(50),
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TANK FILL
-- ============================================================

CREATE TABLE tank_fill (
    fill_id             SERIAL PRIMARY KEY,
    tank_id             INT NOT NULL REFERENCES tank(tank_id),
    enrollment_id       INT NOT NULL REFERENCES program_enrollment(enrollment_id),
    vendor_id           INT REFERENCES vendor(vendor_id),
    scheduled_date      DATE NOT NULL,
    fill_date           DATE,
    gallons_delivered   DECIMAL(10,2),
    fill_status         VARCHAR(50),
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- DOCUMENT
-- ============================================================

CREATE TABLE document (
    document_id         SERIAL PRIMARY KEY,
    pid                 VARCHAR(20) NOT NULL REFERENCES person(pid),
    enrollment_id       INT REFERENCES program_enrollment(enrollment_id),
    document_type_id    INT REFERENCES document_type(document_type_id),
    file_name           VARCHAR(255),
    file_path           VARCHAR(500),
    source              VARCHAR(50),
    upload_date         TIMESTAMP DEFAULT NOW(),
    uploaded_by         INT REFERENCES staff(staff_id),
    ai_extracted        BOOLEAN DEFAULT FALSE,
    extraction_confidence DECIMAL(5,2),
    reviewed_flag       BOOLEAN DEFAULT FALSE,
    reviewed_by         INT REFERENCES staff(staff_id)
);

-- ============================================================
-- COMMUNICATION LOG
-- ============================================================

CREATE TABLE communication_log (
    log_id              SERIAL PRIMARY KEY,
    pid                 VARCHAR(20) NOT NULL REFERENCES person(pid),
    staff_id            INT REFERENCES staff(staff_id),
    contact_date        TIMESTAMP NOT NULL,
    contact_type        VARCHAR(50),
    contact_result      VARCHAR(50),
    notes               TEXT,
    created_date        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- FIELD CHANGE LOG
-- ============================================================

CREATE TABLE field_change_log (
    log_id              SERIAL PRIMARY KEY,
    table_name          VARCHAR(100) NOT NULL,
    record_id           VARCHAR(50) NOT NULL,
    field_name          VARCHAR(100) NOT NULL,
    old_value           TEXT,
    new_value           TEXT,
    changed_by          INT REFERENCES staff(staff_id),
    changed_date        TIMESTAMP DEFAULT NOW(),
    change_reason       VARCHAR(255)
);

-- ============================================================
-- REFERRAL SOURCE
-- ============================================================

CREATE TABLE referral_source (
    referral_id         SERIAL PRIMARY KEY,
    pid                 VARCHAR(20) NOT NULL REFERENCES person(pid),
    source_type         VARCHAR(100),
    source_detail       VARCHAR(255),
    referral_date       DATE NOT NULL
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX ix_apn_county        ON apn(apn_number, county_id);
CREATE INDEX ix_apn_dmpid         ON apn(dmpid) WHERE dmpid IS NOT NULL;
CREATE INDEX ix_structure_apn     ON structure(apn_id);
CREATE INDEX ix_person_name       ON person(last_name, first_name);
CREATE INDEX ix_enrollment_pid    ON program_enrollment(pid);
CREATE INDEX ix_enrollment_prog   ON program_enrollment(program_id);
CREATE INDEX ix_case_enrollment   ON case_record(enrollment_id);
CREATE INDEX ix_activity_case     ON activity(case_id);
CREATE INDEX ix_delivery_enroll   ON delivery(enrollment_id);
CREATE INDEX ix_document_pid      ON document(pid);
CREATE INDEX ix_ps_pid            ON person_structure(pid);
CREATE INDEX ix_well_apn          ON well(apn_id);

-- ============================================================
-- SEED LOOKUP DATA
-- ============================================================

INSERT INTO county (county_name, fips_code) VALUES
('Fresno',      '06019'),
('Tulare',      '06107'),
('Kings',       '06031'),
('Kern',        '06029'),
('Madera',      '06039'),
('Merced',      '06047'),
('Stanislaus',  '06099'),
('San Joaquin', '06077'),
('Mariposa',    '06043'),
('Calaveras',   '06009');

INSERT INTO program (program_name, program_code) VALUES
('Bottled Water',   'BW'),
('Tank Water',      'TW'),
('Water Quality',   'WQ'),
('Water Well',      'WW');

INSERT INTO vendor_type (type_name) VALUES
('Bottled Water Delivery'),
('Tank Hauler'),
('Well Driller'),
('Water Quality Lab');

INSERT INTO role_type (role_name) VALUES
('Owner'),
('Tenant'),
('Authorized Contact');

INSERT INTO enrollment_status (status_name) VALUES
('Active'),
('Inactive'),
('Waitlist'),
('Closed'),
('Pending Approval');

INSERT INTO sample_point_type (point_type_name) VALUES
('POE'),
('POU'),
('Well');

INSERT INTO activity_type (program_id, activity_name, activity_category, triggers_next_step) VALUES
-- Universal
(NULL, 'Intake Call',                   'intake',    TRUE),
(NULL, 'Outreach Contact',              'intake',    TRUE),
(NULL, 'Emergency Mass Enrollment',     'intake',    TRUE),
(NULL, 'Application Received',          'document',  TRUE),
(NULL, 'Initial Site Visit Scheduled',  'field',     TRUE),
(NULL, 'Initial Site Visit Completed',  'field',     TRUE),
(NULL, 'Document Requested',            'document',  FALSE),
(NULL, 'Document Received',             'document',  FALSE),
(NULL, 'Submitted for Approval',        'approval',  TRUE),
(NULL, 'Approved',                      'approval',  TRUE),
(NULL, 'Rejected',                      'approval',  TRUE),
(NULL, 'Case Closed',                   'intake',    FALSE),
(NULL, 'Communication Attempt',         'intake',    FALSE),
-- Bottled Water
(1, 'Vendor Assigned',                  'delivery',  TRUE),
(1, 'Added to Delivery Schedule',       'delivery',  FALSE),
(1, 'Delivery Completed',              'delivery',  FALSE),
(1, 'Missed Delivery Reported',         'delivery',  FALSE),
(1, 'Delivery Disputed',               'delivery',  FALSE),
-- Tank Water
(2, 'Tank Delivered',                   'field',     TRUE),
(2, 'Tank Installed',                   'field',     FALSE),
(2, 'Tank Fill Completed',             'delivery',  FALSE),
(2, 'Tank Fill Missed',                'delivery',  FALSE),
(2, 'Tank Removed',                    'field',     TRUE),
-- Water Quality
(3, 'Sample Collected',                'lab',       TRUE),
(3, 'Lab Assigned',                    'lab',       FALSE),
(3, 'Lab Results Received',            'lab',       TRUE),
(3, 'MCL Exceeded',                    'lab',       TRUE),
(3, 'Treatment Recommended',           'lab',       TRUE),
(3, 'POE Equipment Installed',         'field',     FALSE),
(3, 'POU Equipment Installed',         'field',     FALSE),
(3, 'Follow Up Sample Scheduled',      'lab',       FALSE),
(3, 'Monitoring Schedule Established', 'lab',       FALSE),
-- Water Well
(4, 'Well Sounding Completed',         'field',     TRUE),
(4, 'Well Assessment Completed',       'field',     TRUE),
(4, 'Driller Estimates Collected',     'document',  TRUE),
(4, 'Driller Assigned',               'field',     TRUE),
(4, 'Drilling Scheduled',             'field',     TRUE),
(4, 'Drilling Completed',             'field',     TRUE),
(4, 'New Well Funded',                'approval',  TRUE),
(4, 'Driller Paid',                   'approval',  FALSE),
(4, 'Well Education Delivered',        'field',     FALSE),
(4, 'WQ Referral Triggered',          'intake',    TRUE);

INSERT INTO document_type (type_name, program_id, required_flag) VALUES
('Program Application',             NULL, TRUE),
('Proof of Income',                 NULL, TRUE),
('Proof of Address',                NULL, TRUE),
('Household Size Verification',     NULL, FALSE),
('Site Assessment Form',            NULL, TRUE),
('Lab Result',                      3,    TRUE),
('Property Deed',                   4,    TRUE),
('Program Addendum',                4,    TRUE),
('Driller Estimate',                4,    TRUE),
('Well Permit',                     4,    TRUE),
('Loan Application',                4,    FALSE),
('Well Education Acknowledgment',   4,    TRUE),
('Tank Service Agreement',          2,    TRUE),
('Delivery Confirmation',           1,    FALSE);

-- ============================================================
-- SEED ORGANIZATIONAL DATA
-- ============================================================

INSERT INTO region (region_name, subbasin_name, gsa_boundary_ref) VALUES
('Region 1 - Kings River',      'Kings Subbasin',           'Kings River GSA'),
('Region 2 - Tulare Lake',      'Tulare Lake Subbasin',     'Tulare Irrigation District GSA'),
('Region 3 - Kaweah',           'Kaweah Subbasin',          'Kaweah GSA'),
('Region 4 - Tule',             'Tule Subbasin',            'Tule River GSA'),
('Region 5 - Delta-Mendota',    'Delta-Mendota Subbasin',   'Fresno Irrigation District GSA');

INSERT INTO staff (first_name, last_name, email, phone, role, region_id) VALUES
('Maria',     'Gutierrez',  'mgutierrez@selfhelpenterprises.org',  '559-555-0101', 'region_manager', 1),
('Jose',      'Ramirez',    'jramirez@selfhelpenterprises.org',    '559-555-0102', 'caseworker',     1),
('Ana',       'Torres',     'atorres@selfhelpenterprises.org',     '559-555-0103', 'caseworker',     1),
('Carlos',    'Mendoza',    'cmendoza@selfhelpenterprises.org',    '559-555-0104', 'field_staff',    1),
('Elena',     'Vega',       'evega@selfhelpenterprises.org',       '559-555-0105', 'field_staff',    1),
('Roberto',   'Flores',     'rflores@selfhelpenterprises.org',     '559-555-0201', 'region_manager', 2),
('Sandra',    'Cruz',       'scruz@selfhelpenterprises.org',       '559-555-0202', 'caseworker',     2),
('Miguel',    'Reyes',      'mreyes@selfhelpenterprises.org',      '559-555-0203', 'caseworker',     2),
('Patricia',  'Lopez',      'plopez@selfhelpenterprises.org',      '559-555-0204', 'field_staff',    2),
('David',     'Morales',    'dmorales@selfhelpenterprises.org',    '559-555-0205', 'field_staff',    2),
('Linda',     'Castillo',   'lcastillo@selfhelpenterprises.org',   '559-555-0301', 'region_manager', 3),
('Francisco', 'Hernandez',  'fhernandez@selfhelpenterprises.org',  '559-555-0302', 'caseworker',     3),
('Rosa',      'Jimenez',    'rjimenez@selfhelpenterprises.org',    '559-555-0303', 'caseworker',     3),
('Juan',      'Alvarez',    'jalvarez@selfhelpenterprises.org',    '559-555-0304', 'field_staff',    3),
('Carmen',    'Diaz',       'cdiaz@selfhelpenterprises.org',       '559-555-0305', 'field_staff',    3),
('Thomas',    'Navarro',    'tnavarro@selfhelpenterprises.org',    '559-555-0401', 'region_manager', 4),
('Gloria',    'Ruiz',       'gruiz@selfhelpenterprises.org',       '559-555-0402', 'caseworker',     4),
('Eduardo',   'Vargas',     'evargas@selfhelpenterprises.org',     '559-555-0403', 'caseworker',     4),
('Silvia',    'Medina',     'smedina@selfhelpenterprises.org',     '559-555-0404', 'field_staff',    4),
('Ricardo',   'Guzman',     'rguzman@selfhelpenterprises.org',     '559-555-0405', 'field_staff',    4),
('Angela',    'Ortega',     'aortega@selfhelpenterprises.org',     '559-555-0501', 'region_manager', 5),
('Felipe',    'Ramos',      'framos@selfhelpenterprises.org',      '559-555-0502', 'caseworker',     5),
('Veronica',  'Soto',       'vsoto@selfhelpenterprises.org',       '559-555-0503', 'caseworker',     5),
('Hector',    'Rios',       'hrios@selfhelpenterprises.org',       '559-555-0504', 'field_staff',    5),
('Beatriz',   'Pena',       'bpena@selfhelpenterprises.org',       '559-555-0505', 'field_staff',    5);

-- Update region managers now that staff IDs exist
UPDATE region SET region_manager_id = 1  WHERE region_id = 1;
UPDATE region SET region_manager_id = 6  WHERE region_id = 2;
UPDATE region SET region_manager_id = 11 WHERE region_id = 3;
UPDATE region SET region_manager_id = 16 WHERE region_id = 4;
UPDATE region SET region_manager_id = 21 WHERE region_id = 5;

INSERT INTO vendor (vendor_name, vendor_type_id, phone, email, service_counties) VALUES
('Crystal Springs Delivery',        1, '559-555-1001', 'orders@crystalsprings.com',     'Fresno,Kings,Madera'),
('Valley Pure Water',                1, '559-555-1002', 'dispatch@valleypure.com',       'Tulare,Kern'),
('Primo Water Services',             1, '559-555-1003', 'service@primowater.com',        'Merced,Stanislaus,San Joaquin'),
('Arrowhead Direct',                 1, '559-555-1004', 'service@arrowhead.com',         'Fresno,Madera,Merced'),
('Culligan of the Valley',           1, '559-555-1005', 'valley@culligan.com',           'Tulare,Kings,Kern'),
('Central Valley Tank Services',     2, '559-555-2001', 'dispatch@cvtank.com',           'Fresno,Kings,Tulare,Kern'),
('Valley Water Haulers',             2, '559-555-2002', 'office@valleyhaulers.com',      'Madera,Merced,Stanislaus'),
('Western Ag Water Services',        2, '559-555-2003', 'info@westernag.com',            'Kern,Kings,Tulare'),
('San Joaquin Drilling Co',          3, '559-555-3001', 'bids@sjdrillingco.com',         'Fresno,Kings,Madera'),
('Central Valley Well Services',     3, '559-555-3002', 'info@cvwellservices.com',       'Tulare,Kern'),
('Valley Deep Water Drilling',       3, '559-555-3003', 'quotes@valleydeepwater.com',    'Merced,Stanislaus,San Joaquin'),
('Pacific Western Drilling',         3, '559-555-3004', 'quotes@pacificwestern.com',     'Fresno,Tulare,Kings'),
('Fresno Pacific Laboratory',        4, '559-555-4001', 'results@fresnolab.com',         'Fresno,Madera,Kings'),
('Central Valley Analytical Lab',    4, '559-555-4002', 'lab@cvanalytical.com',          'Tulare,Kern'),
('Valley Environmental Testing',     4, '559-555-4003', 'info@valleyenviro.com',         'Merced,Stanislaus,San Joaquin');
