"""Typed domain schemas and Pydantic v2 models for AI Code Review Assistant."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class CategoryEnum(str, Enum):
    """Categories of code review findings."""

    SYNTAX_ERROR = "syntax_error"
    LOGICAL_BUG = "logical_bug"
    RUNTIME_PROBLEM = "runtime_problem"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    BEST_PRACTICE = "best_practice"
    ERROR_HANDLING = "error_handling"
    RESOURCE_MANAGEMENT = "resource_management"
    DUPLICATE_LOGIC = "duplicate_logic"
    EDGE_CASE = "edge_case"


class SeverityEnum(str, Enum):
    """Deterministic severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class DetectionSourceEnum(str, Enum):
    """Origin of the reported issue."""

    STATIC = "static"
    AI = "ai"
    BOTH = "both"


class ValidationStatusEnum(str, Enum):
    """Validation state for generated fixes and tests."""

    NOT_VALIDATED = "not_validated"
    PASSED = "passed"
    FAILED = "failed"
    REGENERATED_PASSED = "regenerated_passed"


class Fix(BaseModel):
    """Suggested code remediation model."""

    suggested_fix: str = Field(description="Plain-language explanation of suggested fix")
    corrected_code: str = Field(description="Corrected code snippet")
    diff: Optional[str] = Field(default=None, description="Unified diff between original and fixed code")
    validation_status: ValidationStatusEnum = Field(
        default=ValidationStatusEnum.NOT_VALIDATED,
        description="Syntax and re-scan validation status",
    )
    validation_notes: Optional[str] = Field(default=None, description="Validation failure details if any")


class GeneratedTest(BaseModel):
    """Automatically generated test case model."""

    issue_id: str = Field(description="ID of the issue this test targets")
    test_code: str = Field(description="Executable pytest test code")
    explanation: str = Field(description="One-sentence plain language explanation of what the test verifies")
    target_category: CategoryEnum = Field(description="Category of targeted issue")
    validation_status: ValidationStatusEnum = Field(
        default=ValidationStatusEnum.NOT_VALIDATED,
        description="Syntax validation status",
    )


class Issue(BaseModel):
    """Core structured code review issue model."""

    issue_id: str = Field(description="Unique, stable ID within session")
    category: CategoryEnum = Field(description="Issue classification category")
    severity: SeverityEnum = Field(description="Computed deterministic severity level")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    file: str = Field(default="submitted_snippet", description="Filename or identifier")
    line_start: int = Field(ge=1, description="1-indexed starting line number")
    line_end: int = Field(ge=1, description="1-indexed ending line number")
    column: Optional[int] = Field(default=None, ge=0, description="Optional column offset")
    code_snippet: str = Field(description="Exact code excerpt from submitted code")
    description: str = Field(description="Short statement of the issue")
    why_it_matters: str = Field(description="Plain-language explanation of impact")
    root_cause: Optional[str] = Field(default=None, description="Underlying technical cause")
    fix: Optional[Fix] = Field(default=None, description="Associated code fix recommendation")
    generated_test: Optional[GeneratedTest] = Field(default=None, description="Associated generated test case")
    detection_source: DetectionSourceEnum = Field(description="Origin: static, ai, or both")
    detecting_tool: Optional[str] = Field(default=None, description="Tool name e.g., bandit, ast_walker")
    references: Optional[List[str]] = Field(default=None, description="Standard reference IDs e.g., CWE-89")

    @model_validator(mode="after")
    def validate_line_range(self) -> "Issue":
        """Ensures line_end is greater than or equal to line_start."""
        if self.line_end < self.line_start:
            raise ValueError(
                f"line_end ({self.line_end}) must be >= line_start ({self.line_start})"
            )
        return self


class DimensionScore(BaseModel):
    """Score breakdown for a single code quality dimension."""

    dimension_name: str = Field(description="Name of quality dimension")
    score: float = Field(ge=0.0, le=100.0, description="Dimension score out of 100")
    weight: float = Field(ge=0.0, le=1.0, description="Dimension weight in overall score")
    deductions: float = Field(ge=0.0, description="Total point deductions in dimension")
    issue_count: int = Field(ge=0, description="Count of issues affecting dimension")


class CodeQualityScore(BaseModel):
    """Complete code quality score model."""

    overall_score: float = Field(ge=0.0, le=100.0, description="Weighted overall score out of 100")
    label: str = Field(description="Human-readable score category label")
    dimensions: List[DimensionScore] = Field(default_factory=list, description="Score breakdown by dimension")
    summary_notes: str = Field(default="", description="Summary explanation of score")


class ReviewSummary(BaseModel):
    """Aggregate summary statistics and executive analysis."""

    total_issues: int = Field(ge=0, default=0)
    critical_count: int = Field(ge=0, default=0)
    high_count: int = Field(ge=0, default=0)
    medium_count: int = Field(ge=0, default=0)
    low_count: int = Field(ge=0, default=0)
    informational_count: int = Field(ge=0, default=0)
    executive_summary: str = Field(default="", description="AI-generated executive overview")
    top_recommendations: List[str] = Field(default_factory=list, description="Top 3 recommended fixes")


class ReviewResult(BaseModel):
    """Complete code review payload."""

    issues: List[Issue] = Field(default_factory=list)
    score: CodeQualityScore
    summary: ReviewSummary
    language: str = Field(default="python")
    submitted_code: str = Field(default="")
    corrected_full_code: Optional[str] = None
    aggregated_tests_code: Optional[str] = None


class PipelineError(BaseModel):
    """Pipeline error representation for graceful degradation."""

    error_type: str = Field(description="Class or identifier of error")
    message: str = Field(description="Human-readable error description")
    stage: str = Field(description="Pipeline stage where error occurred")
    is_fatal: bool = Field(default=False, description="Whether execution was halted")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PipelineResult(BaseModel):
    """Overall execution result returned by Orchestrator."""

    success: bool = Field(default=True)
    review_result: Optional[ReviewResult] = None
    errors: List[PipelineError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    is_partial_analysis: bool = Field(default=False)
    execution_time_seconds: float = Field(ge=0.0, default=0.0)
