import { copyFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const source = fileURLToPath(new URL('../node_modules/sql.js/dist/sql-wasm.wasm', import.meta.url));
const publicDirectory = fileURLToPath(new URL('../public/', import.meta.url));
const destination = fileURLToPath(new URL('../public/sql-wasm.wasm', import.meta.url));

await mkdir(publicDirectory, { recursive: true });
await copyFile(source, destination);
console.log('Prepared public/sql-wasm.wasm from the locked sql.js package.');
