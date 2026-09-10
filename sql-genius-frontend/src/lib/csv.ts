/** Serialize displayed cells without changing their on-screen values. */
function csvCell(value: unknown): string {
  if (value === null || value === undefined) return '';
  let text = typeof value === 'bigint' ? value.toString() : String(value);
  // Spreadsheet applications may interpret text prefixes as formulas. Numeric values,
  // including negative numbers, remain numeric; suspicious text is explicitly text.
  if (typeof value === 'string' && /^[=+\-@]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

export function rowsToCsv(columns: string[], rows: unknown[][]): string {
  return [columns.map(csvCell), ...rows.map((row) => row.map(csvCell))]
    .map((row) => row.join(','))
    .join('\r\n');
}
