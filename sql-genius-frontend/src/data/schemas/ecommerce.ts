import type { SchemaTemplate } from './types';

export const ecommerceSchema: SchemaTemplate = {
  id: 'ecommerce',
  name: 'E-commerce Platform',
  description: 'Complete online store with products, orders, customers, and reviews',
  category: 'ecommerce',
  difficulty: 'intermediate',
  icon: '🛒',

  tables: [
    {
      name: 'customers',
      columns: [
        { name: 'customer_id', type: 'INTEGER', primaryKey: true },
        { name: 'email', type: 'TEXT' },
        { name: 'first_name', type: 'TEXT' },
        { name: 'last_name', type: 'TEXT' },
        { name: 'created_at', type: 'DATETIME' },
        { name: 'total_spent', type: 'DECIMAL' },
      ],
    },
    {
      name: 'products',
      columns: [
        { name: 'product_id', type: 'INTEGER', primaryKey: true },
        { name: 'name', type: 'TEXT' },
        { name: 'category', type: 'TEXT' },
        { name: 'price', type: 'DECIMAL' },
        { name: 'stock_quantity', type: 'INTEGER' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
    {
      name: 'orders',
      columns: [
        { name: 'order_id', type: 'INTEGER', primaryKey: true },
        { name: 'customer_id', type: 'INTEGER', foreignKey: { table: 'customers', column: 'customer_id' } },
        { name: 'order_date', type: 'DATETIME' },
        { name: 'total_amount', type: 'DECIMAL' },
        { name: 'status', type: 'TEXT' },
      ],
    },
    {
      name: 'order_items',
      columns: [
        { name: 'order_item_id', type: 'INTEGER', primaryKey: true },
        { name: 'order_id', type: 'INTEGER', foreignKey: { table: 'orders', column: 'order_id' } },
        { name: 'product_id', type: 'INTEGER', foreignKey: { table: 'products', column: 'product_id' } },
        { name: 'quantity', type: 'INTEGER' },
        { name: 'unit_price', type: 'DECIMAL' },
      ],
    },
    {
      name: 'reviews',
      columns: [
        { name: 'review_id', type: 'INTEGER', primaryKey: true },
        { name: 'product_id', type: 'INTEGER', foreignKey: { table: 'products', column: 'product_id' } },
        { name: 'customer_id', type: 'INTEGER', foreignKey: { table: 'customers', column: 'customer_id' } },
        { name: 'rating', type: 'INTEGER' },
        { name: 'comment', type: 'TEXT' },
        { name: 'created_at', type: 'DATETIME' },
      ],
    },
  ],

  sampleData: {
    customers: [
      { customer_id: 1, email: 'alice@example.com', first_name: 'Alice', last_name: 'Johnson', created_at: '2024-01-15', total_spent: 1250.50 },
      { customer_id: 2, email: 'bob@example.com', first_name: 'Bob', last_name: 'Smith', created_at: '2024-02-20', total_spent: 890.25 },
      { customer_id: 3, email: 'carol@example.com', first_name: 'Carol', last_name: 'Williams', created_at: '2024-03-10', total_spent: 2100.00 },
      { customer_id: 4, email: 'david@example.com', first_name: 'David', last_name: 'Brown', created_at: '2024-04-05', total_spent: 450.75 },
      { customer_id: 5, email: 'emma@example.com', first_name: 'Emma', last_name: 'Davis', created_at: '2024-05-12', total_spent: 3200.00 },
    ],

    products: [
      { product_id: 1, name: 'Laptop Pro 15"', category: 'Electronics', price: 1299.99, stock_quantity: 45, created_at: '2024-01-01' },
      { product_id: 2, name: 'Wireless Mouse', category: 'Electronics', price: 29.99, stock_quantity: 200, created_at: '2024-01-01' },
      { product_id: 3, name: 'USB-C Cable', category: 'Accessories', price: 12.99, stock_quantity: 500, created_at: '2024-01-05' },
      { product_id: 4, name: 'Mechanical Keyboard', category: 'Electronics', price: 89.99, stock_quantity: 75, created_at: '2024-01-10' },
      { product_id: 5, name: 'Monitor 27"', category: 'Electronics', price: 349.99, stock_quantity: 30, created_at: '2024-01-15' },
      { product_id: 6, name: 'Desk Lamp', category: 'Office', price: 45.99, stock_quantity: 120, created_at: '2024-02-01' },
      { product_id: 7, name: 'Office Chair', category: 'Office', price: 299.99, stock_quantity: 25, created_at: '2024-02-05' },
      { product_id: 8, name: 'Webcam HD', category: 'Electronics', price: 79.99, stock_quantity: 60, created_at: '2024-02-10' },
    ],

    orders: [
      { order_id: 1, customer_id: 1, order_date: '2024-06-01', total_amount: 1329.98, status: 'delivered' },
      { order_id: 2, customer_id: 2, order_date: '2024-06-03', total_amount: 89.99, status: 'delivered' },
      { order_id: 3, customer_id: 3, order_date: '2024-06-05', total_amount: 699.97, status: 'shipped' },
      { order_id: 4, customer_id: 1, order_date: '2024-06-07', total_amount: 45.99, status: 'delivered' },
      { order_id: 5, customer_id: 4, order_date: '2024-06-10', total_amount: 299.99, status: 'processing' },
      { order_id: 6, customer_id: 5, order_date: '2024-06-12', total_amount: 1729.96, status: 'delivered' },
      { order_id: 7, customer_id: 3, order_date: '2024-06-15', total_amount: 142.97, status: 'shipped' },
    ],

    order_items: [
      { order_item_id: 1, order_id: 1, product_id: 1, quantity: 1, unit_price: 1299.99 },
      { order_item_id: 2, order_id: 1, product_id: 2, quantity: 1, unit_price: 29.99 },
      { order_item_id: 3, order_id: 2, product_id: 4, quantity: 1, unit_price: 89.99 },
      { order_item_id: 4, order_id: 3, product_id: 5, quantity: 2, unit_price: 349.99 },
      { order_item_id: 5, order_id: 4, product_id: 6, quantity: 1, unit_price: 45.99 },
      { order_item_id: 6, order_id: 5, product_id: 7, quantity: 1, unit_price: 299.99 },
      { order_item_id: 7, order_id: 6, product_id: 1, quantity: 1, unit_price: 1299.99 },
      { order_item_id: 8, order_id: 6, product_id: 5, quantity: 1, unit_price: 349.99 },
      { order_item_id: 9, order_id: 6, product_id: 8, quantity: 1, unit_price: 79.99 },
      { order_item_id: 10, order_id: 7, product_id: 2, quantity: 2, unit_price: 29.99 },
      { order_item_id: 11, order_id: 7, product_id: 3, quantity: 5, unit_price: 12.99 },
      { order_item_id: 12, order_id: 7, product_id: 6, quantity: 1, unit_price: 45.99 },
    ],

    reviews: [
      { review_id: 1, product_id: 1, customer_id: 1, rating: 5, comment: 'Excellent laptop, very fast!', created_at: '2024-06-05' },
      { review_id: 2, product_id: 2, customer_id: 2, rating: 4, comment: 'Good mouse, comfortable grip', created_at: '2024-06-08' },
      { review_id: 3, product_id: 4, customer_id: 2, rating: 5, comment: 'Best keyboard I ever used', created_at: '2024-06-08' },
      { review_id: 4, product_id: 5, customer_id: 3, rating: 5, comment: 'Crystal clear display', created_at: '2024-06-10' },
      { review_id: 5, product_id: 6, customer_id: 1, rating: 4, comment: 'Nice lamp, good brightness', created_at: '2024-06-12' },
      { review_id: 6, product_id: 1, customer_id: 5, rating: 5, comment: 'Worth every penny!', created_at: '2024-06-18' },
    ],
  },

  relationships: [
    { from: { table: 'orders', column: 'customer_id' }, to: { table: 'customers', column: 'customer_id' }, type: 'many-to-many' },
    { from: { table: 'order_items', column: 'order_id' }, to: { table: 'orders', column: 'order_id' }, type: 'many-to-many' },
    { from: { table: 'order_items', column: 'product_id' }, to: { table: 'products', column: 'product_id' }, type: 'many-to-many' },
    { from: { table: 'reviews', column: 'product_id' }, to: { table: 'products', column: 'product_id' }, type: 'many-to-many' },
    { from: { table: 'reviews', column: 'customer_id' }, to: { table: 'customers', column: 'customer_id' }, type: 'many-to-many' },
  ],

  ddl: `
CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  total_spent DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE products (
  product_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock_quantity INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
  order_id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  total_amount DECIMAL(10,2) NOT NULL,
  status TEXT DEFAULT 'pending',
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
  order_item_id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE reviews (
  review_id INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL,
  customer_id INTEGER NOT NULL,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
  `.trim(),
};
