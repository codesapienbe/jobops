// build.js
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Parse args
const args = process.argv.slice(2);
const getFlag = (name, def = false) => args.some(a => a === `--${name}`) ? true : def;
const getValue = (name, def = null) => {
  const found = args.find(a => a.startsWith(`--${name}=`));
  return found ? found.split('=')[1] : def;
};

const outDir = path.resolve(__dirname, getValue('outdir', '../../dist/extension/'));
const mode = getValue('mode', 'dev');
const isWatch = getFlag('watch', false);
const isMinify = getFlag('minify', mode === 'prod');
const isSourceMap = getFlag('sourcemap', true);

const logPath = path.join(__dirname, 'build.log');
function logStep(message) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] ${message}\n`;
  fs.appendFileSync(logPath, line);
  console.log(line.trim());
}

try {
  logStep('--- Build started ---');
  logStep(`Mode: ${mode} | watch=${isWatch} | minify=${isMinify} | sourcemap=${isSourceMap}`);
  logStep(`Output directory: ${outDir}`);
  logStep('Ensuring output directory exists...');
  fs.mkdirSync(outDir, { recursive: true });
  logStep('Output directory ready.');

  // TypeScript build (transpile only; bundling done by esbuild below)
  logStep('Running TypeScript build...');
  execSync(`tsc --outDir "${outDir}"`, { stdio: 'inherit' });
  logStep('TypeScript build completed.');

  logStep('Copying manifest and icon...');
  fs.copyFileSync(path.join(__dirname, 'manifest.json'), path.join(outDir, 'manifest.json'));
  fs.copyFileSync(path.join(__dirname, 'src', 'icon.png'), path.join(outDir, 'icon.png'));
  logStep('Manifest and icon copied.');

  const backendApiBase = process.env.BACKEND_API_BASE || 'http://localhost:8877';
  logStep(`Using BACKEND_API_BASE: ${backendApiBase}`);

  // Build command helper
  const esbuildBase = `esbuild --bundle --platform=browser ${isMinify ? '--minify' : ''} ${isSourceMap ? '--sourcemap' : ''}`;
  const defineBackend = `--define:process.env.BACKEND_API_BASE='\"${backendApiBase}\"'`;

  logStep('Bundling background.ts with esbuild...');
  execSync(`${esbuildBase} src/background.ts --outfile=${outDir}/background.js --format=iife ${defineBackend}`, { stdio: 'inherit' });
  logStep('background.ts bundled.');

  logStep('Bundling content.ts with esbuild...');
  execSync(`${esbuildBase} src/content.ts --outfile=${outDir}/content.js --format=iife ${defineBackend}`, { stdio: 'inherit' });
  logStep('content.ts bundled.');

  logStep('Bundling popup.ts with esbuild...');
  execSync(`${esbuildBase} src/popup.ts --outfile=${outDir}/popup.js --format=iife ${defineBackend}`, { stdio: 'inherit' });
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

  // Optional: rudimentary watch by re-running build on changes (simple, non-incremental)
  if (isWatch) {
    logStep('Entering watch mode (simple). Watching src/ for changes...');
    const chokidarPath = path.join(__dirname, 'node_modules', '.bin', 'chokidar');
    if (fs.existsSync(chokidarPath)) {
      // Use chokidar-cli if available
      const watchCmd = `${process.platform === 'win32' ? 'npx.cmd' : 'npx'} chokidar \"src/**/*\" -c \"node build.js --outdir=${outDir} --mode=${mode} ${isMinify ? '--minify' : ''} ${isSourceMap ? '--sourcemap' : ''}\"`;
      logStep(`Watch command: ${watchCmd}`);
      execSync(watchCmd, { stdio: 'inherit' });
    } else {
      logStep('chokidar not installed; watch mode requires manual re-run.');
    }
  }

  logStep('--- Build completed successfully ---');
} catch (err) {
  logStep(`ERROR: ${err && err.message ? err.message : err}`);
  logStep('--- Build failed ---');
  process.exit(1);
} 