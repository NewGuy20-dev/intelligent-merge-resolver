const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

let _chalk;
async function getChalk() {
	if (_chalk) return _chalk;
	const mod = await import('chalk');
	_chalk = mod.default;
	return _chalk;
}

async function checkPython() {
	const pythonCmds = ['python3', 'python'];
	for (const cmd of pythonCmds) {
		try {
			const result = await new Promise((resolve) => {
				const child = spawn(cmd, ['--version']);
				child.on('exit', (code) => resolve(code === 0 ? cmd : null));
				child.on('error', () => resolve(null));
			});
			if (result) return result;
		} catch (_) {}
	}
	return null;
}

async function installPythonDeps(pythonCmd) {
	const chalk = await getChalk();
	console.log(chalk.blue('📦 Installing Python dependencies...'));
	return new Promise((resolve, reject) => {
		const child = spawn(pythonCmd, ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
			stdio: 'inherit',
			cwd: __dirname,
		});
		child.on('exit', (code) => {
			if (code === 0) {
				console.log(chalk.green('✅ Python dependencies installed'));
				resolve();
			} else {
				reject(new Error('Failed to install Python dependencies'));
			}
		});
	});
}

async function detectProjectType() {
	const cwd = process.cwd();
	const packageJsonPath = path.join(cwd, 'package.json');
	if (fs.existsSync(packageJsonPath)) {
		const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
		if ((pkg.dependencies && pkg.dependencies.next) || (pkg.devDependencies && pkg.devDependencies.next)) {
			return 'nextjs';
		}
	}
	if (fs.existsSync(path.join(cwd, 'nuxt.config.js'))) return 'nuxt';
	if (fs.existsSync(path.join(cwd, 'angular.json'))) return 'angular';
	if (fs.existsSync(path.join(cwd, 'vue.config.js'))) return 'vue';
	return 'generic';
}

async function main() {
	const chalk = await getChalk();
	try {
		console.log(chalk.cyan('🚀 Setting up Intelligent Merge Resolver...'));
		const pythonCmd = await checkPython();
		if (!pythonCmd) {
			console.log(chalk.red('❌ Python 3.8+ is required'));
			process.exit(1);
		}
		console.log(chalk.green(`✅ Found Python: ${pythonCmd}`));
		await installPythonDeps(pythonCmd);
		const projectType = await detectProjectType();
		console.log(chalk.blue(`🔍 Detected project type: ${projectType}`));
		const configPath = path.join(process.cwd(), '.merge-resolver.yaml');
		if (!fs.existsSync(configPath)) {
			const defaultConfig = `project:\n  type: "${projectType}"\n\npreferences:\n  ui_style: "modern"\n  code_style: "functional"\n  accessibility: "high"\n\nreasoning:\n  enable_visual_analysis: true\n  enable_context_analysis: true\n  confidence_threshold: 0.85\n  max_context_size: 50000\n`;
			fs.writeFileSync(configPath, defaultConfig);
			console.log(chalk.green('✅ Created default configuration'));
		}
		console.log(chalk.green('🎉 Setup complete! Run "npx merge-resolve --help" to get started.'));
	} catch (error) {
		const chalk = await getChalk();
		console.error(chalk.red('❌ Installation failed:'), error.message);
		process.exit(1);
	}
}

if (require.main === module) {
	main();
}