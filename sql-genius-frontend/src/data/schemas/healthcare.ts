import type { SchemaTemplate } from './types';

export const healthcareSchema: SchemaTemplate = {
  id: 'healthcare',
  name: 'Healthcare System',
  description: 'Medical records system with patients, appointments, prescriptions, and doctors',
  category: 'healthcare',
  difficulty: 'intermediate',
  icon: '🏥',

  tables: [
    {
      name: 'patients',
      columns: [
        { name: 'patient_id', type: 'INTEGER', primaryKey: true },
        { name: 'first_name', type: 'TEXT' },
        { name: 'last_name', type: 'TEXT' },
        { name: 'date_of_birth', type: 'DATE' },
        { name: 'blood_type', type: 'TEXT' },
        { name: 'phone', type: 'TEXT' },
      ],
    },
    {
      name: 'doctors',
      columns: [
        { name: 'doctor_id', type: 'INTEGER', primaryKey: true },
        { name: 'first_name', type: 'TEXT' },
        { name: 'last_name', type: 'TEXT' },
        { name: 'specialization', type: 'TEXT' },
        { name: 'department_id', type: 'INTEGER' },
      ],
    },
    {
      name: 'departments',
      columns: [
        { name: 'department_id', type: 'INTEGER', primaryKey: true },
        { name: 'name', type: 'TEXT' },
        { name: 'floor', type: 'INTEGER' },
      ],
    },
    {
      name: 'appointments',
      columns: [
        { name: 'appointment_id', type: 'INTEGER', primaryKey: true },
        { name: 'patient_id', type: 'INTEGER', foreignKey: { table: 'patients', column: 'patient_id' } },
        { name: 'doctor_id', type: 'INTEGER', foreignKey: { table: 'doctors', column: 'doctor_id' } },
        { name: 'appointment_date', type: 'DATETIME' },
        { name: 'status', type: 'TEXT' },
        { name: 'notes', type: 'TEXT' },
      ],
    },
    {
      name: 'prescriptions',
      columns: [
        { name: 'prescription_id', type: 'INTEGER', primaryKey: true },
        { name: 'appointment_id', type: 'INTEGER', foreignKey: { table: 'appointments', column: 'appointment_id' } },
        { name: 'medication', type: 'TEXT' },
        { name: 'dosage', type: 'TEXT' },
        { name: 'duration_days', type: 'INTEGER' },
      ],
    },
  ],

  sampleData: {
    departments: [
      { department_id: 1, name: 'Cardiology', floor: 3 },
      { department_id: 2, name: 'Neurology', floor: 4 },
      { department_id: 3, name: 'Pediatrics', floor: 2 },
      { department_id: 4, name: 'Orthopedics', floor: 5 },
    ],

    patients: [
      { patient_id: 1, first_name: 'Emily', last_name: 'Chen', date_of_birth: '1985-03-15', blood_type: 'A+', phone: '555-0101' },
      { patient_id: 2, first_name: 'Michael', last_name: 'Rodriguez', date_of_birth: '1972-11-28', blood_type: 'O-', phone: '555-0102' },
      { patient_id: 3, first_name: 'Sarah', last_name: 'Anderson', date_of_birth: '1990-07-22', blood_type: 'B+', phone: '555-0103' },
      { patient_id: 4, first_name: 'James', last_name: 'Wilson', date_of_birth: '1965-02-10', blood_type: 'AB+', phone: '555-0104' },
      { patient_id: 5, first_name: 'Lisa', last_name: 'Thompson', date_of_birth: '2010-09-05', blood_type: 'A-', phone: '555-0105' },
    ],

    doctors: [
      { doctor_id: 1, first_name: 'Dr. Robert', last_name: 'Martinez', specialization: 'Cardiologist', department_id: 1 },
      { doctor_id: 2, first_name: 'Dr. Jennifer', last_name: 'Lee', specialization: 'Neurologist', department_id: 2 },
      { doctor_id: 3, first_name: 'Dr. David', last_name: 'Kim', specialization: 'Pediatrician', department_id: 3 },
      { doctor_id: 4, first_name: 'Dr. Susan', last_name: 'Patel', specialization: 'Orthopedic Surgeon', department_id: 4 },
    ],

    appointments: [
      { appointment_id: 1, patient_id: 1, doctor_id: 1, appointment_date: '2024-06-15 10:00:00', status: 'completed', notes: 'Annual checkup, blood pressure normal' },
      { appointment_id: 2, patient_id: 2, doctor_id: 2, appointment_date: '2024-06-18 14:30:00', status: 'completed', notes: 'Follow-up for migraines' },
      { appointment_id: 3, patient_id: 3, doctor_id: 1, appointment_date: '2024-06-20 09:00:00', status: 'scheduled', notes: null },
      { appointment_id: 4, patient_id: 4, doctor_id: 4, appointment_date: '2024-06-22 11:00:00', status: 'scheduled', notes: null },
      { appointment_id: 5, patient_id: 5, doctor_id: 3, appointment_date: '2024-06-16 15:00:00', status: 'completed', notes: 'Vaccination update' },
    ],

    prescriptions: [
      { prescription_id: 1, appointment_id: 1, medication: 'Lisinopril', dosage: '10mg daily', duration_days: 90 },
      { prescription_id: 2, appointment_id: 2, medication: 'Sumatriptan', dosage: '50mg as needed', duration_days: 30 },
      { prescription_id: 3, appointment_id: 2, medication: 'Propranolol', dosage: '20mg twice daily', duration_days: 60 },
      { prescription_id: 4, appointment_id: 5, medication: 'Amoxicillin', dosage: '250mg three times daily', duration_days: 10 },
    ],
  },

  relationships: [
    { from: { table: 'appointments', column: 'patient_id' }, to: { table: 'patients', column: 'patient_id' }, type: 'many-to-many' },
    { from: { table: 'appointments', column: 'doctor_id' }, to: { table: 'doctors', column: 'doctor_id' }, type: 'many-to-many' },
    { from: { table: 'doctors', column: 'department_id' }, to: { table: 'departments', column: 'department_id' }, type: 'many-to-many' },
    { from: { table: 'prescriptions', column: 'appointment_id' }, to: { table: 'appointments', column: 'appointment_id' }, type: 'many-to-many' },
  ],

  ddl: `
CREATE TABLE departments (
  department_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  floor INTEGER
);

CREATE TABLE patients (
  patient_id INTEGER PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  blood_type TEXT,
  phone TEXT
);

CREATE TABLE doctors (
  doctor_id INTEGER PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  specialization TEXT NOT NULL,
  department_id INTEGER,
  FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE appointments (
  appointment_id INTEGER PRIMARY KEY,
  patient_id INTEGER NOT NULL,
  doctor_id INTEGER NOT NULL,
  appointment_date DATETIME NOT NULL,
  status TEXT DEFAULT 'scheduled',
  notes TEXT,
  FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
  FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE prescriptions (
  prescription_id INTEGER PRIMARY KEY,
  appointment_id INTEGER NOT NULL,
  medication TEXT NOT NULL,
  dosage TEXT NOT NULL,
  duration_days INTEGER,
  FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);
  `.trim(),
};
