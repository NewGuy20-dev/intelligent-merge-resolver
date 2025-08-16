from __future__ import annotations
import os
import typing as t
import yaml

_DEFAULTS = {
	"project": {"name": "Project", "type": "python"},
	"preferences": {"ui_style": "modern", "code_style": "mixed", "accessibility": "high"},
	"reasoning": {"enable_visual_analysis": False, "enable_context_analysis": True, "confidence_threshold": 0.85, "max_context_size": 50000},
	"build": {"dev_command": "", "build_command": "", "test_routes": ["/"]},
	"gemini": {"model": "gemini-2.0-flash-exp", "max_tokens": 8192},
}


def deep_merge(a: dict, b: dict) -> dict:
	out = dict(a)
	for k, v in b.items():
		if isinstance(v, dict) and isinstance(out.get(k), dict):
			out[k] = deep_merge(out[k], v)
		else:
			out[k] = v
	return out


def load_config(project_path: str) -> dict:
	user_path = os.path.join(project_path, ".merge-resolver.yaml")
	cfg = dict(_DEFAULTS)
	if os.path.isfile(user_path):
		with open(user_path, "r", encoding="utf-8") as f:
			user_cfg = yaml.safe_load(f) or {}
			cfg = deep_merge(cfg, user_cfg)
	return cfg