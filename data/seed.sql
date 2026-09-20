-- PulseGuard Schema + Seed Data
-- hackIAthon Panamá 2026

-- ============================================
-- CREATE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    blood_type VARCHAR(5),
    allergies JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pre_existences (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(patient_id),
    condition_name VARCHAR(100) NOT NULL,
    diagnosed_date DATE,
    severity VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(patient_id),
    policy_number VARCHAR(30) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    coverage_type VARCHAR(30),
    max_coverage_amount DECIMAL(12,2),
    provider VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admissions (
    admission_id VARCHAR(30) PRIMARY KEY,
    patient_id VARCHAR(20),
    policy_number VARCHAR(30),
    timestamp TIMESTAMP NOT NULL,
    admission_reason VARCHAR(500) NOT NULL,
    vital_signs JSONB,
    symptoms JSONB DEFAULT '[]',
    hospital_code VARCHAR(20),
    status VARCHAR(20) DEFAULT 'received',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(36) PRIMARY KEY,
    admission_id VARCHAR(30) REFERENCES admissions(admission_id),
    level VARCHAR(20) NOT NULL,
    message VARCHAR(500) NOT NULL,
    recommendations JSONB DEFAULT '[]',
    agent_analysis TEXT,
    ai_report TEXT,
    hospital_notified BOOLEAN DEFAULT FALSE,
    insurer_notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id SERIAL PRIMARY KEY,
    admission_id VARCHAR(30),
    action VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_pre_existences_patient ON pre_existences(patient_id);
CREATE INDEX IF NOT EXISTS idx_policies_patient ON policies(patient_id);
CREATE INDEX IF NOT EXISTS idx_policies_number ON policies(policy_number);
CREATE INDEX IF NOT EXISTS idx_admissions_patient ON admissions(patient_id);
CREATE INDEX IF NOT EXISTS idx_admissions_timestamp ON admissions(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);

-- ============================================
-- PACIENTES
-- ============================================

INSERT INTO patients (patient_id, name, age, gender, blood_type, allergies) VALUES
    ('PAT-001', 'Juan Garcia', 45, 'Male', 'O+', '["Penicillin", "Sulfa drugs"]'),
    ('PAT-002', 'Maria Lopez', 32, 'Female', 'A+', '[]'),
    ('PAT-003', 'Pedro Martinez', 67, 'Male', 'B-', '["Ibuprofen"]'),
    ('PAT-004', 'Ana Rodriguez', 28, 'Female', 'AB+', '["Latex"]'),
    ('PAT-005', 'Carlos Mendoza', 55, 'Male', 'O-', '["Aspirin"]'),
    ('PAT-006', 'Laura Fernandez', 41, 'Female', 'A-', '[]'),
    ('PAT-007', 'Roberto Diaz', 72, 'Male', 'AB+', '["Morphine"]'),
    ('PAT-008', 'Isabel Torres', 29, 'Female', 'B+', '[]')
ON CONFLICT (patient_id) DO NOTHING;

-- ============================================
-- PREEXISTENCIAS
-- ============================================

INSERT INTO pre_existences (patient_id, condition_name, diagnosed_date, severity, notes) VALUES
    ('PAT-001', 'Hypertension', '2020-05-15', 'moderate', 'Controlada con medicación'),
    ('PAT-001', 'Type 2 Diabetes', '2019-08-20', 'controlled', 'Metformina 500mg diario'),
    ('PAT-002', 'Asthma', '2010-03-10', 'mild', 'Usa inhalador PRN'),
    ('PAT-003', 'Coronary Artery Disease', '2018-11-05', 'severe', 'Stent colocado 2018'),
    ('PAT-003', 'Heart Failure', '2021-02-28', 'moderate', 'NYHA Class II'),
    ('PAT-003', 'Chronic Kidney Disease', '2022-07-12', 'mild', 'Estadio 2'),
    ('PAT-005', 'COPD', '2015-03-20', 'moderate', 'Ex-fumador'),
    ('PAT-005', 'Hypertension', '2010-01-10', 'controlled', 'Enalapril 10mg'),
    ('PAT-007', 'Diabetes Type 1', '1985-06-15', 'insulin-dependent', 'Insulina multiples dosis'),
    ('PAT-007', 'Chronic Kidney Disease', '2020-09-01', 'severe', 'Estadio 4'),
    ('PAT-007', 'Anemia', '2021-03-15', 'moderate', 'Suplementación de hierro')
ON CONFLICT DO NOTHING;

-- ============================================
-- PÓLIZAS
-- ============================================

INSERT INTO policies (policy_id, patient_id, policy_number, status, start_date, end_date, coverage_type, max_coverage_amount, provider) VALUES
    ('POL-001', 'PAT-001', 'POL-2024-001', 'active', '2024-01-01', '2027-12-31', 'comprehensive', 100000.00, 'HealthGuard Insurance'),
    ('POL-003', 'PAT-003', 'POL-2024-003', 'active', '2024-06-01', '2027-06-01', 'premium', 200000.00, 'HealthGuard Insurance'),
    ('POL-005', 'PAT-005', 'POL-2024-005', 'active', '2024-03-01', '2027-03-01', 'comprehensive', 150000.00, 'HealthGuard Insurance'),
    ('POL-006', 'PAT-006', 'POL-2024-006', 'active', '2024-09-01', '2027-09-01', 'basic', 75000.00, 'HealthGuard Insurance'),
    ('POL-008', 'PAT-008', 'POL-2024-008', 'active', '2025-01-01', '2028-01-01', 'premium', 250000.00, 'HealthGuard Insurance'),
    ('POL-002', 'PAT-002', 'POL-2024-002', 'expired', '2023-01-01', '2024-01-01', 'basic', 50000.00, 'HealthGuard Insurance'),
    ('POL-004', 'PAT-004', 'POL-2024-004', 'suspended', '2024-03-01', '2027-03-01', 'comprehensive', 150000.00, 'HealthGuard Insurance'),
    ('POL-007', 'PAT-007', 'POL-2024-007', 'cancelled', '2024-01-01', '2027-01-01', 'premium', 300000.00, 'HealthGuard Insurance')
ON CONFLICT (policy_id) DO NOTHING;
