#!/usr/bin/env node
const { spawn } = require('cross-spawn');
const path = require('path');
const chalk = require('chalk');

function findPython() {
	const pythonCmds = process.platform === 'win32' ? ['python', 'python3', 'py'] : ['python3', 'python'];
	for (const cmd of pythonCmds) {
		try {
			const result = spawn.sync(cmd, ['--version'], { stdio: 'pipe' });
			if (result.status === 0) return cmd;
		} catch (_) {}
	}
	return null;
}

function main() {
	const pythonCmd = findPython();
	if (!pythonCmd) {
		console.error(chalk.red('❌ Python 3.8+ is required but not found'));
		process.exit(1);
	}
	const scriptPath = path.join(__dirname, '..', 'src', 'python', 'cli', 'main.py');
	const args = [scriptPath, ...process.argv.slice(2)];
	const child = spawn(pythonCmd, args, { stdio: 'inherit', cwd: process.cwd() });
	child.on('exit', (code, signal) => {
		if (signal) process.kill(process.pid, signal); else process.exit(code || 0);
	});
	child.on('error', (error) => {
		console.error(chalk.red('❌ Failed to start merge resolver:'), error.message);
		process.exit(1);
	});
}

if (require.main === module) { main(); }

module.exports = { main };