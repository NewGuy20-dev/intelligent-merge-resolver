from __future__ import annotations
import os
import sys
import json
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli() -> None:
	"""Intelligent Merge Resolver CLI"""

@cli.command()
@click.option('--project-path', default='.', help='Path to project')
@click.option('--project-type', default=None, help='Project type (react, vue, etc.)')
def init(project_path: str, project_type: str | None) -> None:
	"""Initialize merge resolver for a project"""
	console.print(f"Initializing at {project_path} (type={project_type})")
	os.makedirs(os.path.join(project_path, ".imr"), exist_ok=True)
	console.print("Done.")

@cli.command()
@click.option('--file', 'file_path', default=None, help='Specific file to analyze')
@click.option('--confidence-threshold', default=0.8, help='Auto-resolve threshold')
def analyze(file_path: str | None, confidence_threshold: float) -> None:
	"""Analyze and resolve merge conflicts"""
	from ..core.conflict_analyzer import ConflictAnalyzer
	analyzer = ConflictAnalyzer()
	if file_path and os.path.isfile(file_path):
		meta = analyzer.analyze_conflict(file_path)
		console.print(json.dumps(meta.__dict__, indent=2))
	else:
		console.print("No file provided or file missing.")

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