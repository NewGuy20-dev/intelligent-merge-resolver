from __future__ import annotations
import os
import sys
import json
import asyncio
import click
from rich.console import Console
from rich.table import Table

try:
	from ..integrations.js_bridge import JavaScriptBridge
except Exception:  # pragma: no cover
	JavaScriptBridge = None  # type: ignore

from ..integrations.git_integration import GitIntegration
from ..core.conflict_analyzer import ConflictAnalyzer
from ..core.decision_engine import MergeReasoningEngine
from ..reasoning.contextual_reasoning import ContextualReasoning
from ..reasoning.semantic_reasoning import SemanticReasoning
from ..reasoning.impact_reasoning import ImpactReasoning
from ..reasoning.consistency_reasoning import ConsistencyReasoning
from ..reasoning.meta_reasoning import MetaReasoning
from ..core.resolution import resolve_conflicts_in_text
from ..core.backup import BackupManager, DecisionLogger

console = Console()

@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx) -> None:
	"""🧠 Intelligent Merge Resolver - AI-powered conflict resolution"""
	ctx.ensure_object(dict)
	ctx.obj['git_integration'] = GitIntegration('.')
	ctx.obj['js_bridge'] = JavaScriptBridge() if JavaScriptBridge else None

@cli.command()
@click.option('--project-type', default=None, help='Project type (nextjs, react, vue, etc.)')
@click.option('--visual/--no-visual', default=True, help='Enable visual analysis')
@click.pass_context
def init(ctx, project_type: str | None, visual: bool) -> None:
	gi: GitIntegration = ctx.obj['git_integration']
	js: JavaScriptBridge | None = ctx.obj['js_bridge']
	if not project_type and js:
		project_type = js.detect_project_type()
	console.print(f"Detected project type: {project_type or 'generic'}")
	os.makedirs('.imr', exist_ok=True)
	gi.install_hooks()
	console.print("Hooks installed. Done.")

@cli.command()
@click.option('--file', 'file_path', default=None, help='Specific file to analyze')
@click.option('--confidence-threshold', default=0.8, help='Auto-resolve threshold')
@click.pass_context
def analyze(ctx, file_path: str | None, confidence_threshold: float) -> None:
	analyzer = ConflictAnalyzer()
	gi: GitIntegration = ctx.obj['git_integration']
	if file_path and os.path.isfile(file_path):
		meta = analyzer.analyze_conflict(file_path)
		console.print(json.dumps(meta.__dict__, indent=2))
	else:
		conflicts = gi.detect_conflicts()
		console.print(json.dumps([c.__dict__ for c in conflicts], indent=2))

@cli.command()
@click.option('--auto', is_flag=True, help='Attempt auto resolution using reasoning engine')
@click.option('--confidence-threshold', default=0.85, help='Threshold for auto merge')
@click.option('--choice', type=click.Choice(['current', 'incoming']), default='current', help='Fallback resolution choice')
@click.pass_context
def resolve(ctx, auto: bool, confidence_threshold: float, choice: str) -> None:
	gi: GitIntegration = ctx.obj['git_integration']
	conflicts = gi.detect_conflicts()
	if not conflicts:
		console.print("No conflicts detected.")
		return
	layers = [ContextualReasoning(), SemanticReasoning(), ImpactReasoning(), ConsistencyReasoning(), MetaReasoning()]
	engine = MergeReasoningEngine(layers)
	bm = BackupManager('.')
	dl = DecisionLogger('.')
	for c in conflicts:
		file_path = os.path.abspath(c.file_path)
		bm.backup_file(file_path)
		with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
			text = f.read()
		async def _run():
			return await engine.reason_through_merge({"file": c.file_path}, threshold=confidence_threshold)
		result = asyncio.run(_run()) if auto else None
		final_choice = choice
		conf = 0.0
		if result:
			final_choice = 'current' if result.decision == 'keep_current' else ('incoming' if result.decision == 'keep_incoming' else choice)
			conf = result.confidence
		resolved = resolve_conflicts_in_text(text, choice=final_choice)
		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(resolved)
		dl.log({"file": c.file_path, "choice": final_choice, "auto": bool(result), "confidence": conf})
	console.print("Resolution complete. Backups saved under .imr/backups.")

@cli.command()
@click.pass_context
def status(ctx) -> None:
	t = Table(title="Merge Resolver Status")
	t.add_column("Metric")
	t.add_column("Value")
	t.add_row("conflicts_resolved", "0")
	t.add_row("avg_confidence", "0.0")
	console.print(t)


def main() -> None:
	try:
		cli(obj={})
	except KeyboardInterrupt:
		console.print("\nCancelled")
		sys.exit(1)

if __name__ == '__main__':
	main()