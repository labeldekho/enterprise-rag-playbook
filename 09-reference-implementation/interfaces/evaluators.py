"""
Evaluation Interface

Evaluators measure RAG system quality across retrieval and generation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from .retrievers import SearchResult


@dataclass
class EvaluationResult:
    """
    Results from evaluating a RAG query.

    Attributes:
        query: The original query
        retrieval_metrics: Retrieval quality metrics
        generation_metrics: Generation quality metrics
        overall_score: Combined quality score
        details: Additional evaluation details
    """
    query: str
    retrieval_metrics: dict = field(default_factory=dict)
    generation_metrics: dict = field(default_factory=dict)
    overall_score: float = 0.0
    details: dict = field(default_factory=dict)


@dataclass
class GoldenExample:
    """
    A test example with ground truth.

    Attributes:
        query: Test query
        relevant_doc_ids: IDs of relevant documents
        reference_answer: Expected answer
        metadata: Additional test metadata
    """
    query: str
    relevant_doc_ids: list[str]
    reference_answer: str
    metadata: dict = field(default_factory=dict)


class Evaluator(ABC):
    """
    Abstract base class for RAG evaluators.

    Implement this interface to measure:
    - Retrieval quality (recall, precision, MRR)
    - Generation quality (faithfulness, relevance)
    - End-to-end quality

    AGENT_ZONE: Implement evaluation metrics
    See: 06-evaluation/eval-metrics.md
    """

    @abstractmethod
    def evaluate(
        self,
        query: str,
        retrieved: list[SearchResult],
        generated_answer: str,
        golden: Optional[GoldenExample] = None
    ) -> EvaluationResult:
        """
        Evaluate a single RAG query.

        Args:
            query: Original query
            retrieved: Retrieved chunks
            generated_answer: Generated response
            golden: Ground truth (if available)

        Returns:
            EvaluationResult with metrics
        """
        pass

    def evaluate_batch(
        self,
        examples: list[dict]
    ) -> list[EvaluationResult]:
        """
        Evaluate multiple examples.

        Override for optimized batch evaluation.
        """
        return [
            self.evaluate(
                query=ex['query'],
                retrieved=ex['retrieved'],
                generated_answer=ex['generated_answer'],
                golden=ex.get('golden')
            )
            for ex in examples
        ]


# =============================================================================
# Example Implementations
# =============================================================================

class RetrievalEvaluator(Evaluator):
    """
    Evaluator focused on retrieval quality metrics.
    """

    def evaluate(
        self,
        query: str,
        retrieved: list[SearchResult],
        generated_answer: str,
        golden: Optional[GoldenExample] = None
    ) -> EvaluationResult:
        metrics = {}

        if golden and golden.relevant_doc_ids:
            retrieved_ids = [r.chunk.id for r in retrieved]
            relevant_ids = set(golden.relevant_doc_ids)

            # Calculate retrieval metrics
            metrics['recall@5'] = self._recall_at_k(retrieved_ids, relevant_ids, 5)
            metrics['recall@10'] = self._recall_at_k(retrieved_ids, relevant_ids, 10)
            metrics['precision@5'] = self._precision_at_k(retrieved_ids, relevant_ids, 5)
            metrics['mrr'] = self._mrr(retrieved_ids, relevant_ids)

        return EvaluationResult(
            query=query,
            retrieval_metrics=metrics,
            overall_score=metrics.get('recall@5', 0.0)
        )

    def _recall_at_k(
        self,
        retrieved_ids: list[str],
        relevant_ids: set[str],
        k: int
    ) -> float:
        if not relevant_ids:
            return 0.0
        retrieved_set = set(retrieved_ids[:k])
        return len(retrieved_set & relevant_ids) / len(relevant_ids)

    def _precision_at_k(
        self,
        retrieved_ids: list[str],
        relevant_ids: set[str],
        k: int
    ) -> float:
        if k == 0:
            return 0.0
        retrieved_set = set(retrieved_ids[:k])
        return len(retrieved_set & relevant_ids) / k

    def _mrr(
        self,
        retrieved_ids: list[str],
        relevant_ids: set[str]
    ) -> float:
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_ids:
                return 1.0 / rank
        return 0.0


class LLMEvaluator(Evaluator):
    """
    Evaluator using LLM to judge response quality.

    AGENT_ZONE: Configure evaluation prompts
    See: 06-evaluation/eval-metrics.md
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    def evaluate(
        self,
        query: str,
        retrieved: list[SearchResult],
        generated_answer: str,
        golden: Optional[GoldenExample] = None
    ) -> EvaluationResult:
        context = "\n\n".join([r.chunk.text for r in retrieved])

        metrics = {
            'faithfulness': self._evaluate_faithfulness(generated_answer, context),
            'relevance': self._evaluate_relevance(query, generated_answer),
        }

        if golden:
            metrics['correctness'] = self._evaluate_correctness(
                query, generated_answer, golden.reference_answer
            )

        overall = sum(metrics.values()) / len(metrics)

        return EvaluationResult(
            query=query,
            generation_metrics=metrics,
            overall_score=overall
        )

    def _evaluate_faithfulness(self, answer: str, context: str) -> float:
        prompt = f"""
Evaluate if the answer is faithful to (grounded in) the context.
Score from 0 to 1:
- 1.0: All claims in the answer are supported by the context
- 0.5: Some claims are supported, some are not
- 0.0: The answer contains claims that contradict or aren't in the context

Context:
{context}

Answer:
{answer}

Score (just the number):
"""
        response = self.llm.generate(prompt)
        try:
            return float(response.strip())
        except ValueError:
            return 0.0

    def _evaluate_relevance(self, query: str, answer: str) -> float:
        prompt = f"""
Evaluate if the answer is relevant to the question.
Score from 0 to 1:
- 1.0: Directly and completely answers the question
- 0.5: Partially answers or is tangentially related
- 0.0: Does not answer the question

Question: {query}
Answer: {answer}

Score (just the number):
"""
        response = self.llm.generate(prompt)
        try:
            return float(response.strip())
        except ValueError:
            return 0.0

    def _evaluate_correctness(
        self,
        query: str,
        answer: str,
        reference: str
    ) -> float:
        prompt = f"""
Compare the answer to the reference answer for correctness.
Score from 0 to 1:
- 1.0: The answer is factually correct and matches the reference
- 0.5: Partially correct
- 0.0: Incorrect

Question: {query}
Reference Answer: {reference}
Generated Answer: {answer}

Score (just the number):
"""
        response = self.llm.generate(prompt)
        try:
            return float(response.strip())
        except ValueError:
            return 0.0


class CompositeEvaluator(Evaluator):
    """
    Combines multiple evaluators for comprehensive assessment.
    """

    def __init__(self, evaluators: list[Evaluator], weights: list[float] = None):
        self.evaluators = evaluators
        self.weights = weights or [1.0] * len(evaluators)

    def evaluate(
        self,
        query: str,
        retrieved: list[SearchResult],
        generated_answer: str,
        golden: Optional[GoldenExample] = None
    ) -> EvaluationResult:
        all_retrieval_metrics = {}
        all_generation_metrics = {}
        weighted_scores = []

        for evaluator, weight in zip(self.evaluators, self.weights):
            result = evaluator.evaluate(query, retrieved, generated_answer, golden)
            all_retrieval_metrics.update(result.retrieval_metrics)
            all_generation_metrics.update(result.generation_metrics)
            weighted_scores.append(result.overall_score * weight)

        overall = sum(weighted_scores) / sum(self.weights)

        return EvaluationResult(
            query=query,
            retrieval_metrics=all_retrieval_metrics,
            generation_metrics=all_generation_metrics,
            overall_score=overall
        )


# =============================================================================
# Production Considerations
# =============================================================================

"""
When implementing evaluators for production:

1. Golden Dataset
   - Create and maintain test set
   - Include diverse query types
   - Update when documents change
   See: 06-evaluation/golden-datasets.md

2. Automated Evaluation
   - Run on every deployment
   - Track metrics over time
   - Alert on regressions

3. LLM-as-Judge
   - Use consistent prompts
   - Consider using stronger model for evaluation
   - Validate with human judgments periodically

4. Cost Management
   - LLM evaluation can be expensive
   - Sample for large-scale evaluation
   - Cache evaluation results

5. Reporting
   - Dashboard for metrics visualization
   - Trend analysis over time
   - Segment by query type, source, etc.
"""
