// build.js
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Parse --outdir argument or use default
const outDirArg = process.argv.find(arg => arg.startsWith('--outdir='));
const outDir = outDirArg ? path.resolve(process.cwd(), outDirArg.split('=')[1]) : path.resolve(__dirname, '../../dist/jobops_clipper/');

// Ensure output directory exists
fs.mkdirSync(outDir, { recursive: true });

// TypeScript build (respects tsconfig outDir, but we copy artifacts)
execSync(`tsc --outDir "${outDir}"`, { stdio: 'inherit' });

// Copy manifest and icon
fs.copyFileSync(path.join(__dirname, 'manifest.json'), path.join(outDir, 'manifest.json'));
fs.copyFileSync(path.join(__dirname, 'src', 'icon.png'), path.join(outDir, 'icon.png'));

// Bundle scripts with esbuild
execSync(`esbuild src/background.ts --bundle --platform=browser --outfile=${outDir}/background.js --format=iife`, { stdio: 'inherit' });
execSync(`esbuild src/content.ts --bundle --platform=browser --outfile=${outDir}/content.js --format=iife`, { stdio: 'inherit' });
execSync(`esbuild src/config.ts --bundle --platform=browser --outfile=${outDir}/config.js --format=iife`, { stdio: 'inherit' }); 