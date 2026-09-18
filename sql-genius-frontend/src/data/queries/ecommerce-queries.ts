import type { SampleQuery } from './types';

export const ecommerceQueries: SampleQuery[] = [
  // Basic Queries
  {
    id: 'ecom-001',
    schemaId: 'ecommerce',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show me all products',
    sql: 'SELECT * FROM products;',
    description: 'Retrieve all products from the catalog',
    explanation: 'Simple SELECT * query to fetch all columns from the products table',
    tags: ['select', 'products'],
  },
  {
    id: 'ecom-002',
    schemaId: 'ecommerce',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show me all customers',
    sql: 'SELECT customer_id, first_name, last_name, email FROM customers;',
    description: 'List all customers with their basic information',
    explanation: 'Selecting specific columns from the customers table',
    tags: ['select', 'customers'],
  },
  {
    id: 'ecom-003',
    schemaId: 'ecommerce',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Find products in the Electronics category',
    sql: "SELECT * FROM products WHERE category = 'Electronics';",
    description: 'Filter products by category',
    explanation: 'Using WHERE clause to filter results by category column',
    tags: ['where', 'filter', 'products'],
  },
  {
    id: 'ecom-004',
    schemaId: 'ecommerce',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'List products sorted by price from highest to lowest',
    sql: 'SELECT name, price FROM products ORDER BY price DESC;',
    description: 'Sort products by price in descending order',
    explanation: 'ORDER BY clause sorts results by price in descending (DESC) order',
    tags: ['order by', 'sorting', 'products'],
  },
  {
    id: 'ecom-005',
    schemaId: 'ecommerce',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show me the 5 most expensive products',
    sql: 'SELECT name, price FROM products ORDER BY price DESC LIMIT 5;',
    description: 'Get top 5 products by price',
    explanation: 'Combining ORDER BY with LIMIT to get top N results',
    tags: ['limit', 'top n', 'products'],
  },

  // Intermediate Queries
  {
    id: 'ecom-006',
    schemaId: 'ecommerce',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show me total revenue by product category',
    sql: `SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;`,
    description: 'Calculate total revenue grouped by product category',
    explanation: 'Uses JOIN to combine products and order_items, then aggregates with SUM and GROUP BY',
    tags: ['join', 'group by', 'aggregation', 'revenue'],
  },
  {
    id: 'ecom-007',
    schemaId: 'ecommerce',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Find customers who spent more than $1000',
    sql: 'SELECT customer_id, first_name, last_name, total_spent FROM customers WHERE total_spent > 1000 ORDER BY total_spent DESC;',
    description: 'Filter high-value customers',
    explanation: 'WHERE clause with numeric comparison to find customers above spending threshold',
    tags: ['where', 'comparison', 'customers'],
  },
  {
    id: 'ecom-008',
    schemaId: 'ecommerce',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show average order value by customer',
    sql: `SELECT c.customer_id, c.first_name, c.last_name, AVG(o.total_amount) AS avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY avg_order_value DESC;`,
    description: 'Calculate average order value per customer',
    explanation: 'JOIN customers with orders, use AVG aggregation with GROUP BY',
    tags: ['join', 'avg', 'aggregation', 'customers'],
  },
  {
    id: 'ecom-009',
    schemaId: 'ecommerce',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'List products with their review counts and average ratings',
    sql: `SELECT p.product_id, p.name, COUNT(r.review_id) AS review_count,
       ROUND(AVG(r.rating), 2) AS avg_rating
FROM products p
LEFT JOIN reviews r ON p.product_id = r.product_id
GROUP BY p.product_id, p.name
ORDER BY avg_rating DESC;`,
    description: 'Product ratings summary',
    explanation: 'LEFT JOIN ensures all products appear even without reviews, aggregates count and average',
    tags: ['left join', 'count', 'avg', 'reviews'],
  },
  {
    id: 'ecom-010',
    schemaId: 'ecommerce',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Find orders with more than 2 physical units',
    sql: `SELECT o.order_id, o.customer_id, COUNT(oi.order_item_id) AS line_count, SUM(oi.quantity) AS unit_count, o.total_amount
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.customer_id, o.total_amount
HAVING SUM(oi.quantity) > 2;`,
    description: 'Filter orders by physical unit count',
    explanation: 'SUM(quantity) counts physical units; COUNT(order_item_id) separately reports product lines.',
    tags: ['having', 'group by', 'units', 'order lines'],
  },

  // Advanced Queries
  {
    id: 'ecom-011',
    schemaId: 'ecommerce',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Show observed order value by customer over the fixture period',
    sql: `SELECT c.customer_id, c.first_name, c.last_name,
       COUNT(o.order_id) AS total_orders,
       SUM(o.total_amount) AS observed_order_value,
       ROUND(AVG(o.total_amount), 2) AS avg_order_value,
       MIN(o.order_date) AS first_order,
       MAX(o.order_date) AS last_order
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY observed_order_value DESC;`,
    description: 'Observed order value over fixture coverage',
    explanation: 'Aggregates order headers in the fixture; this is neither predicted lifetime value nor the customers.total_spent snapshot.',
    tags: ['aggregation', 'customer analytics', 'multiple functions'],
    contract: {
      metricId: 'observed-order-value', version: '1.0.0',
      supportedDecision: 'Prioritize customer records for review under observed fixture value.',
      inputGrain: 'One order header', outputGrain: 'One customer', sources: ['customers', 'orders'],
      formula: 'SUM(orders.total_amount)', unit: 'currency amount',
      population: 'All order statuses in the 2024-06-01 through 2024-06-15 fixture',
      analysisDate: '2024-06-15',
      limitations: ['Not predicted lifetime value', 'Does not use the separate customers.total_spent snapshot'],
      evidenceChecks: ['Order IDs are unique', 'Each order references one customer', 'Order totals are aggregated before any child-row join'],
    },
  },
  {
    id: 'ecom-012',
    schemaId: 'ecommerce',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Find products that have never been ordered',
    sql: `SELECT p.product_id, p.name, p.category, p.price
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.product_id IS NULL;`,
    description: 'Identify products with zero sales',
    explanation: 'LEFT JOIN with WHERE IS NULL finds products without matching order_items records',
    tags: ['left join', 'null check', 'inventory'],
  },
  {
    id: 'ecom-013',
    schemaId: 'ecommerce',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Show monthly sales trends',
    sql: `SELECT
  strftime('%Y-%m', order_date) AS month,
  COUNT(order_id) AS total_orders,
  SUM(total_amount) AS revenue,
  ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month DESC;`,
    description: 'Monthly sales performance metrics',
    explanation: 'Uses date function strftime to group by month, multiple aggregations for KPIs',
    tags: ['date functions', 'time series', 'analytics'],
  },
  {
    id: 'ecom-014',
    schemaId: 'ecommerce',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Rank products by gross line-item sales amount',
    sql: `SELECT p.product_id, p.name, p.category,
       COUNT(oi.order_item_id) AS order_line_count,
       COALESCE(SUM(oi.quantity), 0) AS units_sold,
       SUM(oi.quantity * oi.unit_price) AS total_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT oi.order_id), 2) AS revenue_per_order,
       RANK() OVER (PARTITION BY p.category ORDER BY SUM(oi.quantity * oi.unit_price) DESC) AS category_rank
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name, p.category
ORDER BY total_revenue DESC;`,
    description: 'Product sales amount and unit performance with category ranking',
    explanation: 'Ranks gross line-item sales amount. Profit cannot be calculated because no cost data exists; units use SUM(quantity), not line count.',
    tags: ['window functions', 'rank', 'sales amount', 'units'],
  },
  {
    id: 'ecom-015',
    schemaId: 'ecommerce',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Find customer purchase patterns and repeat buyers',
    sql: `SELECT c.customer_id, c.first_name, c.last_name,
       COUNT(o.order_id) AS order_count,
       SUM(o.total_amount) AS total_spent,
       CASE
         WHEN COUNT(o.order_id) >= 5 THEN 'VIP'
         WHEN COUNT(o.order_id) >= 3 THEN 'Regular'
         WHEN COUNT(o.order_id) >= 1 THEN 'Occasional'
         ELSE 'Never Purchased'
       END AS customer_segment
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY order_count DESC;`,
    description: 'Customer segmentation based on purchase frequency',
    explanation: 'CASE statement creates customer segments based on order count',
    tags: ['case when', 'segmentation', 'customer analysis'],
  },
];
