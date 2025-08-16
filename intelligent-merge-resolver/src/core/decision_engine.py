from __future__ import annotations
import typing as t
from dataclasses import dataclass, field

@dataclass
class ReasoningContext:
	layers: t.Dict[str, t.Any] = field(default_factory=dict)

	def get_previous_reasoning(self) -> t.Dict[str, t.Any]:
		return self.layers

	def add_reasoning_layer(self, layer_name: str, result: t.Any) -> None:
		self.layers[layer_name] = result

@dataclass
class DecisionSynthesisResult:
	decision: str
	confidence: float
	justification: str
	context_snapshot: t.Dict[str, t.Any]

class MergeReasoningEngine:
	def __init__(self, layers: t.Optional[t.List[t.Any]] = None) -> None:
		self.reasoning_chain = layers or []

	async def reason_through_merge(self, conflict_data: t.Dict[str, t.Any], threshold: float = 0.85) -> DecisionSynthesisResult:
		ctx = ReasoningContext()
		aggregate_conf = 0.0
		count = 0
		for layer in self.reasoning_chain:
			ctx = await layer.analyze(ctx)  # type: ignore
			conf = self._extract_confidence(layer.layer_name, ctx.layers.get(layer.layer_name))
			if conf is not None:
				aggregate_conf += conf
				count += 1
			# Early exit if consistently high
			if count >= 2 and (aggregate_conf / max(1, count)) >= threshold:
				return DecisionSynthesisResult(
					decision="keep_current",
					confidence=min(1.0, aggregate_conf / max(1, count)),
					justification=f"High confidence after {layer.layer_name}",
					context_snapshot=ctx.layers,
				)
		avg_conf = aggregate_conf / max(1, count)
		return DecisionSynthesisResult(
			decision="keep_current" if avg_conf >= 0.5 else "manual_review",
			confidence=avg_conf,
			justification="Aggregated confidence across layers",
			context_snapshot=ctx.layers,
		)

	def _extract_confidence(self, layer_name: str, result: t.Any) -> t.Optional[float]:
		if isinstance(result, dict):
			for key in (f"{layer_name}_confidence", "confidence"):
				val = result.get(key)
				if isinstance(val, (int, float)):
					return float(val)
		return None