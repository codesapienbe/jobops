// build.js
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Parse --outdir argument or use default
const outDirArg = process.argv.find(arg => arg.startsWith('--outdir='));
const outDir = outDirArg ? path.resolve(process.cwd(), outDirArg.split('=')[1]) : path.resolve(__dirname, '../../dist/extension/');

const logPath = path.join(__dirname, 'build.log');
function logStep(message) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] ${message}\n`;
  fs.appendFileSync(logPath, line);
  console.log(line.trim());
}

try {
  logStep('--- Build started ---');
  logStep(`Output directory: ${outDir}`);
  logStep('Ensuring output directory exists...');
  fs.mkdirSync(outDir, { recursive: true });
  logStep('Output directory ready.');

  logStep('Running TypeScript build...');
  execSync(`tsc --outDir "${outDir}"`, { stdio: 'inherit' });
  logStep('TypeScript build completed.');

  logStep('Copying manifest and icon...');
  fs.copyFileSync(path.join(__dirname, 'manifest.json'), path.join(outDir, 'manifest.json'));
  fs.copyFileSync(path.join(__dirname, 'src', 'icon.png'), path.join(outDir, 'icon.png'));
  logStep('Manifest and icon copied.');

  const backendApiBase = process.env.BACKEND_API_BASE || 'http://localhost:8877';
  logStep(`Using BACKEND_API_BASE: ${backendApiBase}`);

  logStep('Bundling background.ts with esbuild...');
  execSync(`esbuild src/background.ts --bundle --platform=browser --outfile=${outDir}/background.js --format=iife --define:process.env.BACKEND_API_BASE='"${backendApiBase}"'`, { stdio: 'inherit' });
  logStep('background.ts bundled.');

  logStep('Bundling content.ts with esbuild...');
  execSync(`esbuild src/content.ts --bundle --platform=browser --outfile=${outDir}/content.js --format=iife --define:process.env.BACKEND_API_BASE='"${backendApiBase}"'`, { stdio: 'inherit' });
  logStep('content.ts bundled.');

  logStep('Bundling popup.ts with esbuild...');
  execSync(`esbuild src/popup.ts --bundle --platform=browser --outfile=${outDir}/popup.js --format=iife --define:process.env.BACKEND_API_BASE='"${backendApiBase}"'`, { stdio: 'inherit' });
  logStep('popup.ts bundled.');

  logStep('Copying popup.html and popup.css...');
  fs.copyFileSync(path.join(__dirname, 'src', 'popup.html'), path.join(outDir, 'popup.html'));
  fs.copyFileSync(path.join(__dirname, 'src', 'popup.css'), path.join(outDir, 'popup.css'));
  logStep('popup.html and popup.css copied.');

  logStep('Copying locale files...');
  const localesDir = path.join(__dirname, 'src', 'locales');
  const outLocalesDir = path.join(outDir, 'src', 'locales');
  fs.mkdirSync(outLocalesDir, { recursive: true });
  
  const localeFiles = ['en.json', 'nl.json', 'fr.json', 'tr.json'];
  localeFiles.forEach(file => {
    const srcPath = path.join(localesDir, file);
    const destPath = path.join(outLocalesDir, file);
    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, destPath);
      logStep(`Copied ${file}`);
    } else {
      logStep(`Warning: ${file} not found`);
    }
  });
  logStep('Locale files copied.');

  logStep('--- Build completed successfully ---');
} catch (err) {
  logStep(`ERROR: ${err && err.message ? err.message : err}`);
  logStep('--- Build failed ---');
  process.exit(1);
} 