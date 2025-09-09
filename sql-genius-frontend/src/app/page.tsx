'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Sparkles, 
  Database, 
  Zap, 
  Shield, 
  Globe, 
  BarChart3,
  ArrowRight,
  CheckCircle,
  Code,
  Users,
  Gauge,
  Lock
} from 'lucide-react';

export default function Home() {
  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Lightning Fast",
      description: "Sub-300ms SQL generation with AI optimization"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Enterprise Security",
      description: "SQL injection protection and sandboxed execution"
    },
    {
      icon: <Database className="w-6 h-6" />,
      title: "Multi-Database",
      description: "Support for PostgreSQL, MySQL, SQL Server, and more"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Multi-Tenant",
      description: "Isolated environments for each organization"
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Real-Time Analytics",
      description: "Monitor performance and usage metrics"
    },
    {
      icon: <Lock className="w-6 h-6" />,
      title: "JWT Authentication",
      description: "Secure API access with token-based auth"
    }
  ];

  const stats = [
    { value: "< 300ms", label: "Response Time" },
    { value: "99.9%", label: "Uptime SLA" },
    { value: "10M+", label: "Queries Processed" },
    { value: "24/7", label: "Support" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      {/* Navigation */}
      <nav className="bg-black/20 backdrop-blur-lg border-b border-white/10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-8 h-8 text-blue-400" />
              <span className="text-2xl font-bold text-white">SQL Genius AI</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/demo" className="text-white hover:text-blue-400 transition">
                Demo
              </Link>
              <Link href="/metrics" className="text-white hover:text-blue-400 transition">
                Metrics
              </Link>
              <Link href="/docs" className="text-white hover:text-blue-400 transition">
                API Docs
              </Link>
              <Link 
                href="/demo"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Try It Free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center space-x-2 bg-blue-600/20 px-4 py-2 rounded-full mb-6">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-blue-400 text-sm font-semibold">Powered by Claude AI</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            Transform Natural Language
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Into SQL Queries
            </span>
          </h1>
          
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Enterprise-grade AI platform that converts plain English to optimized SQL queries. 
            Built for developers, analysts, and businesses.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/demo"
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:shadow-xl transform hover:scale-105 transition flex items-center justify-center space-x-2"
            >
              <span>Try Live Demo</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/metrics"
              className="px-8 py-4 bg-white/10 backdrop-blur-lg text-white font-semibold rounded-lg hover:bg-white/20 transition flex items-center justify-center space-x-2"
            >
              <BarChart3 className="w-5 h-5" />
              <span>View Metrics</span>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-center"
            >
              <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
              <div className="text-gray-400">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl font-bold text-white mb-4">Enterprise Features</h2>
          <p className="text-gray-300 max-w-2xl mx-auto">
            Built with scalability, security, and performance in mind
          </p>
        </motion.div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + idx * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 hover:bg-white/15 transition"
            >
              <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-4 text-blue-400">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Architecture Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-white/10 backdrop-blur-lg rounded-3xl p-8"
        >
          <h2 className="text-3xl font-bold text-white mb-6 text-center">System Architecture</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-20 h-20 bg-blue-600/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Code className="w-10 h-10 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">FastAPI Backend</h3>
              <p className="text-gray-400 text-sm">
                High-performance async Python API with automatic OpenAPI documentation
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-purple-600/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Database className="w-10 h-10 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">PostgreSQL + Redis</h3>
              <p className="text-gray-400 text-sm">
                Scalable data persistence with caching for optimal performance
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-green-600/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Gauge className="w-10 h-10 text-green-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Real-Time Monitoring</h3>
              <p className="text-gray-400 text-sm">
                Prometheus metrics, Grafana dashboards, and comprehensive logging
              </p>
            </div>
          </div>
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12 text-center"
        >
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to Transform Your Data Queries?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join thousands of developers and analysts using SQL Genius AI to accelerate their workflow
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/demo"
              className="px-8 py-4 bg-white text-blue-600 font-semibold rounded-lg hover:shadow-xl transform hover:scale-105 transition"
            >
              Start Free Trial
            </Link>
            <Link
              href="https://github.com/cbratkovics/sql-genius-ai"
              target="_blank"
              className="px-8 py-4 bg-black/20 text-white font-semibold rounded-lg hover:bg-black/30 transition"
            >
              View on GitHub
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="bg-black/20 backdrop-blur-lg border-t border-white/10 py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <Sparkles className="w-6 h-6 text-blue-400" />
              <span className="text-white font-semibold">SQL Genius AI</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/demo" className="text-gray-400 hover:text-white transition">
                Demo
              </Link>
              <Link href="/metrics" className="text-gray-400 hover:text-white transition">
                Metrics
              </Link>
              <Link href="https://sql-genius-api.onrender.com/docs" className="text-gray-400 hover:text-white transition">
                API Docs
              </Link>
              <Link href="https://github.com/cbratkovics/sql-genius-ai" className="text-gray-400 hover:text-white transition">
                GitHub
              </Link>
            </div>
          </div>
          <div className="text-center mt-6 text-gray-500 text-sm">
            © 2024 SQL Genius AI. Built with FastAPI, Next.js, and Claude AI.
          </div>
        </div>
      </footer>
    </div>
  );
}
