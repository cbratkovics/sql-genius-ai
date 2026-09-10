import Link from 'next/link';

export default function MetricsDashboard() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white p-8">
      <div className="max-w-3xl mx-auto bg-white/10 rounded-3xl p-8 border border-white/10">
        <h1 className="text-3xl font-bold mb-4">Evidence, not activity estimates</h1>
        <p className="text-gray-200 mb-6">
          The previous dashboard used randomly generated traffic, success, and latency values. Those values were
          not observations, so they have been removed. The playground now reports only provider round-trip timing
          returned by the current request and local execution status attached to the displayed SQL.
        </p>
        <div className="space-y-3 text-sm text-gray-300">
          <p><strong className="text-white">Implemented:</strong> deterministic sample schemas, curated SQLite queries, optional provider generation, and a read-only execution policy.</p>
          <p><strong className="text-white">Evaluated:</strong> focused contract and policy tests documented in the repository evidence file.</p>
          <p><strong className="text-white">Not measured:</strong> model accuracy, adoption, uptime, cost savings, or hosted performance.</p>
        </div>
        <Link href="/demo" className="inline-block mt-8 px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-500">Open the playground</Link>
      </div>
    </main>
  );
}
