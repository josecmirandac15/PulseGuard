-- PulseGuard Schema + Seed Data (demo profesional)
-- hackIAthon Panama 2026 - Reto 4

-- ============================================
-- TABLAS
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

-- admissions no lleva FK: el webhook puede recibir pacientes/polizas no registrados
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

CREATE INDEX IF NOT EXISTS idx_pre_existences_patient ON pre_existences(patient_id);
CREATE INDEX IF NOT EXISTS idx_policies_patient ON policies(patient_id);
CREATE INDEX IF NOT EXISTS idx_policies_number ON policies(policy_number);
CREATE INDEX IF NOT EXISTS idx_admissions_patient ON admissions(patient_id);
CREATE INDEX IF NOT EXISTS idx_admissions_timestamp ON admissions(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);

-- ============================================
-- ASEGURADOS
-- ============================================

INSERT INTO patients (patient_id, name, age, gender, blood_type, allergies) VALUES
    ('PAT-001', 'Juan García',        45, 'Masculino', 'O+',  '["Penicilina", "Sulfas"]'),
    ('PAT-002', 'María López',        32, 'Femenino',  'A+',  '[]'),
    ('PAT-003', 'Pedro Martínez',     67, 'Masculino', 'B-',  '["Ibuprofeno"]'),
    ('PAT-004', 'Ana Rodríguez',      28, 'Femenino',  'AB+', '["Látex"]'),
    ('PAT-005', 'Carlos Mendoza',     55, 'Masculino', 'O-',  '["Aspirina"]'),
    ('PAT-006', 'Laura Fernández',    41, 'Femenino',  'A-',  '[]'),
    ('PAT-007', 'Roberto Díaz',       72, 'Masculino', 'AB+', '["Morfina"]'),
    ('PAT-008', 'Isabel Torres',      29, 'Femenino',  'B+',  '[]'),
    ('PAT-009', 'Ricardo Aparicio',   58, 'Masculino', 'O+',  '["Penicilina"]'),
    ('PAT-010', 'Yolanda Quintero',   63, 'Femenino',  'A+',  '[]'),
    ('PAT-011', 'Andrés Bethancourt', 37, 'Masculino', 'B+',  '[]'),
    ('PAT-012', 'Carmen Espinosa',    70, 'Femenino',  'O-',  '["Sulfas"]'),
    ('PAT-013', 'Gabriel Iturralde',  49, 'Masculino', 'A-',  '["Polvo"]'),
    ('PAT-014', 'Sofía Vallarino',    24, 'Femenino',  'AB+', '[]')
ON CONFLICT (patient_id) DO NOTHING;

-- ============================================
-- PRE-EXISTENCIAS
-- ============================================

INSERT INTO pre_existences (patient_id, condition_name, diagnosed_date, severity, notes) VALUES
    ('PAT-001', 'Hypertension',            '2020-05-15', 'moderate',          'Controlada con medicación'),
    ('PAT-001', 'Type 2 Diabetes',         '2019-08-20', 'controlled',        'Metformina 500 mg diario'),
    ('PAT-002', 'Asthma',                  '2010-03-10', 'mild',              'Usa inhalador PRN'),
    ('PAT-003', 'Coronary Artery Disease', '2018-11-05', 'severe',            'Stent colocado en 2018'),
    ('PAT-003', 'Heart Failure',           '2021-02-28', 'moderate',          'NYHA Clase II'),
    ('PAT-003', 'Chronic Kidney Disease',  '2022-07-12', 'mild',              'Estadio 2'),
    ('PAT-005', 'COPD',                    '2015-03-20', 'moderate',          'Ex-fumador'),
    ('PAT-005', 'Hypertension',            '2010-01-10', 'controlled',        'Enalapril 10 mg'),
    ('PAT-007', 'Diabetes Type 1',         '1985-06-15', 'insulin-dependent', 'Insulina en múltiples dosis'),
    ('PAT-007', 'Chronic Kidney Disease',  '2020-09-01', 'severe',            'Estadio 4'),
    ('PAT-007', 'Anemia',                  '2021-03-15', 'moderate',          'Suplementación de hierro'),
    ('PAT-009', 'Hypertension',            '2017-02-01', 'moderate',          'Losartán 50 mg'),
    ('PAT-010', 'Type 2 Diabetes',         '2014-09-10', 'controlled',        'Metformina + insulina'),
    ('PAT-010', 'Obesity',                 '2012-01-20', 'moderate',          'IMC 32'),
    ('PAT-012', 'Coronary Artery Disease', '2016-06-30', 'severe',            'Angioplastia en 2016'),
    ('PAT-012', 'Hypertension',            '2009-11-11', 'moderate',          'Amlodipino 5 mg'),
    ('PAT-013', 'Asthma',                  '2005-04-18', 'moderate',          'Budesonida'),
    ('PAT-013', 'COPD',                    '2019-10-05', 'mild',              'Espirometría alterada')
ON CONFLICT DO NOTHING;

-- ============================================
-- PÓLIZAS
-- ============================================

INSERT INTO policies (policy_id, patient_id, policy_number, status, start_date, end_date, coverage_type, max_coverage_amount, provider) VALUES
    ('POL-001', 'PAT-001', 'HG-2026-0001', 'active',    '2026-01-01', '2028-12-31', 'comprehensive', 120000.00, 'HealthGuard Insurance'),
    ('POL-002', 'PAT-002', 'HG-2026-0002', 'expired',   '2024-01-01', '2025-12-31', 'basic',          50000.00, 'HealthGuard Insurance'),
    ('POL-003', 'PAT-003', 'HG-2026-0003', 'active',    '2026-06-01', '2028-06-01', 'premium',       250000.00, 'HealthGuard Insurance'),
    ('POL-004', 'PAT-004', 'HG-2026-0004', 'suspended', '2026-03-01', '2028-03-01', 'comprehensive', 150000.00, 'HealthGuard Insurance'),
    ('POL-005', 'PAT-005', 'HG-2026-0005', 'active',    '2026-03-01', '2028-03-01', 'comprehensive', 150000.00, 'HealthGuard Insurance'),
    ('POL-006', 'PAT-006', 'HG-2026-0006', 'active',    '2026-09-01', '2028-09-01', 'basic',          75000.00, 'HealthGuard Insurance'),
    ('POL-007', 'PAT-007', 'HG-2026-0007', 'cancelled', '2026-01-01', '2028-01-01', 'premium',       300000.00, 'HealthGuard Insurance'),
    ('POL-008', 'PAT-008', 'HG-2026-0008', 'active',    '2026-01-01', '2029-01-01', 'premium',       250000.00, 'HealthGuard Insurance'),
    ('POL-009', 'PAT-009', 'HG-2026-0009', 'active',    '2026-02-01', '2028-02-01', 'comprehensive', 130000.00, 'HealthGuard Insurance'),
    ('POL-010', 'PAT-010', 'HG-2026-0010', 'active',    '2026-05-01', '2028-05-01', 'premium',       200000.00, 'HealthGuard Insurance'),
    ('POL-011', 'PAT-011', 'HG-2026-0011', 'active',    '2026-07-01', '2028-07-01', 'basic',          60000.00, 'HealthGuard Insurance'),
    ('POL-012', 'PAT-012', 'HG-2026-0012', 'expired',   '2024-06-01', '2025-06-01', 'comprehensive', 140000.00, 'HealthGuard Insurance'),
    ('POL-013', 'PAT-013', 'HG-2026-0013', 'active',    '2026-04-01', '2028-04-01', 'comprehensive', 160000.00, 'HealthGuard Insurance'),
    ('POL-014', 'PAT-014', 'HG-2026-0014', 'active',    '2026-08-01', '2028-08-01', 'basic',          70000.00, 'HealthGuard Insurance')
ON CONFLICT (policy_id) DO NOTHING;
