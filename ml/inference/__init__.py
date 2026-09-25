"""CYCLONEX Inference Package."""

def __getattr__(name: str):
    if name in ("CycloneInferencePipeline", "StructuredPrediction", "inference_pipeline"):
        from ml.inference import pipeline
        return getattr(pipeline, name)
    if name in ("CycloneExplainabilityEngine", "FeatureAttribution"):
        from ml.inference import explainability
        return getattr(explainability, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "CycloneInferencePipeline",
    "StructuredPrediction",
    "inference_pipeline",
    "CycloneExplainabilityEngine",
    "FeatureAttribution"
]

