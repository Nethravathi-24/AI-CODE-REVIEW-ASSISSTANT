"""Markdown Report Exporter conforming to ReportExporterProtocol and PRD Part 16."""

from core.interfaces import ReportExporterProtocol
from core.issue_model import ReviewResult, SeverityEnum


class MarkdownReportExporter(ReportExporterProtocol):
    """Serializes ReviewResult payload into structured Markdown report."""

    def export(self, result: ReviewResult) -> str:
        """Exports ReviewResult as structured human-readable Markdown string."""
        if not result:
            return "# Code Review Report\n\nNo review data available."

        lang_clean = (result.language or "python").lower()
        if lang_clean in ("python", "py"):
            parser_info = "Python AST (`ast.parse`) | FULL Validation"
            analyzer_info = "AST Structural, Pyflakes, Bandit, Radon, Pycodestyle"
        elif lang_clean in ("javascript", "js", "jsx"):
            parser_info = "Esprima ECMAScript AST | FULL Validation"
            analyzer_info = "JSAnalyzer (Esprima AST Walker)"
        elif lang_clean in ("typescript", "ts", "tsx"):
            parser_info = "Tree-Sitter TypeScript AST | FULL Validation"
            analyzer_info = "TSAnalyzer (Tree-Sitter AST Walker)"
        elif lang_clean == "java":
            parser_info = "Javalang AST / javac Compiler | FULL Validation"
            analyzer_info = "JavaAnalyzer (Javalang AST Walker & javac)"
        else:
            parser_info = "None | PARTIAL (AI Fallback)"
            analyzer_info = "None"

        static_count = sum(1 for i in result.issues if i.detection_source.value in ("static", "both"))
        ai_count = sum(1 for i in result.issues if i.detection_source.value in ("ai", "both"))

        lines = [
            "# 🛡️ AI Code Review Assistant — Executive Report",
            "",
            "## 1. Executive Summary",
            f"**Overall Score:** `{result.score.overall_score}/100` ({result.score.label})",
            f"**Language:** `{result.language.upper()}`",
            f"**Syntax Parser & Validation:** {parser_info}",
            f"**Active Static Analyzers:** {analyzer_info}",
            f"**Findings Breakdown:** Total: `{len(result.issues)}` | Static: `{static_count}` | AI Reasoning: `{ai_count}`",
            f"**Execution Summary:** {result.summary.executive_summary}",
            "",
            "### Severity Distribution",
            f"- **Critical:** {result.summary.critical_count}",
            f"- **High:** {result.summary.high_count}",
            f"- **Medium:** {result.summary.medium_count}",
            f"- **Low:** {result.summary.low_count}",
            f"- **Informational:** {result.summary.informational_count}",
            "",
            "## 2. Code Quality Breakdown (7 Dimensions)",
            "| Dimension | Score | Weight | Deductions | Issues |",
            "|---|---|---|---|---|",
        ]

        for dim in result.score.dimensions:
            lines.append(
                f"| **{dim.dimension_name}** | `{dim.score}/100` | {int(dim.weight*100)}% | -{dim.deductions} | {dim.issue_count} |"
            )

        lines.extend([
            "",
            "## 3. Findings & Security Audit Results",
        ])

        if not result.issues:
            lines.append("✅ **No code quality or security issues detected.**")
        else:
            for idx, issue in enumerate(result.issues, 1):
                sev_icon = "🔴" if issue.severity in (SeverityEnum.CRITICAL, SeverityEnum.HIGH) else ("🟡" if issue.severity == SeverityEnum.MEDIUM else "🔵")
                lines.extend([
                    f"### Finding #{idx}: {sev_icon} [{issue.severity.value.upper()}] {issue.description}",
                    f"- **Category:** `{issue.category.value}`",
                    f"- **Line:** `{issue.line_start}` to `{issue.line_end}`",
                    f"- **Source:** `{issue.detection_source.value}` ({issue.detecting_tool or 'Static/AI'})",
                    f"- **Code Snippet:** `{issue.code_snippet}`",
                    f"- **Why It Matters:** {issue.why_it_matters}",
                ])

                if issue.fix:
                    lines.extend([
                        "- **Suggested Remediation:**",
                        f"  > {issue.fix.suggested_fix}",
                    ])
                    if issue.fix.diff:
                        lines.extend([
                            "  ```diff",
                            issue.fix.diff.strip(),
                            "  ```",
                        ])

                if issue.generated_test:
                    lines.extend([
                        "- **Generated Test Case:**",
                        "  ```python",
                        issue.generated_test.test_code.strip(),
                        "  ```",
                    ])

                lines.append("")

        # Section 4: Complete Auto-Corrected Source Code
        if result.corrected_code_obj or result.corrected_full_code:
            corr = result.corrected_code_obj
            corr_code = (corr.corrected_code if corr else result.corrected_full_code) or ""
            val_stat = corr.validation_status.value.upper() if corr else "PASSED"
            fixes_list = corr.applied_fixes if corr else []

            lines.extend([
                "## 4. Complete Auto-Corrected Source Code",
                f"**AST Syntax Validation Status:** `{val_stat}`",
                "**Applied Remediation Fixes:**",
            ])
            for fix_item in fixes_list:
                lines.append(f"- {fix_item}")

            lines.extend([
                "",
                "```" + lang_clean,
                corr_code.strip(),
                "```",
                "",
            ])

            if corr and corr.diff and corr.diff.strip():
                lines.extend([
                    "### Complete Unified Diff",
                    "```diff",
                    corr.diff.strip(),
                    "```",
                    "",
                ])

        lines.extend([
            "---",
            "*Report generated by AI Code Review Assistant Engine*",
        ])

        return "\n".join(lines)
