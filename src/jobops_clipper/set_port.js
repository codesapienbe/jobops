const fs = require('fs');
const os = require('os');
const path = require('path');

// Read port from ~/.jobops/jobops_api_port.txt
const portFile = path.join(os.homedir(), '.jobops', 'jobops_api_port.txt');
let port = '8000'; // fallback default
try {
  port = fs.readFileSync(portFile, 'utf-8').trim();
  if (!/^[0-9]+$/.test(port)) throw new Error('Invalid port');
} catch (e) {
  console.warn(`Could not read port from ${portFile}, using default 8000.`, e.message);
}

const configPath = path.join(__dirname, 'src', 'config.ts');
fs.writeFileSync(configPath, `export const BACKEND_API_BASE = "http://localhost:${port}";\n`);
console.log(`Set BACKEND_API_BASE to http://localhost:${port}`); 