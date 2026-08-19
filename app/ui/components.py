"""Production Streamlit UI component library for AI Code Review Assistant matching modern visual design."""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

from core.issue_model import CategoryEnum, CodeQualityScore, Issue, ReviewResult, ReviewSummary, SeverityEnum
from report import JSONReportExporter, MarkdownReportExporter, PDFReportExporter

SEVERITY_ICONS = {
    SeverityEnum.CRITICAL: "🔴",
    SeverityEnum.HIGH: "🟠",
    SeverityEnum.MEDIUM: "🟡",
    SeverityEnum.LOW: "🔵",
    SeverityEnum.INFORMATIONAL: "⚪",
}

SAMPLE_CODE_SNIPPETS = {
    "Python": (
        "def calculate_average(numbers):\n"
        "    total = 0\n"
        "    for n in numbers:\n"
        "        total += n\n"
        "    return total / len(numbers)\n\n"
        'user_input = input("Enter numbers separated by space: ")\n'
        "nums = [int(x) for x in user_input.split()]\n"
        "avg = calculate_average(nums)\n"
        'print(f"Average: {avg}")\n'
    ),
    "JavaScript": (
        "function calculateTotal(price, tax) {\n"
        "  var total = price + tax;\n"
        "  if (price == 0) {\n"
        '    console.log("Price is zero");\n'
        "  }\n"
        '  var output = eval("price * 1.1");\n'
        '  document.getElementById("res").innerHTML = output;\n'
        "  return total;\n"
        "}\n"
    ),
    "TypeScript": (
        "function processUserData(userData: any): any {\n"
        "  var id: any = userData.id;\n"
        "  if (id == null) {\n"
        '    console.log("No ID provided");\n'
        "  }\n"
        '  eval("console.log(id)");\n'
        "  return userData;\n"
        "}\n"
    ),
    "Java": (
        "import java.io.FileInputStream;\n\n"
        "public class Demo {\n"
        "    public void executeCommand(String inputCmd) {\n"
        "        try {\n"
        '            System.out.println("Executing: " + inputCmd);\n'
        "            Runtime.getRuntime().exec(inputCmd);\n"
        '            FileInputStream fis = new FileInputStream("data.txt");\n'
        "        } catch (Exception e) {\n"
        "            e.printStackTrace();\n"
        "        }\n"
        "    }\n\n"
        "    public boolean compareStrings(String s1, String s2) {\n"
        "        return s1 == s2;\n"
        "    }\n"
        "}\n"
    ),
}


def render_custom_css() -> None:
    """Injects custom CSS styling for dark mode matching the dashboard visual theme."""
    st.markdown(
        """
        <style>
        /* Dark Theme Global Styling */
        .stApp {
            background-color: #0A0E17;
            color: #E2E8F0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #111726;
            border-right: 1px solid #1E293B;
        }

        /* Card Container Styling */
        .ui-card {
            background-color: #141B2D;
            border: 1px solid #232D42;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }

        .ui-card-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Badge Pills */
        .badge-green {
            background: rgba(16, 185, 129, 0.15);
            color: #10B981;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.82rem;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .badge-yellow {
            background: rgba(245, 158, 11, 0.15);
            color: #F59E0B;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.82rem;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        /* Primary Button Styling */
        .stButton > button {
            background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1rem;
            border-radius: 10px;
            border: none;
            padding: 14px 28px;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);
            transition: all 0.2s ease-in-out;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6);
        }

        /* Language Badges in Sidebar */
        .lang-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #1A2234;
            border-radius: 8px;
            margin-bottom: 6px;
            font-size: 0.9rem;
        }

        .lang-ext {
            color: #94A3B8;
            font-size: 0.8rem;
            font-family: monospace;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Renders top navigation header matching screenshot layout."""
    st.title("🛡️ AI Code Review Assistant")
    st.caption("⚡ **Production Review Engine** | Multi-Layer Static Analysis & AI Reasoning")


def render_sidebar_controls() -> Tuple[bool, Optional[str], str, Dict[str, bool]]:
    """Renders sidebar review settings, status card, overrides, options, and supported languages list."""
    st.sidebar.markdown("### REVIEW SETTINGS")

    enable_ai = st.sidebar.toggle(
        "Enable AI Reasoning",
        value=True,
        help="Enable OpenAI LLM reasoning chain for logic flaws and edge cases.",
    )

    # OpenAI Status Card
    from services.config_service import get_settings
    settings = get_settings()
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
    has_valid_key = bool(api_key and api_key.strip() and not api_key.startswith("your_"))

    if enable_ai:
        if has_valid_key:
            st.sidebar.success("🟢 OpenAI Connected")
        else:
            st.sidebar.markdown(
                """
                <div style='background:#241E12; border:1px solid #78350F; padding:12px; border-radius:8px; margin-bottom:15px;'>
                    <div style='color:#FBBF24; font-weight:700; font-size:0.9rem;'>⚠️ OpenAI Key Missing</div>
                    <div style='color:#D97706; font-size:0.8rem;'>(Static Fallback Active)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.sidebar.info("🔵 Static-Only Mode Active")

    st.sidebar.markdown("---")
    language_override = st.sidebar.selectbox(
        "Manual Language Override",
        options=["Auto-Detect", "Python", "JavaScript", "TypeScript", "Java"],
        index=0,
        help="Explicitly override auto-detected language.",
    )
    manual_lang = None if language_override == "Auto-Detect" else language_override.lower()

    analysis_depth = st.sidebar.selectbox(
        "Analysis Depth",
        options=["Standard", "Deep", "Fast"],
        index=0,
    )

    st.sidebar.markdown("#### Additional Options")
    inc_tests = st.sidebar.checkbox("Include Test Generation", value=True)
    inc_fixes = st.sidebar.checkbox("Generate Fix Suggestions", value=True)
    inc_bandit = st.sidebar.checkbox("Security Analysis (Bandit / Real AST)", value=True)
    inc_radon = st.sidebar.checkbox("Performance Analysis (Radon / Complexity)", value=True)

    additional_options = {
        "tests": inc_tests,
        "fixes": inc_fixes,
        "security": inc_bandit,
        "performance": inc_radon,
    }

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Supported Languages")
    st.sidebar.markdown(
        """
        <div class='lang-item'><span>🐍 Python</span><span class='lang-ext'>.py, .pyw</span></div>
        <div class='lang-item'><span>🟨 JavaScript</span><span class='lang-ext'>.js, .jsx</span></div>
        <div class='lang-item'><span>🔷 TypeScript</span><span class='lang-ext'>.ts, .tsx</span></div>
        <div class='lang-item'><span>☕ Java</span><span class='lang-ext'>.java</span></div>
        """,
        unsafe_allow_html=True,
    )

    return enable_ai, manual_lang, analysis_depth, additional_options


def render_summary_metrics(summary: ReviewSummary) -> None:
    """Renders high-level review statistics and severity counters."""
    st.subheader("📊 Severity Counter Summary")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Total Issues", summary.total_issues)
    with c2:
        st.metric("🔴 Critical", summary.critical_count)
    with c3:
        st.metric("🟠 High", summary.high_count)
    with c4:
        st.metric("🟡 Medium", summary.medium_count)
    with c5:
        st.metric("🔵 Low", summary.low_count)
    with c6:
        st.metric("⚪ Info", summary.informational_count)


def render_ready_to_analyze_bar() -> bool:
    """Renders the capability feature step bar and big CTA review button matching screenshot."""
    st.markdown(
        """
        <div class='ui-card'>
            <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px;'>
                <div style='display:flex; gap:24px; align-items:center;'>
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;'>🐍</div>
                        <div style='font-weight:700; font-size:0.85rem;'>Multi-Language</div>
                        <div style='color:#94A3B8; font-size:0.75rem;'>Support</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;'>🎯</div>
                        <div style='font-weight:700; font-size:0.85rem;'>Static Analysis</div>
                        <div style='color:#94A3B8; font-size:0.75rem;'>Real AST Parsers</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;'>🛡️</div>
                        <div style='font-weight:700; font-size:0.85rem;'>AI Reasoning</div>
                        <div style='color:#94A3B8; font-size:0.75rem;'>Enabled</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;'>🔀</div>
                        <div style='font-weight:700; font-size:0.85rem;'>Smart Fusion</div>
                        <div style='color:#94A3B8; font-size:0.75rem;'>Deduplicate</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;'>✏️</div>
                        <div style='font-weight:700; font-size:0.85rem;'>Fix Suggestions</div>
                        <div style='color:#94A3B8; font-size:0.75rem;'>Auto-generate</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;'>🧪</div>
                        <div style='font-weight:700; font-size:0.85rem;'>Test Generation</div>
                        <div style='color:#94A3B8; font-size:0.75rem;'>Auto-generate</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.button("🔍 Run Code Review", type="primary", use_container_width=True)


def render_quality_score_gauge(overall_score: int) -> None:
    """Renders semi-circular gauge SVG for Quality Score Preview matching screenshot."""
    score_color = "#10B981" if overall_score >= 85 else ("#F59E0B" if overall_score >= 60 else "#EF4444")
    dash_array = int((overall_score / 100) * 157)  # 157 is arc circumference for radius 50

    st.markdown(
        f"""
        <div style='text-align:center; padding:10px;'>
            <svg width="180" height="100" viewBox="0 0 120 70">
                <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="#232D42" stroke-width="12" stroke-linecap="round"/>
                <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="{score_color}" stroke-width="12" stroke-linecap="round"
                      stroke-dasharray="{dash_array} 157"/>
            </svg>
            <div style='font-size:2.2rem; font-weight:800; color:#F8FAFC; margin-top:-25px;'>{overall_score}</div>
            <div style='color:#94A3B8; font-size:0.85rem;'>/ 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_grid(review_result: Optional[ReviewResult] = None, manual_override: Optional[str] = None) -> None:
    """Renders the 3 bottom cards: Quality Score Preview, Severity Distribution, and Analysis Engine Status."""
    c1, c2, c3 = st.columns([1, 1.3, 1.2])

    score_val = review_result.score.overall_score if review_result else 0
    crit = review_result.summary.critical_count if review_result else 0
    high = review_result.summary.high_count if review_result else 0
    med = review_result.summary.medium_count if review_result else 0
    low = review_result.summary.low_count if review_result else 0
    total_issues = review_result.summary.total_issues if review_result else 0
    lang_str = (review_result.language if review_result else (manual_override or "Auto-Detect")).upper()
    status_str = "Operational" if review_result else "Idle"

    with c1:
        st.markdown(
            "<div class='ui-card'>"
            "<div class='ui-card-title'>🎯 Quality Score Preview</div>",
            unsafe_allow_html=True,
        )
        render_quality_score_gauge(score_val)
        st.markdown(
            f"<div style='text-align:center; color:#94A3B8; font-size:0.8rem;'>"
            f"{'Score calculated' if review_result else 'Score will appear here'}</div></div>",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            "<div class='ui-card'>"
            "<div class='ui-card-title'>📊 Severity Distribution</div>"
            "<div style='display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;'>"
            f"<div style='background:#2D1517; border:1px solid #7F1D1D; border-radius:8px; padding:12px; text-align:center;'><div style='font-size:1.5rem; font-weight:800; color:#EF4444;'>{crit}</div><div style='font-size:0.75rem; color:#FCA5A5;'>Critical</div></div>"
            f"<div style='background:#2B1D0C; border:1px solid #7C2D12; border-radius:8px; padding:12px; text-align:center;'><div style='font-size:1.5rem; font-weight:800; color:#F97316;'>{high}</div><div style='font-size:0.75rem; color:#FDBA74;'>High</div></div>"
            f"<div style='background:#2B240C; border:1px solid #713F12; border-radius:8px; padding:12px; text-align:center;'><div style='font-size:1.5rem; font-weight:800; color:#FBBF24;'>{med}</div><div style='font-size:0.75rem; color:#FDE68A;'>Medium</div></div>"
            f"<div style='background:#0F2338; border:1px solid #1E3A8A; border-radius:8px; padding:12px; text-align:center;'><div style='font-size:1.5rem; font-weight:800; color:#3B82F6;'>{low}</div><div style='font-size:0.75rem; color:#BFDBFE;'>Low</div></div>"
            "</div>"
            f"<div style='margin-top:12px; text-align:right; font-size:0.8rem; color:#94A3B8;'>Total Issues: <b>{total_issues}</b></div>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class='ui-card'>
                <div class='ui-card-title'>⚙️ Analysis Engine Status</div>
                <div style='display:flex; flex-direction:column; gap:10px; margin-top:10px; font-size:0.85rem;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#94A3B8;'>📄 Language Detection</span>
                        <span style='font-weight:700; color:#F8FAFC;'>{lang_str}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#94A3B8;'>⚙️ Static Analysis</span>
                        <span style='font-weight:700; color:#F8FAFC;'>{'Real AST Parsers' if review_result else '--'}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#94A3B8;'>🤖 AI Reasoning</span>
                        <span style='font-weight:700; color:#F8FAFC;'>{'Enabled' if review_result else '--'}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='color:#94A3B8;'>🎯 Status</span>
                        <span class='{"badge-green" if review_result else "badge-yellow"}'>{status_str}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_analysis_engine_status(language: str, active_analyzers: List[Any], enable_ai: bool) -> None:
    """Renders the Analysis Engine & Capability Status details section."""
    st.subheader("⚙️ Active Analyzer Capability Details")

    lang_clean = (language or "python").lower()

    if lang_clean in ("python", "py"):
        parser_name = "ast.parse (Python AST)"
        val_status = "FULL (ast.parse)"
    elif lang_clean in ("javascript", "js", "jsx"):
        parser_name = "Esprima (JavaScript AST)"
        val_status = "FULL (Esprima AST)"
    elif lang_clean in ("typescript", "ts", "tsx"):
        parser_name = "Tree-Sitter (TypeScript AST)"
        val_status = "FULL (Tree-Sitter AST)"
    elif lang_clean == "java":
        parser_name = "Javalang AST & javac Compiler"
        val_status = "FULL (Javalang/javac AST)"
    else:
        parser_name = "None"
        val_status = "PARTIAL (AI-Only Fallback)"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Target Language", language.upper())
    with col2:
        st.metric("Syntax Parser", parser_name)
    with col3:
        st.metric("Validation Mode", val_status)
    with col4:
        st.metric("AI Reasoning", "Enabled 🟢" if enable_ai else "Disabled 🔵")

    with st.expander("🔍 Active Static Analyzers & Tool Availability", expanded=False):
        for analyzer in active_analyzers:
            meta = analyzer.get_metadata() if hasattr(analyzer, "get_metadata") else {
                "analyzer": getattr(analyzer, "name", "analyzer"),
                "tool_name": getattr(analyzer, "name", "tool"),
                "type": "static",
                "available": True,
                "reason": "Operational",
            }
            status_icon = "✅" if meta.get("available", True) else "⚠️"
            st.write(
                f"{status_icon} **{meta.get('analyzer', 'Analyzer')}** (`{meta.get('tool_name', 'tool')}`) "
                f"— Type: `{meta.get('type', 'static')}` | Status: `{meta.get('reason', 'Operational')}`"
            )

        if any(not (a.is_available() if hasattr(a, "is_available") else True) for a in active_analyzers):
            st.warning("⚠️ Static analyzer unavailable — using available analyzers + AI reasoning")


def render_issue_card(issue: Issue, index: int = 1) -> None:
    """Renders an individual structured Issue card in an expandable container."""
    icon = SEVERITY_ICONS.get(issue.severity, "🔍")
    severity_str = issue.severity.value.upper()
    category_str = issue.category.value.replace("_", " ").title()

    expander_title = (
        f"{icon} #{index} [{severity_str}] {category_str}: {issue.description[:80]} "
        f"(Line {issue.line_start})"
    )

    with st.expander(expander_title, expanded=(issue.severity in (SeverityEnum.CRITICAL, SeverityEnum.HIGH))):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Severity**: `{severity_str}`")
        with c2:
            st.markdown(f"**Category**: `{category_str}`")
        with c3:
            line_txt = f"Line {issue.line_start}" if issue.line_start == issue.line_end else f"Lines {issue.line_start}–{issue.line_end}"
            st.markdown(f"**Location**: `{line_txt}`")
        with c4:
            st.markdown(f"**Source**: `{issue.detection_source.value}` ({issue.detecting_tool or 'engine'})")

        st.markdown(f"**Description**: {issue.description}")

        if issue.code_snippet and issue.code_snippet.strip():
            st.markdown("**Code Excerpt**:")
            st.code(issue.code_snippet, language="python")

        if issue.why_it_matters:
            st.markdown(f"💡 **Why it matters**: {issue.why_it_matters}")

        # Fix display
        if issue.fix:
            st.markdown("🛠️ **Suggested Remediation**:")
            st.info(issue.fix.suggested_fix)
            if issue.fix.diff and issue.fix.diff.strip():
                st.markdown("**Unified Diff**:")
                st.code(issue.fix.diff, language="diff")

        # Test case display
        if issue.generated_test:
            st.markdown("🧪 **Generated Unit Test Case**:")
            st.code(issue.generated_test.test_code, language="python")


def render_corrected_code_section(review_result: ReviewResult) -> None:
    """Renders the Complete Auto-Corrected Source Code section matching exact user requirements."""
    if not review_result:
        return

    st.subheader("✨ Complete Auto-Corrected Source Code")

    corr = review_result.corrected_code_obj
    corrected_code = (corr.corrected_code if corr else review_result.corrected_full_code) or ""
    lang = (review_result.language or "python").lower()

    ext_map = {
        "python": "py", "py": "py",
        "javascript": "js", "js": "js", "jsx": "js",
        "typescript": "ts", "ts": "ts", "tsx": "ts",
        "java": "java",
    }
    ext = ext_map.get(lang, "txt")
    out_filename = f"reviewed.{ext}"

    if corr:
        val_status = corr.validation_status.value
        if val_status == "passed":
            st.success("✓ **Corrected code passed AST syntax validation**")
        elif val_status == "failed":
            st.error(f"✗ **Corrected code failed AST validation**: {corr.validation_error}")
        else:
            st.info("ℹ️ **AST Validation**: Partial static check active")

        if corr.applied_fixes:
            with st.expander("🛠️ Applied Remediation Fixes Summary", expanded=True):
                for f_note in corr.applied_fixes:
                    st.write(f"- {f_note}")

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        st.download_button(
            label=f"⬇ Download Corrected Code ({out_filename})",
            data=corrected_code,
            file_name=out_filename,
            mime="text/plain",
            type="primary",
            use_container_width=True,
        )

    # Complete Corrected Code Box
    st.markdown("**Complete Corrected Source File:**")
    st.code(corrected_code, language=lang)

    # Comparison Section: Original vs Corrected
    st.markdown("### 🔄 Original vs Corrected Code Comparison")
    tab_orig, tab_corr, tab_diff = st.tabs(["Original Code", "Corrected Code", "Unified Diff"])

    with tab_orig:
        st.code(review_result.submitted_code, language=lang)

    with tab_corr:
        st.code(corrected_code, language=lang)

    with tab_diff:
        diff_text = (corr.diff if corr else "") or ""
        if diff_text and diff_text.strip():
            st.code(diff_text, language="diff")
        else:
            st.info("No diff detected — original code was clean.")


def render_export_section(review_result: ReviewResult) -> None:
    """Renders complete report and source code export buttons for all 7 assets."""
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Export & Downloads")

    lang = (review_result.language or "python").lower()
    ext_map = {
        "python": "py", "py": "py",
        "javascript": "js", "js": "js", "jsx": "js",
        "typescript": "ts", "ts": "ts", "tsx": "ts",
        "java": "java",
    }
    ext = ext_map.get(lang, "txt")

    corr = review_result.corrected_code_obj
    corrected_code = (corr.corrected_code if corr else review_result.corrected_full_code) or ""
    diff_code = (corr.diff if corr else "") or ""
    tests_code = review_result.aggregated_tests_code or ""

    md_exporter = MarkdownReportExporter()
    json_exporter = JSONReportExporter()
    pdf_exporter = PDFReportExporter()

    md_content = md_exporter.export(review_result)
    json_content = json_exporter.export(review_result)
    pdf_content = pdf_exporter.export(review_result)

    st.sidebar.download_button(
        label=f"✨ Download Corrected Code (reviewed.{ext})",
        data=corrected_code,
        file_name=f"reviewed.{ext}",
        mime="text/plain",
    )

    st.sidebar.download_button(
        label=f"📄 Download Original Code (submitted.{ext})",
        data=review_result.submitted_code,
        file_name=f"submitted.{ext}",
        mime="text/plain",
    )

    if diff_code and diff_code.strip():
        st.sidebar.download_button(
            label="📝 Download Unified Diff (code_review.diff)",
            data=diff_code,
            file_name="code_review.diff",
            mime="text/x-diff",
        )

    if tests_code and tests_code.strip():
        st.sidebar.download_button(
            label=f"🧪 Download Generated Tests (tests.{ext})",
            data=tests_code,
            file_name=f"tests.{ext}",
            mime="text/plain",
        )

    st.sidebar.download_button(
        label="📄 Download Markdown Report",
        data=md_content,
        file_name="code_review_report.md",
        mime="text/markdown",
    )

    st.sidebar.download_button(
        label="📊 Download JSON Payload",
        data=json_content,
        file_name="code_review_report.json",
        mime="application/json",
    )

    st.sidebar.download_button(
        label="📕 Export PDF Report",
        data=pdf_content,
        file_name="code_review_report.pdf",
        mime="application/pdf" if pdf_content.startswith("%PDF") else "text/plain",
    )
