const fs = require('fs');
const path = require('path');

function detectProjectType(cwd = process.cwd()) {
	const packageJsonPath = path.join(cwd, 'package.json');
	if (fs.existsSync(packageJsonPath)) {
		const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
		const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
		if (deps.next) return 'nextjs';
		if (deps.nuxt) return 'nuxt';
		if (deps['@angular/core']) return 'angular';
		if (deps.vue) return 'vue';
		if (deps.react) return 'react';
	}
	const configFiles = [
		{ file: 'next.config.js', type: 'nextjs' },
		{ file: 'nuxt.config.js', type: 'nuxt' },
		{ file: 'angular.json', type: 'angular' },
		{ file: 'vue.config.js', type: 'vue' },
	];
	for (const { file, type } of configFiles) {
		if (fs.existsSync(path.join(cwd, file))) return type;
	}
	return 'generic';
}

if (require.main === module) {
	const idx = process.argv.indexOf('--cwd');
	const cwd = idx >= 0 ? process.argv[idx + 1] : process.cwd();
	console.log(detectProjectType(cwd));
}

module.exports = { detectProjectType };