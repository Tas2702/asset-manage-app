-- DEPARTMENTS TABLE
-- Must be created first as users references it

CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    location      TEXT NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- USERS TABLE
-- Admin and user accounts, each belonging to a department

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password      TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    department_id INTEGER,                              -- FK to departments.department_id
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON DELETE SET NULL  -- If department is deleted, user becomes unassigned
);

-- ASSETS TABLE

CREATE TABLE IF NOT EXISTS assets (
    asset_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_tag       TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL
                    CHECK(category IN (
                        'Laptop', 'Desktop', 'Monitor',
                        'Phone', 'Tablet', 'Printer',
                        'Networking', 'Other'
                    )),
    status          TEXT NOT NULL DEFAULT 'Available'
                    CHECK(status IN (
                        'Available', 'Assigned',
                        'Under Repair', 'Decommissioned'
                    )),
    assigned_to     INTEGER,                            -- FK to users.user_id
    purchase_date   DATE,
    warranty_expiry DATE,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
        ON DELETE SET NULL  -- If user is deleted, asset becomes unassigned
);

-- SEED DATA - DEPARTMENTS

INSERT OR IGNORE INTO departments (name, location) VALUES
    ('IT',               'Floor 3 - Server Room'),
    ('Finance',          'Floor 2 - East Wing'),
    ('HR',               'Floor 1 - North Wing'),
    ('Marketing',        'Floor 2 - West Wing'),
    ('Sales',            'Floor 1 - South Wing'),
    ('Operations',       'Floor 3 - West Wing'),
    ('Legal',            'Floor 4 - North Wing'),
    ('R&D',              'Floor 4 - East Wing'),
    ('Customer Support', 'Floor 1 - East Wing'),
    ('Admin',            'Floor 2 - North Wing');

-- SEED DATA - USERS
-- Admin: admin123 | Regular users: password123

INSERT OR IGNORE INTO users (username, email, password, role, department_id) VALUES
    ('admin',    'admin@company.com',    'admin123',    'admin', 1),
    ('jlevi',    'j.levi@company.com',   'password123', 'user',  8),
    ('osimons',  'o.simons@company.com', 'password123', 'user',  2),
    ('tmori',    't.mori@company.com',   'password123', 'user',  4),
    ('lwillow',  'l.willow@company.com', 'password123', 'user',  5),
    ('rmiren',   'r.miren@company.com',  'password123', 'user',  1),
    ('solive',   's.olive@company.com',  'password123', 'user',  6),
    ('kbrownie', 'k.brownie@company.com','password123', 'user',  3),
    ('emolse',   'e.molse@company.com',  'password123', 'user',  9),
    ('dpinit',   'd.pinit@company.com',  'password123', 'user',  10);

-- SEED DATA - ASSETS

INSERT OR IGNORE INTO assets (asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry, notes) VALUES
    ('SET-001', 'Dell XPS Laptop',         'Laptop',     'Assigned',        2, '2022-03-15', '2025-03-15', 'Assigned to J. Levi - R&D team'),
    ('SET-002', 'HP EliteDesk Desktop',    'Desktop',    'Assigned',        3, '2021-06-01', '2024-06-01', 'Assigned to O. Simons - Finance team'),
    ('SET-003', 'Samsung 27" Monitor',     'Monitor',    'Available',    NULL, '2023-01-10', '2026-01-10', 'Spare monitor in storage room B'),
    ('SET-004', 'iPhone 14 Pro',           'Phone',      'Assigned',        4, '2023-09-20', '2025-09-20', 'Company mobile for T. Mori - Marketing team'),
    ('SET-005', 'Lenovo Pad X1',           'Tablet',     'Under Repair', NULL, '2020-11-05', '2023-11-05', 'Sent to repair - screen damage'),
    ('SET-006', 'iPad Pro',                'Tablet',     'Assigned',        5, '2022-07-18', '2024-07-18', 'Used by L. Willow - Sales team'),
    ('SET-007', 'HP LaserJet Pro Printer', 'Printer',    'Available',    NULL, '2021-04-22', '2024-04-22', 'Located in 2nd floor print room'),
    ('SET-008', 'Cisco Switch',            'Networking', 'Available',    NULL, '2023-02-14', '2026-02-14', 'Spare networking equipment'),
    ('SET-009', 'Dell Latitude 5520',      'Laptop',     'Assigned',        6, '2022-12-01', '2025-12-01', 'Assigned to R. Miren - IT team'),
    ('SET-010', 'MacBook Pro 14"',         'Laptop',     'Decommissioned',NULL, '2019-08-30', '2022-08-30', 'End of life - awaiting disposal');
