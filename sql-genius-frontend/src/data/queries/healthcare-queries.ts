import type { SampleQuery } from './types';

export const healthcareQueries: SampleQuery[] = [
  {
    id: 'health-001',
    schemaId: 'healthcare',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show all patients',
    sql: 'SELECT * FROM patients ORDER BY last_name, first_name;',
    description: 'List all patients alphabetically',
    explanation: 'SELECT with ORDER BY multiple columns',
    tags: ['select', 'patients', 'order by'],
  },
  {
    id: 'health-002',
    schemaId: 'healthcare',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Find all doctors in Cardiology',
    sql: "SELECT d.* FROM doctors d JOIN departments dep ON d.department_id = dep.department_id WHERE dep.name = 'Cardiology';",
    description: 'Filter doctors by department',
    explanation: 'JOIN with WHERE clause to filter by department name',
    tags: ['join', 'where', 'doctors'],
  },
  {
    id: 'health-003',
    schemaId: 'healthcare',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show upcoming appointments',
    sql: `SELECT a.appointment_date, p.first_name || ' ' || p.last_name AS patient_name,
       d.first_name || ' ' || d.last_name AS doctor_name, a.status
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN doctors d ON a.doctor_id = d.doctor_id
WHERE a.status = 'scheduled'
ORDER BY a.appointment_date;`,
    description: 'List scheduled appointments',
    explanation: 'Multiple JOINs with string concatenation and filtering',
    tags: ['multiple joins', 'concatenation', 'appointments'],
  },
  {
    id: 'health-004',
    schemaId: 'healthcare',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Calculate doctor workload',
    sql: `SELECT d.doctor_id, d.first_name, d.last_name, d.specialization,
       COUNT(a.appointment_id) AS total_appointments,
       SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN a.status = 'scheduled' THEN 1 ELSE 0 END) AS upcoming
FROM doctors d
LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
GROUP BY d.doctor_id, d.first_name, d.last_name, d.specialization
ORDER BY total_appointments DESC;`,
    description: 'Doctor appointment statistics',
    explanation: 'CASE statements within SUM for conditional counting',
    tags: ['case when', 'conditional aggregation', 'workload'],
  },
  {
    id: 'health-005',
    schemaId: 'healthcare',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Find most prescribed medications',
    sql: `SELECT pr.medication, COUNT(*) AS prescription_count,
       COUNT(DISTINCT a.doctor_id) AS prescribing_doctors,
       COUNT(DISTINCT a.patient_id) AS unique_patients
FROM prescriptions pr
JOIN appointments a ON pr.appointment_id = a.appointment_id
GROUP BY pr.medication
ORDER BY prescription_count DESC
LIMIT 10;`,
    description: 'Top 10 most prescribed medications',
    explanation: 'Multiple COUNT DISTINCT aggregations',
    tags: ['count distinct', 'prescriptions', 'top n'],
  },
  {
    id: 'health-006',
    schemaId: 'healthcare',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Analyze patient visit frequency',
    sql: `SELECT p.patient_id, p.first_name, p.last_name,
       COUNT(a.appointment_id) AS visit_count,
       MIN(a.appointment_date) AS first_visit,
       MAX(a.appointment_date) AS last_visit,
       ROUND(julianday(MAX(a.appointment_date)) - julianday(MIN(a.appointment_date)), 0) AS days_between_first_last
FROM patients p
LEFT JOIN appointments a ON p.patient_id = a.patient_id
GROUP BY p.patient_id, p.first_name, p.last_name
HAVING visit_count > 0
ORDER BY visit_count DESC;`,
    description: 'Patient engagement metrics',
    explanation: 'Date calculations to analyze patient visit patterns',
    tags: ['patient analytics', 'date functions', 'engagement'],
  },
  {
    id: 'health-007',
    schemaId: 'healthcare',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show department capacity utilization',
    sql: `SELECT dep.name AS department, dep.floor,
       COUNT(d.doctor_id) AS doctor_count,
       COUNT(a.appointment_id) AS total_appointments
FROM departments dep
LEFT JOIN doctors d ON dep.department_id = d.department_id
LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
GROUP BY dep.department_id, dep.name, dep.floor
ORDER BY total_appointments DESC;`,
    description: 'Department resource analysis',
    explanation: 'Multiple LEFT JOINs to include departments without doctors/appointments',
    tags: ['capacity planning', 'departments', 'resources'],
  },
  {
    id: 'health-008',
    schemaId: 'healthcare',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Find patients with multiple prescriptions',
    sql: `SELECT p.patient_id, p.first_name, p.last_name,
       GROUP_CONCAT(DISTINCT pr.medication, ', ') AS medications,
       COUNT(DISTINCT pr.prescription_id) AS prescription_count
FROM patients p
JOIN appointments a ON p.patient_id = a.patient_id
JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
GROUP BY p.patient_id, p.first_name, p.last_name
HAVING prescription_count > 1
ORDER BY prescription_count DESC;`,
    description: 'Polypharmacy analysis',
    explanation: 'GROUP_CONCAT to aggregate medication names into single column',
    tags: ['group_concat', 'having', 'polypharmacy'],
  },
];
