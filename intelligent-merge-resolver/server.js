const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

const PORT = process.env.IMR_SERVER_PORT ? Number(process.env.IMR_SERVER_PORT) : 3939;

function loadEnvLocal(cwd = process.cwd()) {
	const envPath = path.join(cwd, '.env.local');
	const env = {};
	if (!fs.existsSync(envPath)) return env;
	const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
	for (const raw of lines) {
		const line = raw.trim();
		if (!line || line.startsWith('#')) continue;
		const eq = line.indexOf('=');
		if (eq === -1) continue;
		const k = line.slice(0, eq).trim();
		let v = line.slice(eq + 1).trim();
		if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith('\'') && v.endsWith('\''))) {
			v = v.slice(1, -1);
		}
		env[k] = v;
	}
	return env;
}

const ENV = loadEnvLocal();
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || ENV.GEMINI_API_KEY || '';
let credits = 100;

function sendJson(res, status, obj) {
	const body = JSON.stringify(obj);
	res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
	res.end(body);
}

function notFound(res) { sendJson(res, 404, { error: 'not_found' }); }

async function handleGenerateJson(req, res, body) {
	if (!GEMINI_API_KEY) return sendJson(res, 500, { error: 'missing_gemini_api_key' });
	if (credits <= 0) return sendJson(res, 429, { error: 'rate_limit_exceeded', credits });
	let payload = {};
	try { payload = JSON.parse(body || '{}'); } catch (_) { payload = {}; }
	const prompt = String(payload.prompt || '');
	const systemInstruction = payload.system_instruction || undefined;
	if (!prompt) return sendJson(res, 400, { error: 'missing_prompt' });
	try {
		const { GoogleGenerativeAI } = await import('@google/generative-ai');
		const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
		const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp', systemInstruction });
		const response = await model.generateContent(prompt);
		credits -= 1;
		const text = response.response && response.response.text ? response.response.text() : (response.text ? response.text() : '');
		return sendJson(res, 200, { raw: text, credits });
	} catch (err) {
		return sendJson(res, 500, { error: String(err && err.message || err) });
	}
}

async function requestListener(req, res) {
	const { pathname } = url.parse(req.url);
	if (req.method === 'GET' && pathname === '/status') {
		return sendJson(res, 200, { credits, hasKey: Boolean(GEMINI_API_KEY) });
	}
	if (req.method === 'POST' && pathname === '/ai/generate-json') {
		let body = '';
		req.on('data', chunk => { body += chunk; });
		req.on('end', () => { handleGenerateJson(req, res, body); });
		return;
	}
	return notFound(res);
}

const server = http.createServer(requestListener);
server.listen(PORT, () => {
	console.log(`[imr-server] listening on http://127.0.0.1:${PORT} (credits=${credits})`);
});