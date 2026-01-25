#!/usr/bin/env node

/*
  intelligent-merge-resolver CLI
  - Main entrypoint: resolve git merge conflicts using Google's Generative AI
  - Commands:
    - resolve [files...]           Resolve conflicts in specified files or all
    - --interactive                Interactive mode
    - --config [key=value]         Show or set config (e.g., --config apiKey=...)
    - --version, --help            Standard
*/

const path = require('path');
const fs = require('fs');
const os = require('os');
const { Command } = require('commander');
let chalk; // loaded via dynamic import
let ora;   // loaded via dynamic import
const spawn = require('cross-spawn');

const packageJson = require(path.resolve(__dirname, '..', 'package.json'));

const CONFIG_FILENAME = '.merge-resolver.yaml';

function runGit(args, options = {}) {
	const result = spawn.sync('git', args, {
		cwd: options.cwd || process.cwd(),
		encoding: 'utf8'
	});
	if (result.error) {
		throw result.error;
	}
	if (result.status !== 0) {
		return { stdout: '', stderr: result.stderr || '', status: result.status };
	}
	return { stdout: result.stdout || '', stderr: result.stderr || '', status: 0 };
}

function getRepoRoot() {
	const res = runGit(['rev-parse', '--show-toplevel']);
	if (res.status === 0 && res.stdout.trim()) {
		return res.stdout.trim();
	}
	return process.cwd();
}

function readFileSafe(filePath) {
	try {
		return fs.readFileSync(filePath, 'utf8');
	} catch (e) {
		return null;
	}
}

function writeFileSafe(filePath, content) {
	fs.writeFileSync(filePath, content, 'utf8');
}

function ensureBackup(filePath) {
	const backupPath = filePath + '.imr.bak';
	if (!fs.existsSync(backupPath)) {
		fs.copyFileSync(filePath, backupPath);
	}
	return backupPath;
}

function parseSimpleYaml(text) {
	// Very small YAML reader for key: value (scalars only)
	const config = {};
	if (!text) return config;
	const lines = text.split(/\r?\n/);
	for (const line of lines) {
		const trimmed = line.trim();
		if (!trimmed || trimmed.startsWith('#')) continue;
		const idx = trimmed.indexOf(':');
		if (idx === -1) continue;
		const key = trimmed.substring(0, idx).trim();
		let value = trimmed.substring(idx + 1).trim();
		if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
			value = value.slice(1, -1);
		}
		// try to parse booleans/numbers
		if (value === 'true') value = true;
		else if (value === 'false') value = false;
		else if (!Number.isNaN(Number(value))) value = Number(value);
		config[key] = value;
	}
	return config;
}

function toSimpleYaml(obj) {
	return Object.entries(obj)
		.map(([k, v]) => `${k}: ${typeof v === 'string' ? JSON.stringify(v) : String(v)}`)
		.join(os.EOL) + os.EOL;
}

function loadConfig() {
	const repoRoot = getRepoRoot();
	const configPath = path.join(repoRoot, CONFIG_FILENAME);
	const defaults = {
		model: 'gemini-1.5-pro',
		temperature: 0.2,
	};
	const text = readFileSafe(configPath);
	const fileCfg = parseSimpleYaml(text || '');
	const envCfg = {
		apiKey: process.env.GOOGLE_API_KEY || fileCfg.apiKey || ''
	};
	return { ...defaults, ...fileCfg, ...envCfg, _path: configPath };
}

function saveConfig(updates) {
	const current = loadConfig();
	const toSave = { ...current, ...updates };
	delete toSave._path; // not persisted
	const yaml = toSimpleYaml(toSave);
	fs.writeFileSync(current._path, yaml, 'utf8');
	return current._path;
}

function detectConflictedFiles() {
	const res = runGit(['diff', '--name-only', '--diff-filter=U']);
	if (res.status !== 0) return [];
	return res.stdout
		.split(/\r?\n/)
		.map(s => s.trim())
		.filter(Boolean)
		.filter(p => fs.existsSync(path.join(process.cwd(), p)));
}

function parseConflictHunks(fileContent) {
	// Returns array of { startIndex, endIndex, head, incoming, marker }
	const lines = fileContent.split(/\r?\n/);
	const hunks = [];
	let i = 0;
	while (i < lines.length) {
		if (lines[i].startsWith('<<<<<<<')) {
			const startIndex = i;
			i++;
			const headLines = [];
			while (i < lines.length && !lines[i].startsWith('=======')) {
				headLines.push(lines[i]);
				i++;
			}
			if (i >= lines.length) break; // malformed
			// skip =======
			i++;
			const incomingLines = [];
			while (i < lines.length && !lines[i].startsWith('>>>>>>>')) {
				incomingLines.push(lines[i]);
				i++;
			}
			if (i >= lines.length) break; // malformed
			const endIndex = i;
			const marker = lines[endIndex]; // >>>>>>> something
			hunks.push({ startIndex, endIndex, head: headLines.join('\n'), incoming: incomingLines.join('\n'), marker });
		}
		i++;
	}
	return { hunks, lines };
}

async function suggestResolutionWithAI(conflict, config) {
	// Lazy ESM import to avoid requiring on --help
	const { GoogleGenerativeAI } = await import('@google/generative-ai');
	if (!config.apiKey) {
		throw new Error('Missing Google API Key. Set GOOGLE_API_KEY env or use --config apiKey=YOUR_KEY');
	}
	const genAI = new GoogleGenerativeAI(String(config.apiKey));
	const model = genAI.getGenerativeModel({ model: config.model || 'gemini-1.5-pro' });
	const systemInstruction = [
		'You are an expert software engineer helping resolve Git merge conflicts.',
		'Return ONLY the resolved content with no explanations and no markdown formatting.',
		'Preserve code style and semantics. Prefer non-destructive merges when possible.'
	].join(' ');
	const prompt = [
		systemInstruction,
		'Here is a merge conflict. Merge the two sides into a single best version.\n',
		'<<<<<<< HEAD (ours)\n',
		conflict.head,
		'\n=======\n',
		conflict.incoming,
		'\n>>>>>>> theirs\n',
		'Respond with only the resolved content.'
	].join('');
	const result = await model.generateContent({ contents: [{ role: 'user', parts: [{ text: prompt }]}], generationConfig: { temperature: Number(config.temperature) || 0.2 } });
	const text = (result && result.response && typeof result.response.text === 'function') ? result.response.text() : '';
	return (text || '').replace(/^```[\s\S]*?\n|```$/g, '').trim();
}

function applyResolutionsToContent(originalContent, parsed, resolutions) {
	// resolutions is array same length as parsed.hunks with strings to replace
	const { hunks, lines } = parsed;
	const out = [];
	let lastIndex = 0;
	for (let idx = 0; idx < hunks.length; idx++) {
		const h = hunks[idx];
		for (let k = lastIndex; k < h.startIndex; k++) {
			out.push(lines[k]);
		}
		out.push(resolutions[idx]);
		lastIndex = h.endIndex + 1; // skip marker line
	}
	for (let k = lastIndex; k < lines.length; k++) {
		out.push(lines[k]);
	}
	return out.join('\n');
}

async function interactiveApprove(promptText) {
	process.stdout.write(promptText);
	return new Promise(resolve => {
		process.stdin.setEncoding('utf8');
		const onData = (data) => {
			const input = String(data || '').trim().toLowerCase();
			process.stdin.off('data', onData);
			resolve(input);
		};
		process.stdin.on('data', onData);
	});
}

async function resolveFile(filePath, options, config) {
	const fullPath = path.resolve(process.cwd(), filePath);
	const content = readFileSafe(fullPath);
	if (content == null) {
		console.log(chalk.red(`✖ Unable to read ${filePath}`));
		return { file: filePath, changed: false };
	}
	const parsed = parseConflictHunks(content);
	if (!parsed.hunks.length) {
		console.log(chalk.gray(`- No conflicts found in ${filePath}`));
		return { file: filePath, changed: false };
	}
	const spinner = ora({ text: `Analyzing ${filePath} (${parsed.hunks.length} conflict${parsed.hunks.length > 1 ? 's' : ''})`, color: 'cyan' }).start();
	const resolutions = [];
	try {
		for (let i = 0; i < parsed.hunks.length; i++) {
			spinner.text = `Generating suggestion ${i + 1}/${parsed.hunks.length} for ${filePath}`;
			const suggestion = await suggestResolutionWithAI(parsed.hunks[i], config);
			if (options.interactive) {
				spinner.stop();
				console.log(chalk.yellow(`\nFile: ${filePath} — Conflict ${i + 1}/${parsed.hunks.length}`));
				console.log(chalk.blue('Ours:'));
				console.log(parsed.hunks[i].head.length ? parsed.hunks[i].head : chalk.gray('(empty)'));
				console.log(chalk.magenta('\nTheirs:'));
				console.log(parsed.hunks[i].incoming.length ? parsed.hunks[i].incoming : chalk.gray('(empty)'));
				console.log(chalk.green('\nSuggested resolution:'));
				console.log(suggestion.length ? suggestion : chalk.gray('(empty)'));
				const input = await interactiveApprove(chalk.cyan('Accept suggestion? [y]es/[n]o/[s]kip/[q]uit: '));
				if (input === 'q') {
					console.log(chalk.red('Aborted by user.'));
					return { file: filePath, changed: false, aborted: true };
				}
				if (input === 'n' || input === 's') {
					// keep markers to resolve later
					resolutions.push(['<<<<<<< OURS', parsed.hunks[i].head, '=======', parsed.hunks[i].incoming, parsed.hunks[i].marker].join('\n'));
					spinner.start();
					continue;
				}
				// default accept
				resolutions.push(suggestion);
				spinner.start();
			} else {
				resolutions.push(suggestion);
			}
		}
		spinner.text = `Applying resolutions to ${filePath}`;
		const newContent = applyResolutionsToContent(content, parsed, resolutions);
		ensureBackup(fullPath);
		writeFileSafe(fullPath, newContent);
		spinner.succeed(`Resolved: ${filePath}`);
		return { file: filePath, changed: true };
	} catch (e) {
		spinner.fail(`Failed on ${filePath}: ${e.message}`);
		return { file: filePath, changed: false, error: e };
	}
}

async function resolveAll(files, options) {
	await ensureUiDeps();
	const config = loadConfig();
	if (!config.apiKey) {
		console.log(chalk.red('Missing Google API Key: set env GOOGLE_API_KEY or run:'));
		console.log(chalk.yellow('  merge-resolve --config apiKey=YOUR_KEY'));
		process.exitCode = 2;
		return;
	}
	const targets = files.length ? files : detectConflictedFiles();
	if (!targets.length) {
		console.log(chalk.green('✔ No merge conflicts detected.'));
		return;
	}
	console.log(chalk.cyan(`Detected ${targets.length} conflicted file${targets.length > 1 ? 's' : ''}.`));
	const results = [];
	for (const f of targets) {
		// eslint-disable-next-line no-await-in-loop
		const r = await resolveFile(f, options, config);
		if (r && r.aborted) break;
		results.push(r);
	}
	const changed = results.filter(r => r && r.changed).length;
	console.log(chalk.bold(`\nSummary: ${changed}/${targets.length} file(s) updated.`));
	console.log(chalk.gray('Backups saved with .imr.bak suffix.'));
}

async function handleConfigOption(value) {
	await ensureUiDeps();
	if (typeof value === 'string' && value.includes('=')) {
		const [key, ...rest] = value.split('=');
		const val = rest.join('=');
		const pathSaved = saveConfig({ [key.trim()]: val.trim() });
		console.log(chalk.green(`Updated '${key.trim()}' in ${pathSaved}`));
		return;
	}
	const cfg = loadConfig();
	const shown = { ...cfg };
	delete shown._path;
	console.log(chalk.cyan('Current configuration:'));
	for (const [k, v] of Object.entries(shown)) {
		const display = (k.toLowerCase().includes('key') && v) ? `${String(v).slice(0, 5)}***` : v;
		console.log(`- ${k}: ${display}`);
	}
	console.log(chalk.gray(`Config file: ${cfg._path}`));
}

async function main(argv) {
	const program = new Command();
	let executedCommand = false;

	program
		.name('merge-resolve')
		.description('AI-powered Git merge conflict resolver')
		.version(packageJson.version)
		.option('--config [key=value]', 'Show or set configuration (e.g. --config apiKey=XXXX)');

	program
		.command('resolve')
		.argument('[files...]', 'specific files to resolve')
		.option('-i, --interactive', 'interactive mode', false)
		.description('Resolve merge conflicts in the current repo')
		.action(async (files = [], opts) => {
			executedCommand = true;
			await resolveAll(files, { interactive: !!opts.interactive });
		});

	program.parse(argv);
	const options = program.opts();
	if (!executedCommand) {
		if (Object.prototype.hasOwnProperty.call(options, 'config')) {
			await handleConfigOption(options.config);
			return;
		}
		// default: same as help
		await ensureUiDeps();
		program.help();
	}
}

async function ensureUiDeps() {
	if (!chalk) {
		const m = await import('chalk');
		chalk = m.default || m;
	}
	if (!ora) {
		const m = await import('ora');
		ora = m.default || m;
	}
}

(async () => {
	try {
		await main(process.argv);
	} catch (err) {
		const red = chalk && typeof chalk.red === 'function' ? chalk.red : (s) => s;
		console.error(red(`Unexpected error: ${err && err.message ? err.message : String(err)}`));
		process.exitCode = 1;
	}
})();