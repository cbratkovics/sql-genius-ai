import type { SchemaTemplate } from './types';

export const saasSchema: SchemaTemplate = {
  id: 'saas',
  name: 'SaaS Analytics Platform',
  description: 'Multi-tenant SaaS application with subscriptions, usage metrics, and feature tracking',
  category: 'saas',
  difficulty: 'advanced',
  icon: '📊',

  tables: [
    {
      name: 'organizations',
      columns: [
        { name: 'org_id', type: 'INTEGER', primaryKey: true },
        { name: 'name', type: 'TEXT' },
        { name: 'plan', type: 'TEXT' },
        { name: 'created_at', type: 'DATETIME' },
        { name: 'mrr', type: 'DECIMAL' },
      ],
    },
    {
      name: 'users',
      columns: [
        { name: 'user_id', type: 'INTEGER', primaryKey: true },
        { name: 'org_id', type: 'INTEGER', foreignKey: { table: 'organizations', column: 'org_id' } },
        { name: 'email', type: 'TEXT' },
        { name: 'role', type: 'TEXT' },
        { name: 'last_login', type: 'DATETIME' },
      ],
    },
    {
      name: 'subscriptions',
      columns: [
        { name: 'subscription_id', type: 'INTEGER', primaryKey: true },
        { name: 'org_id', type: 'INTEGER', foreignKey: { table: 'organizations', column: 'org_id' } },
        { name: 'plan_name', type: 'TEXT' },
        { name: 'status', type: 'TEXT' },
        { name: 'started_at', type: 'DATETIME' },
        { name: 'monthly_price', type: 'DECIMAL' },
      ],
    },
    {
      name: 'usage_events',
      columns: [
        { name: 'event_id', type: 'INTEGER', primaryKey: true },
        { name: 'user_id', type: 'INTEGER', foreignKey: { table: 'users', column: 'user_id' } },
        { name: 'event_type', type: 'TEXT' },
        { name: 'feature_name', type: 'TEXT' },
        { name: 'timestamp', type: 'DATETIME' },
        { name: 'metadata', type: 'TEXT' },
      ],
    },
    {
      name: 'features',
      columns: [
        { name: 'feature_id', type: 'INTEGER', primaryKey: true },
        { name: 'name', type: 'TEXT' },
        { name: 'plan_required', type: 'TEXT' },
        { name: 'usage_count', type: 'INTEGER' },
      ],
    },
  ],

  sampleData: {
    organizations: [
      { org_id: 1, name: 'Acme Corp', plan: 'enterprise', created_at: '2023-06-15', mrr: 999.00 },
      { org_id: 2, name: 'TechStart Inc', plan: 'pro', created_at: '2024-01-20', mrr: 299.00 },
      { org_id: 3, name: 'DataFlow LLC', plan: 'basic', created_at: '2024-03-10', mrr: 99.00 },
      { org_id: 4, name: 'CloudSync Co', plan: 'enterprise', created_at: '2023-11-05', mrr: 1499.00 },
      { org_id: 5, name: 'DevTools Hub', plan: 'pro', created_at: '2024-02-28', mrr: 299.00 },
    ],

    users: [
      { user_id: 1, org_id: 1, email: 'john@acme.com', role: 'admin', last_login: '2024-06-20' },
      { user_id: 2, org_id: 1, email: 'jane@acme.com', role: 'member', last_login: '2024-06-19' },
      { user_id: 3, org_id: 2, email: 'mike@techstart.com', role: 'admin', last_login: '2024-06-20' },
      { user_id: 4, org_id: 3, email: 'sarah@dataflow.com', role: 'admin', last_login: '2024-06-18' },
      { user_id: 5, org_id: 4, email: 'alex@cloudsync.com', role: 'admin', last_login: '2024-06-20' },
      { user_id: 6, org_id: 4, email: 'emma@cloudsync.com', role: 'member', last_login: '2024-06-19' },
      { user_id: 7, org_id: 5, email: 'chris@devtools.com', role: 'admin', last_login: '2024-06-17' },
    ],

    subscriptions: [
      { subscription_id: 1, org_id: 1, plan_name: 'Enterprise', status: 'active', started_at: '2023-06-15', monthly_price: 999.00 },
      { subscription_id: 2, org_id: 2, plan_name: 'Pro', status: 'active', started_at: '2024-01-20', monthly_price: 299.00 },
      { subscription_id: 3, org_id: 3, plan_name: 'Basic', status: 'active', started_at: '2024-03-10', monthly_price: 99.00 },
      { subscription_id: 4, org_id: 4, plan_name: 'Enterprise', status: 'active', started_at: '2023-11-05', monthly_price: 1499.00 },
      { subscription_id: 5, org_id: 5, plan_name: 'Pro', status: 'trialing', started_at: '2024-02-28', monthly_price: 299.00 },
    ],

    usage_events: [
      { event_id: 1, user_id: 1, event_type: 'api_call', feature_name: 'advanced_analytics', timestamp: '2024-06-20 10:30:00', metadata: '{"endpoint": "/api/reports"}' },
      { event_id: 2, user_id: 2, event_type: 'export', feature_name: 'data_export', timestamp: '2024-06-20 11:15:00', metadata: '{"format": "csv"}' },
      { event_id: 3, user_id: 3, event_type: 'api_call', feature_name: 'basic_analytics', timestamp: '2024-06-20 12:00:00', metadata: '{"endpoint": "/api/stats"}' },
      { event_id: 4, user_id: 1, event_type: 'api_call', feature_name: 'advanced_analytics', timestamp: '2024-06-20 14:22:00', metadata: '{"endpoint": "/api/dashboards"}' },
      { event_id: 5, user_id: 5, event_type: 'integration', feature_name: 'slack_integration', timestamp: '2024-06-20 15:45:00', metadata: '{"action": "connect"}' },
    ],

    features: [
      { feature_id: 1, name: 'advanced_analytics', plan_required: 'pro', usage_count: 1245 },
      { feature_id: 2, name: 'data_export', plan_required: 'basic', usage_count: 892 },
      { feature_id: 3, name: 'slack_integration', plan_required: 'enterprise', usage_count: 456 },
      { feature_id: 4, name: 'api_access', plan_required: 'pro', usage_count: 3421 },
      { feature_id: 5, name: 'custom_reports', plan_required: 'enterprise', usage_count: 234 },
    ],
  },

  relationships: [
    { from: { table: 'users', column: 'org_id' }, to: { table: 'organizations', column: 'org_id' }, type: 'many-to-many' },
    { from: { table: 'subscriptions', column: 'org_id' }, to: { table: 'organizations', column: 'org_id' }, type: 'one-to-one' },
    { from: { table: 'usage_events', column: 'user_id' }, to: { table: 'users', column: 'user_id' }, type: 'many-to-many' },
  ],

  ddl: `
CREATE TABLE organizations (
  org_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  plan TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  mrr DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL,
  email TEXT NOT NULL UNIQUE,
  role TEXT DEFAULT 'member',
  last_login DATETIME,
  FOREIGN KEY (org_id) REFERENCES organizations(org_id)
);

CREATE TABLE subscriptions (
  subscription_id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL,
  plan_name TEXT NOT NULL,
  status TEXT DEFAULT 'trialing',
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  monthly_price DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (org_id) REFERENCES organizations(org_id)
);

CREATE TABLE usage_events (
  event_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  feature_name TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE features (
  feature_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  plan_required TEXT NOT NULL,
  usage_count INTEGER DEFAULT 0
);
  `.trim(),
};
