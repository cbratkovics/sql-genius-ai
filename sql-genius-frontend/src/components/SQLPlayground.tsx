'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  Database,
  Play,
  Copy,
  Check,
  Loader2,
  Code,
  FileText,
  Zap,
  Shield,
  CheckCircle,
  Download,
  ChevronDown
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import { useGenerateSQL } from '@/hooks/useDemo';
import { useDatabase, useSQLQuery } from '@/hooks/useDatabase';
import { schemas } from '@/data/schemas';
import { getQueriesBySchema } from '@/data/queries';
import type { SchemaTemplate } from '@/data/schemas/types';
import type { SampleQuery } from '@/data/queries/types';
import * as Tabs from '@radix-ui/react-tabs';
import Link from 'next/link';
import { toast } from 'react-hot-toast';

export default function SQLPlayground() {
  const [query, setQuery] = useState('');
  const [generatedSQL, setGeneratedSQL] = useState('');
  const [selectedSchemaId, setSelectedSchemaId] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('playground');

  const generateSQL = useGenerateSQL();
  const database = useDatabase();
  const sqlQuery = useSQLQuery();

  // Auto-load first schema on initialization
  useEffect(() => {
    if (database.isInitialized && !selectedSchemaId && schemas.length > 0) {
      handleSchemaChange(schemas[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [database.isInitialized]);

  const handleSchemaChange = async (schema: SchemaTemplate) => {
    setSelectedSchemaId(schema.id);
    await database.loadSchema(schema);
    setGeneratedSQL('');
    sqlQuery.reset();
  };

  const handleGenerate = async () => {
    if (!query.trim()) {
      toast.error('Please enter a natural language query');
      return;
    }

    const currentSchema = schemas.find(s => s.id === selectedSchemaId);
    if (!currentSchema) {
      toast.error('Please select a schema first');
      return;
    }

    try {
      const result = await generateSQL.mutateAsync({
        query,
        schemaContext: currentSchema.name,
      });

      if (result.success) {
        setGeneratedSQL(result.sql);
      }
    } catch (error) {
      console.error('SQL generation error:', error);
    }
  };

  const handleCopySQL = () => {
    navigator.clipboard.writeText(generatedSQL);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExecute = async () => {
    if (!generatedSQL) {
      toast.error('No SQL query to execute');
      return;
    }

    if (!database.isReady()) {
      toast.error('Database not ready. Please select a schema first.');
      return;
    }

    try {
      await sqlQuery.execute(generatedSQL);
    } catch (error) {
      console.error('Execution error:', error);
    }
  };

  const loadSampleQuery = (sample: SampleQuery) => {
    setQuery(sample.naturalLanguage);
    setGeneratedSQL(sample.sql);
    setActiveTab('playground');
  };

  const currentSchema = schemas.find(s => s.id === selectedSchemaId);
  const currentSchemaQueries = selectedSchemaId ? getQueriesBySchema(selectedSchemaId) : [];

  const exportResults = () => {
    if (!sqlQuery.results) return;

    const csv = [
      sqlQuery.results.columns.join(','),
      ...sqlQuery.results.values.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'query-results.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      {/* Navigation */}
      <nav className="bg-black/20 backdrop-blur-lg border-b border-white/10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <Sparkles className="w-8 h-8 text-blue-400" />
              <span className="text-2xl font-bold text-white">SQL Genius AI</span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link href="/" className="text-white hover:text-blue-400 transition">
                Home
              </Link>
              <Link href="/metrics" className="text-white hover:text-blue-400 transition">
                Metrics
              </Link>
              <Link href="https://github.com/cbratkovics/sql-genius-ai" target="_blank" rel="noopener noreferrer" className="text-white hover:text-blue-400 transition">
                GitHub
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-3">
                <Database className="w-8 h-8 text-white" />
                <div>
                  <h1 className="text-3xl font-bold text-white">SQL Playground</h1>
                  <p className="text-blue-100 text-sm mt-1">Interactive SQL environment with AI-powered generation</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 bg-white/20 rounded-full px-4 py-2">
                  <Shield className="w-4 h-4 text-green-300" />
                  <span className="text-sm text-white">In-Browser SQL</span>
                </div>
                <div className="flex items-center space-x-2 bg-white/20 rounded-full px-4 py-2">
                  <Zap className="w-4 h-4 text-yellow-300" />
                  <span className="text-sm text-white">AI Powered</span>
                </div>
              </div>
            </div>

            {/* Schema Selector */}
            <div className="mt-4 flex items-center space-x-3">
              <label className="text-white font-semibold text-sm">Schema:</label>
              <div className="relative">
                <select
                  value={selectedSchemaId}
                  onChange={(e) => {
                    const schema = schemas.find(s => s.id === e.target.value);
                    if (schema) handleSchemaChange(schema);
                  }}
                  className="appearance-none bg-white/20 backdrop-blur-sm text-white rounded-lg px-4 py-2 pr-10 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 cursor-pointer"
                  disabled={!database.isInitialized}
                >
                  <option value="" disabled>Select a schema...</option>
                  {schemas.map((schema) => (
                    <option key={schema.id} value={schema.id} className="bg-gray-800">
                      {schema.icon} {schema.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white pointer-events-none" />
              </div>
              {currentSchema && (
                <span className="text-blue-100 text-sm">
                  {currentSchema.description}
                </span>
              )}
            </div>
          </div>

          <div className="p-6">
            <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="w-full">
              <Tabs.List className="flex space-x-1 bg-gray-800/50 p-1 rounded-lg mb-6">
                <Tabs.Trigger
                  value="playground"
                  className="flex-1 px-4 py-2 rounded-md text-white data-[state=active]:bg-blue-600 transition-all"
                >
                  <Code className="w-4 h-4 inline-block mr-2" />
                  Playground
                </Tabs.Trigger>
                <Tabs.Trigger
                  value="templates"
                  className="flex-1 px-4 py-2 rounded-md text-white data-[state=active]:bg-blue-600 transition-all"
                >
                  <Database className="w-4 h-4 inline-block mr-2" />
                  Schema Templates
                </Tabs.Trigger>
                <Tabs.Trigger
                  value="samples"
                  className="flex-1 px-4 py-2 rounded-md text-white data-[state=active]:bg-blue-600 transition-all"
                >
                  <FileText className="w-4 h-4 inline-block mr-2" />
                  Sample Queries
                </Tabs.Trigger>
              </Tabs.List>

              {/* Playground Tab */}
              <Tabs.Content value="playground" className="space-y-6">
                {/* Real AI Notice */}
                <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span className="text-sm text-green-300">
                      Real AI: Uses Claude 3.5 Sonnet API for SQL generation + In-browser SQLite execution
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Natural Language Input */}
                  <div className="space-y-4">
                    <label className="text-white font-semibold text-lg flex items-center justify-between">
                      <span>Natural Language Query</span>
                      <span className="text-xs text-gray-400 font-normal">Ask in plain English</span>
                    </label>
                    <textarea
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g., Show me total sales by month for the last year..."
                      className="w-full h-40 p-4 bg-gray-800/50 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none resize-none placeholder:text-gray-500"
                    />
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleGenerate}
                      disabled={!query.trim() || generateSQL.isPending || !database.isReady()}
                      className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all"
                    >
                      {generateSQL.isPending ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Sparkles className="w-5 h-5" />
                      )}
                      <span>{generateSQL.isPending ? 'Generating...' : 'Generate SQL with AI'}</span>
                    </motion.button>
                  </div>

                  {/* Generated SQL Output */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold text-lg">Generated SQL</label>
                      <div className="flex space-x-2">
                        <button
                          onClick={handleCopySQL}
                          disabled={!generatedSQL}
                          className="px-3 py-1.5 bg-gray-800 text-white rounded-md text-sm flex items-center space-x-1 hover:bg-gray-700 disabled:opacity-50 transition-colors"
                        >
                          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          <span>{copied ? 'Copied!' : 'Copy'}</span>
                        </button>
                        <button
                          onClick={handleExecute}
                          disabled={!generatedSQL || sqlQuery.isExecuting || !database.isReady()}
                          className="px-3 py-1.5 bg-green-600 text-white rounded-md text-sm flex items-center space-x-1 hover:bg-green-700 disabled:opacity-50 transition-colors"
                        >
                          {sqlQuery.isExecuting ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                          <span>Execute</span>
                        </button>
                      </div>
                    </div>
                    <div className="h-40 rounded-lg overflow-hidden border border-gray-700">
                      <Editor
                        height="160px"
                        defaultLanguage="sql"
                        value={generatedSQL}
                        onChange={(value) => setGeneratedSQL(value || '')}
                        theme="vs-dark"
                        options={{
                          minimap: { enabled: false },
                          fontSize: 14,
                          wordWrap: 'on',
                          lineNumbers: 'on',
                          scrollBeyondLastLine: false,
                          automaticLayout: true,
                        }}
                      />
                    </div>

                    {/* Execution Notice */}
                    <div className="p-2 bg-blue-500/10 border-l-2 border-blue-500 rounded">
                      <span className="text-xs text-blue-300">
                        <Database className="w-3 h-3 inline mr-1" />
                        Queries execute against in-browser SQLite database with sample data
                      </span>
                    </div>
                  </div>
                </div>

                {/* Generation Results */}
                {generateSQL.data && generateSQL.data.success && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800/50 rounded-lg p-6 space-y-4 border border-gray-700"
                  >
                    <h3 className="text-white font-semibold text-lg">AI Analysis</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Confidence Score</div>
                        <div className="text-2xl font-bold text-green-400">
                          {(generateSQL.data.confidence_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Generation Time</div>
                        <div className="text-2xl font-bold text-blue-400">
                          {generateSQL.data.performance.generation_time_ms.toFixed(0)}ms
                        </div>
                      </div>
                      <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Security Status</div>
                        <div className="text-2xl font-bold text-green-400 flex items-center">
                          <CheckCircle className="w-6 h-6 mr-2" />
                          Validated
                        </div>
                      </div>
                    </div>
                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="text-gray-400 text-sm mb-2">Explanation</div>
                      <p className="text-white">{generateSQL.data.explanation}</p>
                    </div>
                  </motion.div>
                )}

                {/* Execution Results */}
                {sqlQuery.results && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800/50 rounded-lg p-6 border border-gray-700"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-white font-semibold text-lg">Query Results</h3>
                      <button
                        onClick={exportResults}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm flex items-center space-x-1 hover:bg-blue-700 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        <span>Export CSV</span>
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-white border-collapse">
                        <thead>
                          <tr className="border-b border-gray-700">
                            {sqlQuery.results.columns.map((col, idx) => (
                              <th key={idx} className="text-left p-3 bg-gray-900/50 font-semibold text-blue-300">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {sqlQuery.results.values.map((row, rowIdx) => (
                            <tr key={rowIdx} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                              {row.map((value, colIdx) => (
                                <td key={colIdx} className="p-3">
                                  {value === null ? <span className="text-gray-500 italic">NULL</span> : String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="mt-4 flex items-center justify-between text-sm text-gray-400">
                      <span>{sqlQuery.results.rowCount} rows returned</span>
                      <span className="text-green-400">✓ Executed successfully</span>
                    </div>
                  </motion.div>
                )}
              </Tabs.Content>

              {/* Schema Templates Tab */}
              <Tabs.Content value="templates" className="space-y-4">
                <div className="mb-4 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <span className="text-sm text-purple-300">
                    Select a schema template to load sample data and start querying
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {schemas.map((schema) => (
                    <motion.div
                      key={schema.id}
                      whileHover={{ scale: 1.02 }}
                      className={`bg-gray-800/50 rounded-lg p-6 cursor-pointer border-2 transition-all ${
                        selectedSchemaId === schema.id
                          ? 'border-blue-500 bg-blue-900/20'
                          : 'border-gray-700 hover:border-gray-600'
                      }`}
                      onClick={() => handleSchemaChange(schema)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="text-4xl mb-2">{schema.icon}</div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          schema.difficulty === 'beginner' ? 'bg-green-500/20 text-green-300' :
                          schema.difficulty === 'intermediate' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-red-500/20 text-red-300'
                        }`}>
                          {schema.difficulty}
                        </span>
                      </div>
                      <h3 className="text-white font-semibold text-lg mb-2">{schema.name}</h3>
                      <p className="text-gray-400 text-sm mb-4">{schema.description}</p>
                      <div className="space-y-2">
                        <div className="text-gray-500 text-xs uppercase tracking-wide">Tables ({schema.tables.length})</div>
                        <div className="flex flex-wrap gap-2">
                          {schema.tables.map((table) => (
                            <span
                              key={table.name}
                              className="px-2 py-1 bg-gray-900/50 text-gray-300 rounded text-xs border border-gray-700"
                            >
                              {table.name}
                            </span>
                          ))}
                        </div>
                      </div>
                      {selectedSchemaId === schema.id && (
                        <div className="mt-3 pt-3 border-t border-blue-500/30">
                          <span className="text-blue-400 text-sm flex items-center">
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Currently loaded
                          </span>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </Tabs.Content>

              {/* Sample Queries Tab */}
              <Tabs.Content value="samples" className="space-y-6">
                <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <span className="text-sm text-amber-300">
                    Click any query to load it into the playground. {currentSchemaQueries.length} queries available for {currentSchema?.name || 'selected schema'}.
                  </span>
                </div>

                {!selectedSchemaId ? (
                  <div className="text-center py-12 text-gray-400">
                    <Database className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>Please select a schema first to view sample queries</p>
                  </div>
                ) : (
                  <>
                    {['beginner', 'intermediate', 'advanced'].map((difficulty) => {
                      const queries = currentSchemaQueries.filter(q => q.difficulty === difficulty);
                      if (queries.length === 0) return null;

                      return (
                        <div key={difficulty}>
                          <h3 className="text-white font-semibold text-lg mb-3 capitalize flex items-center">
                            {difficulty}
                            <span className="ml-2 px-2 py-0.5 bg-gray-700 text-gray-300 rounded-full text-xs">
                              {queries.length} queries
                            </span>
                          </h3>
                          <div className="space-y-3">
                            {queries.map((sample) => (
                              <motion.button
                                key={sample.id}
                                whileHover={{ scale: 1.01 }}
                                onClick={() => loadSampleQuery(sample)}
                                className="w-full text-left p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800/70 transition-all border border-gray-700 hover:border-gray-600"
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <h4 className="text-white font-semibold">{sample.naturalLanguage}</h4>
                                  <span className="text-xs px-2 py-1 bg-blue-600/20 text-blue-300 rounded ml-2 whitespace-nowrap">
                                    {sample.category.replace('_', ' ')}
                                  </span>
                                </div>
                                <p className="text-gray-400 text-sm mb-2">{sample.description}</p>
                                <pre className="text-gray-300 font-mono text-xs bg-gray-900/50 p-2 rounded overflow-x-auto border border-gray-700">
                                  {sample.sql}
                                </pre>
                                <div className="mt-2 flex flex-wrap gap-1">
                                  {sample.tags.map((tag) => (
                                    <span key={tag} className="px-2 py-0.5 bg-gray-700/50 text-gray-400 rounded text-xs">
                                      #{tag}
                                    </span>
                                  ))}
                                </div>
                              </motion.button>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </>
                )}
              </Tabs.Content>
            </Tabs.Root>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
