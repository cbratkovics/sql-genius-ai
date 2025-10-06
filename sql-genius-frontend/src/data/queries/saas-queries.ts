import type { SampleQuery } from './types';

export const saasQueries: SampleQuery[] = [
  {
    id: 'saas-001',
    schemaId: 'saas',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show all organizations',
    sql: 'SELECT * FROM organizations ORDER BY created_at DESC;',
    description: 'List all organizations',
    explanation: 'Simple SELECT with ORDER BY to show newest organizations first',
    tags: ['select', 'organizations'],
  },
  {
    id: 'saas-002',
    schemaId: 'saas',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Find all enterprise plan customers',
    sql: "SELECT * FROM organizations WHERE plan = 'enterprise';",
    description: 'Filter organizations by plan type',
    explanation: 'WHERE clause filters by plan column',
    tags: ['where', 'filter', 'plans'],
  },
  {
    id: 'saas-003',
    schemaId: 'saas',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Calculate total MRR by plan type',
    sql: `SELECT plan, COUNT(*) AS customer_count, SUM(mrr) AS total_mrr,
       ROUND(AVG(mrr), 2) AS avg_mrr
FROM organizations
GROUP BY plan
ORDER BY total_mrr DESC;`,
    description: 'Monthly recurring revenue by plan',
    explanation: 'Aggregates MRR metrics grouped by subscription plan',
    tags: ['group by', 'sum', 'mrr', 'revenue'],
  },
  {
    id: 'saas-004',
    schemaId: 'saas',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show user activity with last login dates',
    sql: `SELECT u.user_id, u.email, u.role, o.name AS org_name, u.last_login,
       julianday('now') - julianday(u.last_login) AS days_since_login
FROM users u
JOIN organizations o ON u.org_id = o.org_id
ORDER BY u.last_login DESC;`,
    description: 'User engagement tracking',
    explanation: 'Calculates days since last login using date functions',
    tags: ['join', 'date functions', 'user activity'],
  },
  {
    id: 'saas-005',
    schemaId: 'saas',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Find most used features by plan type',
    sql: `SELECT o.plan, ue.feature_name, COUNT(*) AS usage_count
FROM usage_events ue
JOIN users u ON ue.user_id = u.user_id
JOIN organizations o ON u.org_id = o.org_id
GROUP BY o.plan, ue.feature_name
ORDER BY o.plan, usage_count DESC;`,
    description: 'Feature usage analysis by plan',
    explanation: 'Multi-table JOIN with GROUP BY to analyze feature adoption',
    tags: ['multiple joins', 'feature usage', 'analytics'],
  },
  {
    id: 'saas-006',
    schemaId: 'saas',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Calculate customer churn risk score',
    sql: `SELECT o.org_id, o.name, o.plan, s.status,
       COUNT(DISTINCT u.user_id) AS user_count,
       MAX(u.last_login) AS most_recent_login,
       julianday('now') - julianday(MAX(u.last_login)) AS days_inactive,
       CASE
         WHEN s.status = 'trialing' AND julianday('now') - julianday(MAX(u.last_login)) > 7 THEN 'High Risk'
         WHEN julianday('now') - julianday(MAX(u.last_login)) > 14 THEN 'Medium Risk'
         ELSE 'Low Risk'
       END AS churn_risk
FROM organizations o
JOIN subscriptions s ON o.org_id = s.org_id
LEFT JOIN users u ON o.org_id = u.org_id
GROUP BY o.org_id, o.name, o.plan, s.status
ORDER BY days_inactive DESC;`,
    description: 'Churn prediction model',
    explanation: 'Complex CASE statement creates risk scores based on inactivity patterns',
    tags: ['churn analysis', 'case when', 'risk scoring'],
  },
  {
    id: 'saas-007',
    schemaId: 'saas',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Show feature adoption rate by organization size',
    sql: `WITH org_sizes AS (
  SELECT org_id,
         CASE
           WHEN COUNT(user_id) >= 10 THEN 'Large'
           WHEN COUNT(user_id) >= 5 THEN 'Medium'
           ELSE 'Small'
         END AS org_size
  FROM users
  GROUP BY org_id
)
SELECT os.org_size, ue.feature_name, COUNT(DISTINCT ue.user_id) AS unique_users
FROM usage_events ue
JOIN users u ON ue.user_id = u.user_id
JOIN org_sizes os ON u.org_id = os.org_id
GROUP BY os.org_size, ue.feature_name
ORDER BY os.org_size, unique_users DESC;`,
    description: 'Feature adoption by company size',
    explanation: 'Uses CTE (Common Table Expression) to categorize organizations, then analyzes feature usage',
    tags: ['cte', 'with clause', 'feature adoption'],
  },
  {
    id: 'saas-008',
    schemaId: 'saas',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Find inactive users who haven\'t logged in for 30 days',
    sql: `SELECT u.user_id, u.email, u.role, o.name AS org_name, u.last_login
FROM users u
JOIN organizations o ON u.org_id = o.org_id
WHERE julianday('now') - julianday(u.last_login) > 30
ORDER BY u.last_login ASC;`,
    description: 'Identify inactive users for re-engagement',
    explanation: 'Date calculation to find users beyond activity threshold',
    tags: ['date functions', 'user retention', 'filter'],
  },
  {
    id: 'saas-009',
    schemaId: 'saas',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Calculate API usage metrics per organization',
    sql: `SELECT o.org_id, o.name, o.plan,
       COUNT(ue.event_id) AS total_api_calls,
       COUNT(DISTINCT DATE(ue.timestamp)) AS active_days,
       ROUND(COUNT(ue.event_id) * 1.0 / COUNT(DISTINCT DATE(ue.timestamp)), 2) AS avg_calls_per_day
FROM organizations o
LEFT JOIN users u ON o.org_id = u.org_id
LEFT JOIN usage_events ue ON u.user_id = ue.user_id AND ue.event_type = 'api_call'
GROUP BY o.org_id, o.name, o.plan
ORDER BY total_api_calls DESC;`,
    description: 'API usage patterns by organization',
    explanation: 'Calculates usage intensity metrics with multiple aggregations',
    tags: ['api usage', 'metrics', 'aggregation'],
  },
  {
    id: 'saas-010',
    schemaId: 'saas',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Show subscription conversion funnel',
    sql: `SELECT s.status,
       COUNT(*) AS org_count,
       SUM(s.monthly_price) AS total_revenue,
       ROUND(AVG(s.monthly_price), 2) AS avg_price,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM subscriptions s
GROUP BY s.status
ORDER BY
  CASE s.status
    WHEN 'trialing' THEN 1
    WHEN 'active' THEN 2
    WHEN 'cancelled' THEN 3
  END;`,
    description: 'Subscription status funnel analysis',
    explanation: 'Window function calculates percentage distribution of subscription statuses',
    tags: ['window functions', 'funnel analysis', 'conversion'],
  },
];
