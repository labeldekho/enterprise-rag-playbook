# A/B Testing

Validating RAG improvements in production.

## Why A/B Test RAG?

Offline evaluation has limits:
- Golden datasets don't capture all query patterns
- User behavior differs from annotator behavior
- Real-world conditions reveal issues

A/B testing answers: "Does this change actually help users?"

## A/B Testing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Traffic Router                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │    Assignment       │
                    │    (User/Session)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                  │
              ▼                                  ▼
       ┌─────────────┐                   ┌─────────────┐
       │   Control   │                   │  Treatment  │
       │   (Old RAG) │                   │  (New RAG)  │
       └──────┬──────┘                   └──────┬──────┘
              │                                  │
              └────────────────┬─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   Metrics Logger    │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │   Analysis Engine   │
                    └─────────────────────┘
```

## What to A/B Test

### High-Impact Changes
- Embedding model swap
- Retrieval strategy (vector → hybrid)
- Chunk size changes
- Reranking introduction
- Prompt template changes

### Lower-Impact Changes
- Minor prompt tweaks
- k parameter adjustments
- Threshold tuning

### Don't A/B Test
- Bug fixes (just ship them)
- Security patches
- Clearly broken changes

## Experiment Design

### Traffic Split
```python
class ExperimentRouter:
    def __init__(self, experiment_config):
        self.config = experiment_config

    def assign_variant(self, user_id):
        """
        Deterministic assignment based on user_id hash.
        Ensures same user always gets same variant.
        """
        hash_value = hash(f"{self.config.experiment_id}:{user_id}")
        bucket = hash_value % 100

        if bucket < self.config.control_percent:
            return 'control'
        else:
            return 'treatment'

    def route_request(self, request):
        variant = self.assign_variant(request.user_id)

        if variant == 'control':
            return self.config.control_pipeline
        else:
            return self.config.treatment_pipeline
```

### Sample Size Calculation
```python
from scipy import stats

def calculate_sample_size(
    baseline_metric,
    minimum_detectable_effect,
    alpha=0.05,
    power=0.80
):
    """
    Calculate required sample size per variant.

    baseline_metric: current metric value (e.g., 0.75 for 75% satisfaction)
    minimum_detectable_effect: smallest improvement worth detecting (e.g., 0.05)
    alpha: significance level (typically 0.05)
    power: statistical power (typically 0.80)
    """
    effect_size = minimum_detectable_effect / baseline_metric
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(n)

# Example: detecting 5% improvement in 75% satisfaction
sample_size = calculate_sample_size(0.75, 0.05)
# Result: ~1,200 samples per variant
```

## Metrics for A/B Tests

### Primary Metrics
Choose one or two as decision criteria:

| Metric | Description | Good For |
|--------|-------------|----------|
| Task completion | User achieved goal | Transactional queries |
| User satisfaction | Explicit feedback | General quality |
| Answer acceptance | User used the answer | Recommendation |
| Query refinement rate | User had to re-query | Search quality |

### Secondary Metrics
Monitor but don't decide on:
- Latency
- Error rate
- Engagement metrics
- Cost per query

### Guardrail Metrics
Must not degrade:
- Error rate < threshold
- Latency p99 < threshold
- User complaints

## Implementation

### Logging Requirements
```python
@dataclass
class ExperimentLog:
    timestamp: datetime
    experiment_id: str
    variant: str
    user_id: str
    session_id: str
    query: str
    response: str
    retrieved_doc_ids: List[str]
    latency_ms: float
    # Outcome metrics (may be logged later)
    user_feedback: Optional[str]
    task_completed: Optional[bool]
    follow_up_query: Optional[str]

def log_experiment_event(event: ExperimentLog):
    # Log to analytics system
    analytics.track('rag_experiment', event.to_dict())
```

### Feedback Collection
```python
def collect_feedback(session_id, response_id):
    """
    Collect explicit user feedback on response quality.
    """
    return {
        'helpful': request_binary_feedback("Was this helpful?"),
        'rating': request_rating("Rate this response (1-5)"),
        'issue': request_optional_text("What could be improved?")
    }
```

## Analysis

### Basic Analysis
```python
import pandas as pd
from scipy import stats

def analyze_experiment(logs_df):
    control = logs_df[logs_df['variant'] == 'control']
    treatment = logs_df[logs_df['variant'] == 'treatment']

    # Calculate metrics
    control_satisfaction = control['user_satisfied'].mean()
    treatment_satisfaction = treatment['user_satisfied'].mean()

    # Statistical test
    stat, p_value = stats.chi2_contingency([
        [control['user_satisfied'].sum(), len(control) - control['user_satisfied'].sum()],
        [treatment['user_satisfied'].sum(), len(treatment) - treatment['user_satisfied'].sum()]
    ])[:2]

    return {
        'control_rate': control_satisfaction,
        'treatment_rate': treatment_satisfaction,
        'relative_improvement': (treatment_satisfaction - control_satisfaction) / control_satisfaction,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
```

### Confidence Intervals
```python
def confidence_interval(successes, trials, confidence=0.95):
    """
    Calculate Wilson score confidence interval.
    """
    from statsmodels.stats.proportion import proportion_confint

    lower, upper = proportion_confint(
        successes,
        trials,
        alpha=1-confidence,
        method='wilson'
    )
    return lower, upper
```

### Segment Analysis
```python
def segment_analysis(logs_df, segments=['query_type', 'user_type']):
    """
    Analyze experiment results by segment.
    May reveal that treatment helps some users but not others.
    """
    results = {}

    for segment in segments:
        segment_results = {}
        for segment_value in logs_df[segment].unique():
            segment_df = logs_df[logs_df[segment] == segment_value]
            segment_results[segment_value] = analyze_experiment(segment_df)
        results[segment] = segment_results

    return results
```

## Decision Framework

### When to Ship Treatment
- Primary metric significantly improved (p < 0.05)
- No guardrail metrics degraded
- Secondary metrics acceptable
- Sufficient sample size reached

### When to Stop Early
```python
def should_stop_early(results, min_samples=1000):
    """
    Stop if clearly winning or losing.
    """
    if results['total_samples'] < min_samples:
        return False, "Need more samples"

    # Clear winner
    if results['p_value'] < 0.01 and results['relative_improvement'] > 0.1:
        return True, "Clear winner - ship treatment"

    # Clear loser
    if results['p_value'] < 0.01 and results['relative_improvement'] < -0.05:
        return True, "Clear loser - keep control"

    # Guardrail violated
    if results['error_rate_treatment'] > results['error_rate_threshold']:
        return True, "Guardrail violated - keep control"

    return False, "Continue experiment"
```

### Inconclusive Results
If no significant difference after sufficient samples:
- Treatment is likely neutral
- Consider if it has other benefits (simpler, cheaper)
- May ship anyway if no downsides

## Common Pitfalls

### 1. Peeking at Results
**Problem:** Checking results too often inflates false positive rate
**Fix:** Pre-define analysis schedule, use sequential testing

### 2. Segment Hunting
**Problem:** Testing many segments finds spurious effects
**Fix:** Pre-define segments, apply multiple comparison correction

### 3. Short Test Duration
**Problem:** Day-of-week effects, novelty effects
**Fix:** Run for at least 1-2 weeks

### 4. Logging Bugs
**Problem:** Missing or incorrect experiment logs
**Fix:** Validate logging before launch, monitor completeness

### 5. Network Effects
**Problem:** Users in different variants interact
**Fix:** Use cluster randomization if needed

## Checklist

- [ ] Experiment hypothesis defined
- [ ] Primary metric chosen
- [ ] Sample size calculated
- [ ] Experiment duration planned (1-2 weeks minimum)
- [ ] Logging implemented and validated
- [ ] Assignment deterministic (same user → same variant)
- [ ] Guardrail metrics defined
- [ ] Analysis plan written
- [ ] Rollback plan ready
- [ ] Stakeholders informed

---

**Previous:** [Golden Datasets](./golden-datasets.md)
**Next:** [Failure Analysis](./failure-analysis.md)
