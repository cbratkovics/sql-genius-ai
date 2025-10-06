import type { SchemaTemplate } from './types';

export const socialSchema: SchemaTemplate = {
  id: 'social',
  name: 'Social Media Platform',
  description: 'Social network with users, posts, comments, likes, and follows',
  category: 'social',
  difficulty: 'intermediate',
  icon: '📱',

  tables: [
    {
      name: 'users',
      columns: [
        { name: 'user_id', type: 'INTEGER', primaryKey: true },
        { name: 'username', type: 'TEXT' },
        { name: 'email', type: 'TEXT' },
        { name: 'bio', type: 'TEXT' },
        { name: 'follower_count', type: 'INTEGER' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
    {
      name: 'posts',
      columns: [
        { name: 'post_id', type: 'INTEGER', primaryKey: true },
        { name: 'user_id', type: 'INTEGER', foreignKey: { table: 'users', column: 'user_id' } },
        { name: 'content', type: 'TEXT' },
        { name: 'media_url', type: 'TEXT', nullable: true },
        { name: 'like_count', type: 'INTEGER' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
    {
      name: 'comments',
      columns: [
        { name: 'comment_id', type: 'INTEGER', primaryKey: true },
        { name: 'post_id', type: 'INTEGER', foreignKey: { table: 'posts', column: 'post_id' } },
        { name: 'user_id', type: 'INTEGER', foreignKey: { table: 'users', column: 'user_id' } },
        { name: 'content', type: 'TEXT' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
    {
      name: 'likes',
      columns: [
        { name: 'like_id', type: 'INTEGER', primaryKey: true },
        { name: 'user_id', type: 'INTEGER', foreignKey: { table: 'users', column: 'user_id' } },
        { name: 'post_id', type: 'INTEGER', foreignKey: { table: 'posts', column: 'post_id' } },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
    {
      name: 'follows',
      columns: [
        { name: 'follow_id', type: 'INTEGER', primaryKey: true },
        { name: 'follower_id', type: 'INTEGER', foreignKey: { table: 'users', column: 'user_id' } },
        { name: 'following_id', type: 'INTEGER', foreignKey: { table: 'users', column: 'user_id' } },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
  ],

  sampleData: {
    users: [
      { user_id: 1, username: 'tech_guru', email: 'guru@social.com', bio: 'Tech enthusiast and developer', follower_count: 15420, created_at: '2023-01-10' },
      { user_id: 2, username: 'travel_addict', email: 'travel@social.com', bio: 'Exploring the world one city at a time', follower_count: 8920, created_at: '2023-03-15' },
      { user_id: 3, username: 'foodie_life', email: 'food@social.com', bio: 'Food blogger and chef', follower_count: 23100, created_at: '2023-02-20' },
      { user_id: 4, username: 'fitness_coach', email: 'fit@social.com', bio: 'Certified fitness trainer', follower_count: 12300, created_at: '2023-05-08' },
      { user_id: 5, username: 'art_creator', email: 'art@social.com', bio: 'Digital artist and illustrator', follower_count: 5670, created_at: '2023-08-12' },
    ],

    posts: [
      { post_id: 1, user_id: 1, content: 'Just deployed my first microservices architecture! 🚀', media_url: null, like_count: 234, created_at: '2024-06-15 10:30:00' },
      { post_id: 2, user_id: 2, content: 'Sunset in Santorini is absolutely breathtaking!', media_url: '/images/santorini.jpg', like_count: 892, created_at: '2024-06-16 18:45:00' },
      { post_id: 3, user_id: 3, content: 'New recipe alert: Homemade pasta carbonara 🍝', media_url: '/images/pasta.jpg', like_count: 1203, created_at: '2024-06-17 12:00:00' },
      { post_id: 4, user_id: 4, content: '5 exercises you can do at home with no equipment', media_url: '/videos/workout.mp4', like_count: 567, created_at: '2024-06-18 07:00:00' },
      { post_id: 5, user_id: 5, content: 'Work in progress: Digital portrait commission', media_url: '/images/portrait.jpg', like_count: 445, created_at: '2024-06-19 15:30:00' },
      { post_id: 6, user_id: 1, content: 'Anyone else excited about the new AI developments?', media_url: null, like_count: 178, created_at: '2024-06-20 09:15:00' },
    ],

    comments: [
      { comment_id: 1, post_id: 1, user_id: 3, content: 'Congrats! Would love to hear more about your tech stack!', created_at: '2024-06-15 11:00:00' },
      { comment_id: 2, post_id: 1, user_id: 4, content: 'This is awesome! How long did it take?', created_at: '2024-06-15 12:30:00' },
      { comment_id: 3, post_id: 2, user_id: 1, content: 'Adding this to my bucket list!', created_at: '2024-06-16 19:15:00' },
      { comment_id: 4, post_id: 3, user_id: 2, content: 'Looks delicious! Can you share the recipe?', created_at: '2024-06-17 13:45:00' },
      { comment_id: 5, post_id: 4, user_id: 5, content: 'Thanks for sharing! Just what I needed', created_at: '2024-06-18 08:30:00' },
      { comment_id: 6, post_id: 5, user_id: 2, content: 'Your art is incredible! How can I commission one?', created_at: '2024-06-19 16:00:00' },
    ],

    likes: [
      { like_id: 1, user_id: 2, post_id: 1, created_at: '2024-06-15 10:45:00' },
      { like_id: 2, user_id: 3, post_id: 1, created_at: '2024-06-15 11:00:00' },
      { like_id: 3, user_id: 4, post_id: 1, created_at: '2024-06-15 12:30:00' },
      { like_id: 4, user_id: 1, post_id: 2, created_at: '2024-06-16 19:15:00' },
      { like_id: 5, user_id: 5, post_id: 2, created_at: '2024-06-16 20:00:00' },
      { like_id: 6, user_id: 2, post_id: 3, created_at: '2024-06-17 13:45:00' },
      { like_id: 7, user_id: 1, post_id: 4, created_at: '2024-06-18 08:00:00' },
      { like_id: 8, user_id: 3, post_id: 5, created_at: '2024-06-19 16:00:00' },
    ],

    follows: [
      { follow_id: 1, follower_id: 1, following_id: 2, created_at: '2024-01-15' },
      { follow_id: 2, follower_id: 1, following_id: 3, created_at: '2024-01-20' },
      { follow_id: 3, follower_id: 2, following_id: 1, created_at: '2024-02-10' },
      { follow_id: 4, follower_id: 2, following_id: 3, created_at: '2024-02-15' },
      { follow_id: 5, follower_id: 3, following_id: 4, created_at: '2024-03-01' },
      { follow_id: 6, follower_id: 4, following_id: 1, created_at: '2024-03-10' },
      { follow_id: 7, follower_id: 5, following_id: 3, created_at: '2024-04-05' },
    ],
  },

  relationships: [
    { from: { table: 'posts', column: 'user_id' }, to: { table: 'users', column: 'user_id' }, type: 'many-to-many' },
    { from: { table: 'comments', column: 'post_id' }, to: { table: 'posts', column: 'post_id' }, type: 'many-to-many' },
    { from: { table: 'comments', column: 'user_id' }, to: { table: 'users', column: 'user_id' }, type: 'many-to-many' },
    { from: { table: 'likes', column: 'user_id' }, to: { table: 'users', column: 'user_id' }, type: 'many-to-many' },
    { from: { table: 'likes', column: 'post_id' }, to: { table: 'posts', column: 'post_id' }, type: 'many-to-many' },
    { from: { table: 'follows', column: 'follower_id' }, to: { table: 'users', column: 'user_id' }, type: 'many-to-many' },
    { from: { table: 'follows', column: 'following_id' }, to: { table: 'users', column: 'user_id' }, type: 'many-to-many' },
  ],

  ddl: `
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  bio TEXT,
  follower_count INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
  post_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  media_url TEXT,
  like_count INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE comments (
  comment_id INTEGER PRIMARY KEY,
  post_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (post_id) REFERENCES posts(post_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE likes (
  like_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (post_id) REFERENCES posts(post_id),
  UNIQUE(user_id, post_id)
);

CREATE TABLE follows (
  follow_id INTEGER PRIMARY KEY,
  follower_id INTEGER NOT NULL,
  following_id INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (follower_id) REFERENCES users(user_id),
  FOREIGN KEY (following_id) REFERENCES users(user_id),
  UNIQUE(follower_id, following_id)
);
  `.trim(),
};
