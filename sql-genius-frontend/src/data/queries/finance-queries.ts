import type { SampleQuery } from './types';

export const financeQueries: SampleQuery[] = [
  {
    id: 'fin-001',
    schemaId: 'finance',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show all customer accounts',
    sql: 'SELECT * FROM accounts WHERE status = "active";',
    description: 'List active accounts',
    explanation: 'Simple WHERE filter on status column',
    tags: ['select', 'accounts', 'filter'],
  },
  {
    id: 'fin-002',
    schemaId: 'finance',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Find accounts with balance over $10,000',
    sql: 'SELECT * FROM accounts WHERE balance > 10000 ORDER BY balance DESC;',
    description: 'High-value accounts',
    explanation: 'Numeric comparison with ORDER BY',
    tags: ['where', 'comparison', 'sorting'],
  },
  {
    id: 'fin-003',
    schemaId: 'finance',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Calculate total assets by customer',
    sql: `SELECT c.customer_id, c.first_name, c.last_name, c.email,
       COUNT(a.account_id) AS account_count,
       SUM(a.balance) AS total_balance
FROM customers c
LEFT JOIN accounts a ON c.customer_id = a.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY total_balance DESC;`,
    description: 'Customer wealth analysis',
    explanation: 'JOIN with SUM aggregation for total balance',
    tags: ['join', 'sum', 'customer assets'],
  },
  {
    id: 'fin-004',
    schemaId: 'finance',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show daily transaction volume',
    sql: `SELECT DATE(timestamp) AS transaction_date,
       COUNT(*) AS transaction_count,
       SUM(amount) AS total_volume,
       AVG(amount) AS avg_amount
FROM transactions
WHERE status = 'completed'
GROUP BY DATE(timestamp)
ORDER BY transaction_date DESC;`,
    description: 'Daily transaction metrics',
    explanation: 'Date grouping with multiple aggregations',
    tags: ['date functions', 'aggregation', 'transactions'],
  },
  {
    id: 'fin-005',
    schemaId: 'finance',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Detect unusual transaction patterns',
    sql: `WITH avg_transaction AS (
  SELECT from_account_id, AVG(amount) AS avg_amount
  FROM transactions
  WHERE status = 'completed'
  GROUP BY from_account_id
)
SELECT t.transaction_id, t.from_account_id, t.amount, at.avg_amount,
       ROUND(t.amount / at.avg_amount, 2) AS amount_ratio
FROM transactions t
JOIN avg_transaction at ON t.from_account_id = at.from_account_id
WHERE t.amount > at.avg_amount * 3
ORDER BY amount_ratio DESC;`,
    description: 'Anomaly detection for transactions',
    explanation: 'CTE calculates averages, main query finds outliers',
    tags: ['cte', 'anomaly detection', 'fraud'],
  },
  {
    id: 'fin-006',
    schemaId: 'finance',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Calculate customer risk score',
    sql: `SELECT c.customer_id, c.first_name, c.last_name,
       c.kyc_verified,
       COUNT(DISTINCT a.account_id) AS account_count,
       SUM(a.balance) AS total_balance,
       COUNT(DISTINCT t.transaction_id) AS transaction_count,
       COUNT(DISTINCT CASE WHEN fa.alert_id IS NOT NULL THEN t.transaction_id END) AS flagged_transactions,
       CASE
         WHEN c.kyc_verified = 0 THEN 'High Risk'
         WHEN COUNT(DISTINCT CASE WHEN fa.alert_id IS NOT NULL THEN t.transaction_id END) > 0 THEN 'Medium Risk'
         ELSE 'Low Risk'
       END AS risk_category
FROM customers c
LEFT JOIN accounts a ON c.customer_id = a.customer_id
LEFT JOIN transactions t ON a.account_id = t.from_account_id
LEFT JOIN fraud_alerts fa ON t.transaction_id = fa.transaction_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.kyc_verified
ORDER BY
  CASE risk_category
    WHEN 'High Risk' THEN 1
    WHEN 'Medium Risk' THEN 2
    ELSE 3
  END;`,
    description: 'Comprehensive risk assessment',
    explanation: 'Complex CASE logic creates risk scores from multiple factors',
    tags: ['risk scoring', 'kyc', 'fraud prevention'],
  },
  {
    id: 'fin-007',
    schemaId: 'finance',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Show account balance trends',
    sql: `SELECT a.account_id, c.first_name || ' ' || c.last_name AS customer_name,
       a.balance AS current_balance,
       COALESCE(SUM(CASE WHEN t.to_account_id = a.account_id THEN t.amount ELSE 0 END), 0) AS total_incoming,
       COALESCE(SUM(CASE WHEN t.from_account_id = a.account_id THEN t.amount ELSE 0 END), 0) AS total_outgoing,
       COALESCE(SUM(CASE WHEN t.to_account_id = a.account_id THEN t.amount ELSE 0 END), 0) -
       COALESCE(SUM(CASE WHEN t.from_account_id = a.account_id THEN t.amount ELSE 0 END), 0) AS net_flow
FROM accounts a
JOIN customers c ON a.customer_id = c.customer_id
LEFT JOIN transactions t ON a.account_id = t.from_account_id OR a.account_id = t.to_account_id
WHERE t.status = 'completed' OR t.status IS NULL
GROUP BY a.account_id, c.first_name, c.last_name, a.balance
ORDER BY net_flow DESC;`,
    description: 'Account cash flow analysis',
    explanation: 'Complex CASE statements calculate incoming/outgoing flows',
    tags: ['cash flow', 'balance analysis', 'conditional aggregation'],
  },
  {
    id: 'fin-008',
    schemaId: 'finance',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Generate fraud alert summary report',
    sql: `SELECT fa.alert_type,
       COUNT(*) AS alert_count,
       SUM(CASE WHEN fa.reviewed = 1 THEN 1 ELSE 0 END) AS reviewed_count,
       ROUND(AVG(fa.risk_score), 3) AS avg_risk_score,
       SUM(t.amount) AS total_flagged_amount
FROM fraud_alerts fa
JOIN transactions t ON fa.transaction_id = t.transaction_id
GROUP BY fa.alert_type
ORDER BY alert_count DESC;`,
    description: 'Fraud monitoring dashboard',
    explanation: 'Aggregates fraud alerts by type with review status',
    tags: ['fraud alerts', 'monitoring', 'dashboard'],
  },
];
