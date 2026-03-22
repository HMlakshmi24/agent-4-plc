# backend/engine/confidence_score.py

class ConfidenceScoreCalculator:
    """
    Layer 13: Calculates a professional-grade transparency score based on 
    the generation history and warnings.
    """
    def __init__(self):
        self.score = 100
        self.reasons = []

    def apply_penalty(self, description: str, points: int):
        self.score -= points
        self.reasons.append(f"-{points}: {description}")

    def evaluate(self, history: dict) -> dict:
        """
        history dict should contain counts:
        - regenerations (guard retries)
        - fix_loops (semantic validator fails)
        - engineering_warnings
        - physical_warnings
        - semantic_warnings
        - fallback_used (bool)
        """
        
        if history.get("regenerations", 0) > 0:
            self.apply_penalty(f"Variable guard required {history['regenerations']} regeneration(s)", 15)

        if history.get("fix_loops", 0) > 0:
            self.apply_penalty(f"Semantic API fix loop triggered {history['fix_loops']} time(s)", 20)
            
        env_warns = history.get("engineering_warnings", 0)
        if env_warns > 0:
            self.apply_penalty(f"{env_warns} Engineering completeness warning(s)", 10)

        phys_warns = history.get("physical_warnings", 0)
        if phys_warns > 0:
            self.apply_penalty(f"{phys_warns} Physical Sequence warning(s)", 15)

        sem_warns = history.get("semantic_warnings", 0)
        if sem_warns > 0:
            self.apply_penalty(f"{sem_warns} Semantic code warning(s)", 10)

        if history.get("fallback_used", False):
            self.apply_penalty(f"Generator fell back to non-template deterministic stub", 40)

        final_score = max(0, self.score)

        return {
            "confidence": final_score,
            "reasons": self.reasons,
            "rating": "EXCELLENT" if final_score >= 90 else "GOOD" if final_score >= 70 else "MARGINAL" if final_score >= 50 else "POOR"
        }
