#!/usr/bin/env node

// Alias/shortcut to merge-resolve
const path = require('path');
const { spawn } = require('child_process');

const mainPath = path.resolve(__dirname, 'merge-resolve.js');

const child = spawn(process.execPath, [mainPath, ...process.argv.slice(2)], {
	stdio: 'inherit'
});
child.on('exit', (code, signal) => {
	if (signal) {
		process.kill(process.pid, signal);
	} else {
		process.exit(code);
	}
});