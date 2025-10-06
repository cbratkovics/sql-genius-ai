'use client';

import React, { useState } from 'react';
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
  Shield
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import { useGenerateSQL, useExecuteSandbox, useSchemaTemplates, useSampleQueries } from '@/hooks/useDemo';
import type { Schema, SampleQuery } from '@/lib/api';
import * as Tabs from '@radix-ui/react-tabs';
import * as Select from '@radix-ui/react-select';

export default function SQLPlayground() {
  const [query, setQuery] = useState('');
  const [generatedSQL, setGeneratedSQL] = useState('');
  const [selectedSchema, setSelectedSchema] = useState('');
  const [copied, setCopied] = useState(false);
  
  const generateSQL = useGenerateSQL();
  const executeSandbox = useExecuteSandbox();
  const { data: schemas } = useSchemaTemplates();
  const { data: sampleQueries } = useSampleQueries();

  const handleGenerate = async () => {
    if (!query.trim()) return;
    
    const result = await generateSQL.mutateAsync({
      query,
      schemaContext: selectedSchema,
    });
    
    if (result.success) {
      setGeneratedSQL(result.sql);
    }
  };

  const handleCopySQL = () => {
    navigator.clipboard.writeText(generatedSQL);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExecute = async () => {
    if (!generatedSQL) return;
    await executeSandbox.mutateAsync(generatedSQL);
  };

  const loadSampleQuery = (sample: SampleQuery) => {
    setQuery(sample.query);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Sparkles className="w-8 h-8 text-white" />
                <h1 className="text-3xl font-bold text-white">SQL Playground</h1>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 bg-white/20 rounded-full px-4 py-2">
                  <Shield className="w-4 h-4 text-green-300" />
                  <span className="text-sm text-white">Sandbox Mode</span>
                </div>
                <div className="flex items-center space-x-2 bg-white/20 rounded-full px-4 py-2">
                  <Zap className="w-4 h-4 text-yellow-300" />
                  <span className="text-sm text-white">AI Powered</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6">
            <Tabs.Root defaultValue="playground" className="w-full">
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Natural Language Input */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold">Natural Language Query</label>
                      <Select.Root value={selectedSchema} onValueChange={setSelectedSchema}>
                        <Select.Trigger className="px-3 py-1 bg-gray-800 text-white rounded-md text-sm">
                          <Select.Value placeholder="Select schema" />
                        </Select.Trigger>
                        <Select.Portal>
                          <Select.Content className="bg-gray-800 text-white rounded-md shadow-lg">
                            <Select.Viewport>
                              {schemas?.map((schema: Schema) => (
                                <Select.Item
                                  key={schema.name}
                                  value={schema.name}
                                  className="px-3 py-2 hover:bg-gray-700 cursor-pointer"
                                >
                                  <Select.ItemText>{schema.name}</Select.ItemText>
                                </Select.Item>
                              ))}
                            </Select.Viewport>
                          </Select.Content>
                        </Select.Portal>
                      </Select.Root>
                    </div>
                    <textarea
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g., Show me total sales by month for the last year"
                      className="w-full h-40 p-4 bg-gray-800/50 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none resize-none"
                    />
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleGenerate}
                      disabled={!query.trim() || generateSQL.isPending}
                      className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {generateSQL.isPending ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Sparkles className="w-5 h-5" />
                      )}
                      <span>{generateSQL.isPending ? 'Generating...' : 'Generate SQL'}</span>
                    </motion.button>
                  </div>

                  {/* Generated SQL Output */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold">Generated SQL</label>
                      <div className="flex space-x-2">
                        <button
                          onClick={handleCopySQL}
                          disabled={!generatedSQL}
                          className="px-3 py-1 bg-gray-800 text-white rounded-md text-sm flex items-center space-x-1 hover:bg-gray-700 disabled:opacity-50"
                        >
                          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          <span>{copied ? 'Copied!' : 'Copy'}</span>
                        </button>
                        <button
                          onClick={handleExecute}
                          disabled={!generatedSQL || executeSandbox.isPending}
                          className="px-3 py-1 bg-green-600 text-white rounded-md text-sm flex items-center space-x-1 hover:bg-green-700 disabled:opacity-50"
                        >
                          <Play className="w-4 h-4" />
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
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Results Display */}
                {generateSQL.data && generateSQL.data.success && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800/50 rounded-lg p-6 space-y-4"
                  >
                    <h3 className="text-white font-semibold text-lg">Analysis</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gray-900/50 rounded-lg p-4">
                        <div className="text-gray-400 text-sm mb-1">Confidence Score</div>
                        <div className="text-2xl font-bold text-green-400">
                          {(generateSQL.data.confidence_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="bg-gray-900/50 rounded-lg p-4">
                        <div className="text-gray-400 text-sm mb-1">Generation Time</div>
                        <div className="text-2xl font-bold text-blue-400">
                          {generateSQL.data.performance.generation_time_ms.toFixed(0)}ms
                        </div>
                      </div>
                      <div className="bg-gray-900/50 rounded-lg p-4">
                        <div className="text-gray-400 text-sm mb-1">Security Status</div>
                        <div className="text-2xl font-bold text-green-400">
                          Validated
                        </div>
                      </div>
                    </div>
                    <div className="bg-gray-900/50 rounded-lg p-4">
                      <div className="text-gray-400 text-sm mb-2">Explanation</div>
                      <p className="text-white">{generateSQL.data.explanation}</p>
                    </div>
                  </motion.div>
                )}

                {/* Execution Results */}
                {executeSandbox.data && executeSandbox.data.success && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800/50 rounded-lg p-6"
                  >
                    <h3 className="text-white font-semibold text-lg mb-4">Execution Results</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-white">
                        <thead>
                          <tr className="border-b border-gray-700">
                            {executeSandbox.data.sample_results[0] &&
                              Object.keys(executeSandbox.data.sample_results[0]).map((key) => (
                                <th key={key} className="text-left p-2">
                                  {key}
                                </th>
                              ))}
                          </tr>
                        </thead>
                        <tbody>
                          {executeSandbox.data.sample_results.map((row: Record<string, unknown>, idx: number) => (
                            <tr key={idx} className="border-b border-gray-700/50">
                              {Object.values(row).map((value: unknown, i: number) => (
                                <td key={i} className="p-2">
                                  {String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="mt-4 flex items-center justify-between text-sm text-gray-400">
                      <span>{executeSandbox.data.rows_affected} rows returned</span>
                      <span>Execution time: {executeSandbox.data.execution_time_ms.toFixed(0)}ms</span>
                    </div>
                  </motion.div>
                )}
              </Tabs.Content>

              {/* Schema Templates Tab */}
              <Tabs.Content value="templates" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {schemas?.map((schema: Schema) => (
                    <motion.div
                      key={schema.name}
                      whileHover={{ scale: 1.02 }}
                      className="bg-gray-800/50 rounded-lg p-6 cursor-pointer"
                      onClick={() => setSelectedSchema(schema.name)}
                    >
                      <h3 className="text-white font-semibold text-lg mb-2">{schema.name}</h3>
                      <p className="text-gray-400 text-sm mb-4">{schema.description}</p>
                      <div className="space-y-2">
                        <div className="text-gray-500 text-xs uppercase tracking-wide">Tables</div>
                        <div className="flex flex-wrap gap-2">
                          {schema.tables.map((table) => (
                            <span
                              key={table.name}
                              className="px-2 py-1 bg-gray-900/50 text-gray-300 rounded text-sm"
                            >
                              {table.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </Tabs.Content>

              {/* Sample Queries Tab */}
              <Tabs.Content value="samples" className="space-y-6">
                {sampleQueries && sampleQueries.map((sample, idx) => (
                  <motion.button
                    key={idx}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => loadSampleQuery(sample)}
                    className="text-left p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800/70 transition-colors mb-3"
                  >
                    <h4 className="text-white font-semibold mb-1">{sample.title}</h4>
                    <p className="text-gray-400 text-sm mb-2">{sample.description}</p>
                    <p className="text-gray-300 font-mono text-xs">{sample.query}</p>
                  </motion.button>
                ))}
              </Tabs.Content>
            </Tabs.Root>
          </div>
        </motion.div>
      </div>
    </div>
  );
}