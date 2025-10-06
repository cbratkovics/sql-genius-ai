import type { SampleQuery } from './types';

export const socialQueries: SampleQuery[] = [
  {
    id: 'social-001',
    schemaId: 'social',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Show all users',
    sql: 'SELECT * FROM users ORDER BY follower_count DESC;',
    description: 'List users by follower count',
    explanation: 'Simple SELECT with ORDER BY',
    tags: ['select', 'users', 'order by'],
  },
  {
    id: 'social-002',
    schemaId: 'social',
    category: 'basic',
    difficulty: 'beginner',
    naturalLanguage: 'Find posts with more than 500 likes',
    sql: 'SELECT * FROM posts WHERE like_count > 500 ORDER BY like_count DESC;',
    description: 'Popular posts',
    explanation: 'WHERE clause with numeric comparison',
    tags: ['where', 'filter', 'posts'],
  },
  {
    id: 'social-003',
    schemaId: 'social',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show user engagement metrics',
    sql: `SELECT u.user_id, u.username,
       COUNT(DISTINCT p.post_id) AS post_count,
       COUNT(DISTINCT c.comment_id) AS comment_count,
       COUNT(DISTINCT l.like_id) AS like_count,
       u.follower_count
FROM users u
LEFT JOIN posts p ON u.user_id = p.user_id
LEFT JOIN comments c ON u.user_id = c.user_id
LEFT JOIN likes l ON u.user_id = l.user_id
GROUP BY u.user_id, u.username, u.follower_count
ORDER BY (COUNT(DISTINCT p.post_id) + COUNT(DISTINCT c.comment_id)) DESC;`,
    description: 'User activity summary',
    explanation: 'Multiple LEFT JOINs with COUNT DISTINCT aggregations',
    tags: ['multiple joins', 'engagement', 'user metrics'],
  },
  {
    id: 'social-004',
    schemaId: 'social',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Find most commented posts',
    sql: `SELECT p.post_id, u.username AS author, p.content,
       COUNT(c.comment_id) AS comment_count,
       p.like_count
FROM posts p
JOIN users u ON p.user_id = u.user_id
LEFT JOIN comments c ON p.post_id = c.post_id
GROUP BY p.post_id, u.username, p.content, p.like_count
ORDER BY comment_count DESC
LIMIT 10;`,
    description: 'Top 10 most discussed posts',
    explanation: 'JOIN with GROUP BY and LIMIT for top N results',
    tags: ['join', 'group by', 'top n', 'engagement'],
  },
  {
    id: 'social-005',
    schemaId: 'social',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Calculate engagement rate for each post',
    sql: `SELECT p.post_id, u.username, p.content,
       p.like_count,
       COUNT(DISTINCT c.comment_id) AS comment_count,
       u.follower_count,
       ROUND(((p.like_count + COUNT(DISTINCT c.comment_id)) * 100.0 / u.follower_count), 2) AS engagement_rate
FROM posts p
JOIN users u ON p.user_id = u.user_id
LEFT JOIN comments c ON p.post_id = c.post_id
GROUP BY p.post_id, u.username, p.content, p.like_count, u.follower_count
ORDER BY engagement_rate DESC;`,
    description: 'Post performance analysis',
    explanation: 'Calculates engagement rate as percentage of follower base',
    tags: ['engagement rate', 'analytics', 'performance'],
  },
  {
    id: 'social-006',
    schemaId: 'social',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Find users with mutual follows',
    sql: `SELECT f1.follower_id AS user1_id, f1.following_id AS user2_id,
       u1.username AS user1_name, u2.username AS user2_name
FROM follows f1
JOIN follows f2 ON f1.follower_id = f2.following_id AND f1.following_id = f2.follower_id
JOIN users u1 ON f1.follower_id = u1.user_id
JOIN users u2 ON f1.following_id = u2.user_id
WHERE f1.follower_id < f1.following_id
ORDER BY u1.username;`,
    description: 'Mutual following relationships',
    explanation: 'Self-JOIN on follows table to find bidirectional relationships',
    tags: ['self join', 'relationships', 'social graph'],
  },
  {
    id: 'social-007',
    schemaId: 'social',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Show user growth and activity trends',
    sql: `SELECT DATE(created_at) AS signup_date,
       COUNT(*) AS new_users,
       SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) AS cumulative_users
FROM users
GROUP BY DATE(created_at)
ORDER BY signup_date;`,
    description: 'User acquisition funnel',
    explanation: 'Window function SUM OVER for running total',
    tags: ['window functions', 'growth metrics', 'funnel'],
  },
  {
    id: 'social-008',
    schemaId: 'social',
    category: 'business_intelligence',
    difficulty: 'advanced',
    naturalLanguage: 'Identify top influencers',
    sql: `SELECT u.user_id, u.username, u.follower_count,
       COUNT(DISTINCT p.post_id) AS total_posts,
       AVG(p.like_count) AS avg_likes_per_post,
       SUM(p.like_count) AS total_likes,
       ROUND(SUM(p.like_count) * 1.0 / COUNT(DISTINCT p.post_id), 2) AS like_per_post_ratio
FROM users u
LEFT JOIN posts p ON u.user_id = p.user_id
GROUP BY u.user_id, u.username, u.follower_count
HAVING total_posts > 0
ORDER BY follower_count DESC, avg_likes_per_post DESC
LIMIT 10;`,
    description: 'Top influencer leaderboard',
    explanation: 'Multiple aggregations with HAVING to filter users with content',
    tags: ['influencers', 'leaderboard', 'content creators'],
  },
  {
    id: 'social-009',
    schemaId: 'social',
    category: 'advanced',
    difficulty: 'advanced',
    naturalLanguage: 'Find users who follow but never engage',
    sql: `SELECT u.user_id, u.username,
       COUNT(DISTINCT f.following_id) AS following_count,
       COUNT(DISTINCT l.like_id) AS like_count,
       COUNT(DISTINCT c.comment_id) AS comment_count
FROM users u
LEFT JOIN follows f ON u.user_id = f.follower_id
LEFT JOIN likes l ON u.user_id = l.user_id
LEFT JOIN comments c ON u.user_id = c.user_id
GROUP BY u.user_id, u.username
HAVING following_count > 0 AND like_count = 0 AND comment_count = 0
ORDER BY following_count DESC;`,
    description: 'Passive user identification',
    explanation: 'HAVING clause filters for specific engagement patterns',
    tags: ['user behavior', 'engagement analysis', 'passive users'],
  },
  {
    id: 'social-010',
    schemaId: 'social',
    category: 'intermediate',
    difficulty: 'intermediate',
    naturalLanguage: 'Show viral content candidates',
    sql: `SELECT p.post_id, u.username, SUBSTR(p.content, 1, 50) || '...' AS preview,
       p.like_count,
       COUNT(c.comment_id) AS comment_count,
       ROUND(julianday('now') - julianday(p.created_at), 1) AS days_old,
       ROUND((p.like_count + COUNT(c.comment_id)) / (julianday('now') - julianday(p.created_at) + 1), 2) AS virality_score
FROM posts p
JOIN users u ON p.user_id = u.user_id
LEFT JOIN comments c ON p.post_id = c.post_id
GROUP BY p.post_id, u.username, p.content, p.like_count, p.created_at
ORDER BY virality_score DESC
LIMIT 10;`,
    description: 'Trending content detection',
    explanation: 'Custom virality score based on engagement per day',
    tags: ['viral content', 'trending', 'content discovery'],
  },
];
