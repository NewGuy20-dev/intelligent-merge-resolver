from __future__ import annotations
import os
import sys
import json
import asyncio
import click
from rich.console import Console
from rich.table import Table
from .utils.config_loader import load_config
from ..integrations.git_integration import GitIntegration
from ..reasoning.contextual_reasoning import ContextualReasoning
from ..reasoning.semantic_reasoning import SemanticReasoning
from ..reasoning.visual_reasoning import VisualReasoning
from ..reasoning.impact_reasoning import ImpactReasoning
from ..reasoning.consistency_reasoning import ConsistencyReasoning
from ..reasoning.meta_reasoning import MetaReasoning
from ..core.decision_engine import MergeReasoningEngine
from ..core.resolution import resolve_conflicts_in_text
from ..core.backup import BackupManager, DecisionLogger

console = Console()

@click.group()
def cli() -> None:
	"""Intelligent Merge Resolver CLI"""

@cli.command()
@click.option('--project-path', default='.', help='Path to project')
@click.option('--project-type', default=None, help='Project type (react, vue, etc.)')
def init(project_path: str, project_type: str | None) -> None:
	"""Initialize merge resolver for a project"""
	cfg = load_config(project_path)
	console.print(f"Initializing at {project_path} (type={project_type or cfg['project']['type']})")
	os.makedirs(os.path.join(project_path, ".imr"), exist_ok=True)
	GitIntegration(project_path).install_hooks()
	console.print("Hooks installed. Done.")

@cli.command()
@click.option('--file', 'file_path', default=None, help='Specific file to analyze')
@click.option('--confidence-threshold', default=0.8, help='Auto-resolve threshold')
def analyze(file_path: str | None, confidence_threshold: float) -> None:
	"""Analyze and resolve merge conflicts"""
	from ..core.conflict_analyzer import ConflictAnalyzer
	cfg = load_config('.')
	analyzer = ConflictAnalyzer()
	if file_path and os.path.isfile(file_path):
		meta = analyzer.analyze_conflict(file_path)
		console.print(json.dumps(meta.__dict__, indent=2))
	else:
		gi = GitIntegration('.')
		conflicts = gi.detect_conflicts()
		console.print(json.dumps([c.__dict__ for c in conflicts], indent=2))

@cli.command()
@click.option('--auto', is_flag=True, help='Attempt auto resolution using reasoning engine')
@click.option('--confidence-threshold', default=0.85, help='Threshold for auto merge')
@click.option('--choice', type=click.Choice(['current', 'incoming']), default='current', help='Fallback resolution choice')
def resolve(auto: bool, confidence_threshold: float, choice: str) -> None:
	"""Resolve detected merge conflicts"""
	gi = GitIntegration('.')
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
		# Run reasoning chain
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
		dl.log({
			"file": c.file_path,
			"choice": final_choice,
			"auto": bool(result),
			"confidence": conf,
		})
	console.print("Resolution complete. Backups saved under .imr/backups.")

@cli.command()
def status() -> None:
	"""Show merge resolver status and statistics"""
	t = Table(title="Merge Resolver Status")
	t.add_column("Metric")
	t.add_column("Value")
	t.add_row("conflicts_resolved", "0")
	t.add_row("avg_confidence", "0.0")
	console.print(t)

if __name__ == '__main__':
	cli()