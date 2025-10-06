import type { SchemaTemplate } from './types';

export const financeSchema: SchemaTemplate = {
  id: 'finance',
  name: 'Financial Services',
  description: 'Banking system with accounts, transactions, customers, and fraud detection',
  category: 'finance',
  difficulty: 'advanced',
  icon: '💰',

  tables: [
    {
      name: 'customers',
      columns: [
        { name: 'customer_id', type: 'INTEGER', primaryKey: true },
        { name: 'first_name', type: 'TEXT' },
        { name: 'last_name', type: 'TEXT' },
        { name: 'email', type: 'TEXT' },
        { name: 'kyc_verified', type: 'BOOLEAN' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
    {
      name: 'accounts',
      columns: [
        { name: 'account_id', type: 'INTEGER', primaryKey: true },
        { name: 'customer_id', type: 'INTEGER', foreignKey: { table: 'customers', column: 'customer_id' } },
        { name: 'account_type', type: 'TEXT' },
        { name: 'balance', type: 'DECIMAL' },
        { name: 'currency', type: 'TEXT' },
        { name: 'status', type: 'TEXT' },
      ],
    },
    {
      name: 'transactions',
      columns: [
        { name: 'transaction_id', type: 'INTEGER', primaryKey: true },
        { name: 'from_account_id', type: 'INTEGER', foreignKey: { table: 'accounts', column: 'account_id' } },
        { name: 'to_account_id', type: 'INTEGER', foreignKey: { table: 'accounts', column: 'account_id' } },
        { name: 'amount', type: 'DECIMAL' },
        { name: 'transaction_type', type: 'TEXT' },
        { name: 'timestamp', type: 'DATETIME' },
        { name: 'status', type: 'TEXT' },
      ],
    },
    {
      name: 'cards',
      columns: [
        { name: 'card_id', type: 'INTEGER', primaryKey: true },
        { name: 'account_id', type: 'INTEGER', foreignKey: { table: 'accounts', column: 'account_id' } },
        { name: 'card_number', type: 'TEXT' },
        { name: 'card_type', type: 'TEXT' },
        { name: 'expiry_date', type: 'DATE' },
        { name: 'status', type: 'TEXT' },
      ],
    },
    {
      name: 'fraud_alerts',
      columns: [
        { name: 'alert_id', type: 'INTEGER', primaryKey: true },
        { name: 'transaction_id', type: 'INTEGER', foreignKey: { table: 'transactions', column: 'transaction_id' } },
        { name: 'risk_score', type: 'DECIMAL' },
        { name: 'alert_type', type: 'TEXT' },
        { name: 'reviewed', type: 'BOOLEAN' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
  ],

  sampleData: {
    customers: [
      { customer_id: 1, first_name: 'Alice', last_name: 'Johnson', email: 'alice.j@email.com', kyc_verified: 1, created_at: '2023-01-15' },
      { customer_id: 2, first_name: 'Bob', last_name: 'Williams', email: 'bob.w@email.com', kyc_verified: 1, created_at: '2023-03-22' },
      { customer_id: 3, first_name: 'Carol', last_name: 'Martinez', email: 'carol.m@email.com', kyc_verified: 1, created_at: '2023-06-10' },
      { customer_id: 4, first_name: 'David', last_name: 'Brown', email: 'david.b@email.com', kyc_verified: 0, created_at: '2024-01-08' },
      { customer_id: 5, first_name: 'Emma', last_name: 'Davis', email: 'emma.d@email.com', kyc_verified: 1, created_at: '2024-02-14' },
    ],

    accounts: [
      { account_id: 1, customer_id: 1, account_type: 'checking', balance: 5420.75, currency: 'USD', status: 'active' },
      { account_id: 2, customer_id: 1, account_type: 'savings', balance: 25000.00, currency: 'USD', status: 'active' },
      { account_id: 3, customer_id: 2, account_type: 'checking', balance: 1250.30, currency: 'USD', status: 'active' },
      { account_id: 4, customer_id: 3, account_type: 'checking', balance: 8900.50, currency: 'USD', status: 'active' },
      { account_id: 5, customer_id: 4, account_type: 'checking', balance: 320.00, currency: 'USD', status: 'frozen' },
      { account_id: 6, customer_id: 5, account_type: 'savings', balance: 15600.00, currency: 'USD', status: 'active' },
    ],

    transactions: [
      { transaction_id: 1, from_account_id: 1, to_account_id: 3, amount: 150.00, transaction_type: 'transfer', timestamp: '2024-06-15 09:30:00', status: 'completed' },
      { transaction_id: 2, from_account_id: 2, to_account_id: 1, amount: 500.00, transaction_type: 'transfer', timestamp: '2024-06-16 14:22:00', status: 'completed' },
      { transaction_id: 3, from_account_id: 3, to_account_id: 4, amount: 75.50, transaction_type: 'transfer', timestamp: '2024-06-17 11:15:00', status: 'completed' },
      { transaction_id: 4, from_account_id: 1, to_account_id: null, amount: 45.99, transaction_type: 'debit_card', timestamp: '2024-06-18 16:45:00', status: 'completed' },
      { transaction_id: 5, from_account_id: 4, to_account_id: null, amount: 2500.00, transaction_type: 'withdrawal', timestamp: '2024-06-19 10:00:00', status: 'pending' },
      { transaction_id: 6, from_account_id: 5, to_account_id: 1, amount: 10000.00, transaction_type: 'transfer', timestamp: '2024-06-19 22:30:00', status: 'flagged' },
    ],

    cards: [
      { card_id: 1, account_id: 1, card_number: '**** **** **** 1234', card_type: 'debit', expiry_date: '2026-12-31', status: 'active' },
      { card_id: 2, account_id: 2, card_number: '**** **** **** 5678', card_type: 'debit', expiry_date: '2027-06-30', status: 'active' },
      { card_id: 3, account_id: 3, card_number: '**** **** **** 9012', card_type: 'debit', expiry_date: '2025-03-31', status: 'active' },
      { card_id: 4, account_id: 4, card_number: '**** **** **** 3456', card_type: 'debit', expiry_date: '2026-09-30', status: 'active' },
      { card_id: 5, account_id: 5, card_number: '**** **** **** 7890', card_type: 'debit', expiry_date: '2024-11-30', status: 'blocked' },
    ],

    fraud_alerts: [
      { alert_id: 1, transaction_id: 5, risk_score: 0.87, alert_type: 'unusual_amount', reviewed: 0, created_at: '2024-06-19 10:05:00' },
      { alert_id: 2, transaction_id: 6, risk_score: 0.95, alert_type: 'suspicious_timing', reviewed: 0, created_at: '2024-06-19 22:31:00' },
    ],
  },

  relationships: [
    { from: { table: 'accounts', column: 'customer_id' }, to: { table: 'customers', column: 'customer_id' }, type: 'many-to-many' },
    { from: { table: 'transactions', column: 'from_account_id' }, to: { table: 'accounts', column: 'account_id' }, type: 'many-to-many' },
    { from: { table: 'transactions', column: 'to_account_id' }, to: { table: 'accounts', column: 'account_id' }, type: 'many-to-many' },
    { from: { table: 'cards', column: 'account_id' }, to: { table: 'accounts', column: 'account_id' }, type: 'many-to-many' },
    { from: { table: 'fraud_alerts', column: 'transaction_id' }, to: { table: 'transactions', column: 'transaction_id' }, type: 'one-to-one' },
  ],

  ddl: `
CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  kyc_verified BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
  account_id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  account_type TEXT NOT NULL,
  balance DECIMAL(15,2) DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  status TEXT DEFAULT 'active',
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE transactions (
  transaction_id INTEGER PRIMARY KEY,
  from_account_id INTEGER,
  to_account_id INTEGER,
  amount DECIMAL(15,2) NOT NULL,
  transaction_type TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'pending',
  FOREIGN KEY (from_account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (to_account_id) REFERENCES accounts(account_id)
);

CREATE TABLE cards (
  card_id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  card_number TEXT NOT NULL,
  card_type TEXT NOT NULL,
  expiry_date DATE NOT NULL,
  status TEXT DEFAULT 'active',
  FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE fraud_alerts (
  alert_id INTEGER PRIMARY KEY,
  transaction_id INTEGER NOT NULL,
  risk_score DECIMAL(3,2) NOT NULL,
  alert_type TEXT NOT NULL,
  reviewed BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);
  `.trim(),
};
