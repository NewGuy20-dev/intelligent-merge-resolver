const fs = require('fs');
const path = require('path');

async function captureScreenshots({ projectPath = '.', baseUrl = 'http://localhost:3000', routes = ['/'], outDir = 'screenshots', viewports = [{ width: 1280, height: 800, name: 'desktop' }, { width: 375, height: 812, name: 'mobile' }] }) {
	let puppeteer;
	try {
		puppeteer = require('puppeteer');
	} catch (e) {
		return { error: 'puppeteer_not_installed' };
	}
	fs.mkdirSync(outDir, { recursive: true });
	const browser = await puppeteer.launch({ headless: 'new' });
	try {
		const results = [];
		for (const route of routes) {
			for (const vp of viewports) {
				const page = await browser.newPage();
				await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
				const url = baseUrl.replace(/\/$/, '') + route;
				await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
				await page.waitForTimeout(500);
				const safeRoute = route.replace(/[^a-z0-9]/gi, '_');
				const file = path.join(outDir, `${safeRoute}_${vp.name}.png`);
				await page.screenshot({ path: file, fullPage: true });
				await page.close();
				results.push({ route, viewport: vp.name, file });
			}
		}
		return { results };
	} finally {
		await browser.close();
	}
}

if (require.main === module) {
	(async () => {
		try {
			const args = JSON.parse(process.argv[2] || '{}');
			const res = await captureScreenshots(args);
			process.stdout.write(JSON.stringify(res));
			process.exit(0);
		} catch (e) {
			process.stdout.write(JSON.stringify({ error: String(e && e.message || e) }));
			process.exit(1);
		}
	})();
}

module.exports = { captureScreenshots };