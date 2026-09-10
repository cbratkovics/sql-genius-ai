'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Sparkles,
  Database,
  Zap,
  Shield,
  Globe,
  ArrowRight,
  Code,
  Gauge,
  AlertCircle
} from 'lucide-react';

export default function Home() {
  const features = [
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: "LLM Integration",
      description: "Optional provider generation with explicit model and request provenance"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Input Validation",
      description: "Typed requests plus a narrow, tested read-only SQLite policy"
    },
    {
      icon: <Database className="w-6 h-6" />,
      title: "Schema Context",
      description: "Selected tables, columns, types, and relationships are sent as bounded context"
    },
    {
      icon: <Code className="w-6 h-6" />,
      title: "Type-Safe APIs",
      description: "End-to-end TypeScript with FastAPI + Pydantic"
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Async Architecture",
      description: "Separate generation, review, and explicit local execution states"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Modern Deployment",
      description: "Maintained deployment templates with documented verification steps"
    }
  ];

  const stats = [
    { value: "SQLite", label: "Local Engine" },
    { value: "FastAPI", label: "Backend Framework" },
    { value: "Next.js 15", label: "Frontend" },
    { value: "TypeScript", label: "Type Safety" }
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
                API Docs
              </Link>
              <Link
                href="/demo"
                className="group px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-blue-500/50 transform hover:scale-105 transition-all duration-200 flex items-center space-x-1"
              >
                <span>Try Demo</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
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
          <div className="mb-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-full">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-blue-300">Portfolio Demo Project</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            Transform Natural Language
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Into SQL Queries
            </span>
          </h1>
          
          <p className="text-gray-300 text-lg max-w-2xl mx-auto mb-8">
            Natural-language SQL and analytics playground with optional provider generation.
            Explore deterministic sample schemas, inspect SQL, and run supported queries locally in SQLite.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/demo"
              className="group px-16 py-7 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-2xl rounded-xl hover:shadow-2xl hover:shadow-blue-500/50 transform hover:scale-105 transition-all duration-200 flex items-center justify-center space-x-3 min-h-[80px]"
            >
              <span>Try Live Demo</span>
              <ArrowRight className="w-8 h-8 group-hover:translate-x-1 transition-transform" />
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
          <h2 className="text-3xl font-bold text-white mb-4">
            AI Engineering Skills Demonstrated
          </h2>
          <p className="text-gray-300 mb-12 max-w-2xl mx-auto">
            This portfolio project demonstrates applied AI and analytics engineering patterns
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
                Optional typed generation API; provider output is returned as not executed
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-purple-600/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Database className="w-10 h-10 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Browser SQLite</h3>
              <p className="text-gray-400 text-sm">
                Deterministic synthetic schemas with explicit, read-only local execution
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-green-600/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Gauge className="w-10 h-10 text-green-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Visible Provenance</h3>
              <p className="text-gray-400 text-sm">
                Generation source, schema, execution status, and truncation stay visible
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
            Explore an Inspectable SQL Workflow
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Choose a sample schema, inspect curated or generated SQL, then run it explicitly against local fixture data.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/demo"
              className="group px-10 py-5 bg-white text-blue-600 font-bold text-lg rounded-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-200 flex items-center justify-center space-x-2 min-h-[60px]"
            >
              <span>Try Live Demo</span>
              <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="https://github.com/cbratkovics/sql-genius-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="group px-10 py-5 bg-black/30 backdrop-blur-sm text-white font-bold text-lg rounded-lg hover:bg-black/40 transition-all duration-200 flex items-center justify-center space-x-2 min-h-[60px] border border-white/20"
            >
              <Code className="w-6 h-6" />
              <span>View on GitHub</span>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Transparency Notice */}
      <section className="container mx-auto px-4 pb-12">
        <div className="mt-16 p-6 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
          <h3 className="text-lg font-semibold text-yellow-300 mb-2 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Portfolio Demo Notice
          </h3>
          <p className="text-gray-300 text-sm">
            This portfolio project demonstrates analytics and applied-AI engineering. Curated examples need no key; optional live generation requires configured backend credentials. Accepted SQL executes locally only against bundled synthetic sample data. No aggregate usage or model-accuracy metrics are claimed. View the full implementation
            at{' '}
            <a 
              href="https://github.com/cbratkovics/sql-genius-ai" 
              className="text-blue-400 hover:underline"
              target="_blank" 
              rel="noopener noreferrer"
            >
              github.com/cbratkovics/sql-genius-ai
            </a>
          </p>
        </div>
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
