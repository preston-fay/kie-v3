"""
Code Simplifier Skill

WHAT THIS SKILL DOES:
Simplifies and refines Python code for clarity, consistency, and maintainability
while preserving exact functionality. Focuses on recently modified code unless
instructed otherwise.

Inspired by Anthropic's internal code-simplifier plugin used by the Claude Code team.

CORE PRINCIPLES:
1. Preserve Functionality - Never change what code does, only how it does it
2. Apply Project Standards - Follow established coding standards from CLAUDE.md
3. Enhance Clarity - Simplify structure and improve readability
4. Maintain Balance - Avoid over-simplification that reduces maintainability
5. Focus Scope - Refine recently modified code unless instructed otherwise

INPUTS (read-only):
- Python source files in kie/ directory
- Project conventions from CLAUDE.md

OUTPUTS:
- outputs/internal/code_simplifier_report.json
- outputs/internal/code_simplifier_report.md

STAGE SCOPE: build, preview (runs after code changes)

SIMPLIFICATION RULES:
1. Reduce unnecessary complexity and nesting
2. Eliminate redundant code and abstractions
3. Improve readability through clear naming
4. Consolidate related logic
5. Remove obvious/redundant comments

ANTI-PATTERNS TO DETECT:
1. Nested ternary operators
2. Dense one-liners that sacrifice clarity
3. Over-abstraction
4. Unused imports
5. Redundant type annotations
6. Overly complex comprehensions
7. Deep nesting (>3 levels)
8. Long functions (>50 lines)
9. Too many parameters (>5)
10. Magic numbers without explanation

CLASSIFICATION:
- clean: No issues, code is clear and maintainable
- needs_attention: Minor issues, could be improved
- needs_refactor: Significant issues, should be refactored
"""

import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.skills.base import Skill, SkillContext, SkillResult


@dataclass
class CodeIssue:
    """Represents a detected code quality issue."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # "info", "warning", "error"
    message: str
    suggestion: str
    code_snippet: str = ""


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    complexity_score: float
    issues: list[CodeIssue] = field(default_factory=list)
    classification: str = "clean"


class CodeSimplifierSkill(Skill):
    """
    Code Simplifier Skill.

    Analyzes Python code for clarity, consistency, and maintainability.
    Provides actionable suggestions for simplification while preserving functionality.
    """

    # Thresholds for code quality
    MAX_LINE_LENGTH = 100
    MAX_FUNCTION_LINES = 50
    MAX_FUNCTION_PARAMS = 5
    MAX_NESTING_DEPTH = 3
    MAX_COMPREHENSION_LENGTH = 60
    MAX_COGNITIVE_COMPLEXITY = 15

    # Patterns to detect
    NESTED_TERNARY_PATTERN = re.compile(r'\w+\s+if\s+.+\s+else\s+.+\s+if\s+.+\s+else')
    MAGIC_NUMBER_PATTERN = re.compile(r'(?<!["\'])\b(?!0\b|1\b)([2-9]|\d{2,})\b(?!["\'])')

    @property
    def skill_id(self) -> str:
        return "code_simplifier"

    @property
    def description(self) -> str:
        return "Simplify and refine code for clarity, consistency, and maintainability"

    @property
    def stage_scope(self) -> list[str]:
        return ["build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        return []  # Can run without prerequisites

    @property
    def produces_artifacts(self) -> list[str]:
        return ["code_simplifier_json", "code_simplifier_markdown"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute code simplification analysis.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with analysis artifacts and status
        """
        warnings = []
        errors = []

        outputs_dir = context.project_root / "outputs" / "internal"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Check for target_path in metadata (from CLI)
        target_path_str = context.metadata.get("target_path")
        target_path = Path(target_path_str) if target_path_str else None

        # Determine files to analyze
        py_files_to_analyze = []

        if target_path and target_path.exists():
            if target_path.is_file() and target_path.suffix == ".py":
                # Single file specified
                py_files_to_analyze = [target_path]
            elif target_path.is_dir():
                # Directory specified - scan it
                py_files_to_analyze = list(target_path.rglob("*.py"))
        else:
            # Default: scan kie/ directory
            kie_dir = context.project_root / "kie"
            if not kie_dir.exists():
                # Try parent directory for KIE repo structure
                kie_dir = context.project_root.parent / "kie"

            if not kie_dir.exists():
                errors.append("KIE source directory not found")
                return SkillResult(
                    success=False,
                    artifacts={},
                    evidence={},
                    warnings=warnings,
                    errors=errors,
                )
            py_files_to_analyze = list(kie_dir.rglob("*.py"))

        # Analyze Python files
        file_analyses = []
        all_issues = []

        for py_file in py_files_to_analyze:
            # Skip test files and __pycache__
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            try:
                analysis = self._analyze_file(py_file, context.project_root)
                file_analyses.append(analysis)
                all_issues.extend(analysis.issues)
            except Exception as e:
                warnings.append(f"Failed to analyze {py_file.name}: {e}")

        # Calculate summary statistics
        summary = self._calculate_summary(file_analyses, all_issues)

        # Build output
        output = {
            "generated_at": datetime.now().isoformat(),
            "project_root": str(context.project_root),
            "files_analyzed": len(file_analyses),
            "summary": summary,
            "files": [self._file_analysis_to_dict(fa) for fa in file_analyses],
            "all_issues": [self._issue_to_dict(issue) for issue in all_issues],
        }

        # Save JSON
        json_path = outputs_dir / "code_simplifier_report.json"
        with open(json_path, "w") as f:
            json.dump(output, f, indent=2)

        # Save Markdown
        md_path = outputs_dir / "code_simplifier_report.md"
        markdown = self._generate_markdown(output, file_analyses)
        md_path.write_text(markdown)

        evidence = {
            "files_analyzed": len(file_analyses),
            "total_issues": len(all_issues),
            "issues_by_severity": summary["issues_by_severity"],
            "issues_by_type": summary["issues_by_type"],
        }

        return SkillResult(
            success=True,
            artifacts={
                "code_simplifier_json": str(json_path),
                "code_simplifier_markdown": str(md_path),
            },
            evidence=evidence,
            warnings=warnings,
            errors=errors,
        )

    def _analyze_file(self, file_path: Path, project_root: Path) -> FileAnalysis:
        """Analyze a single Python file for code quality issues."""
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        # Basic metrics
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        code_lines = total_lines - blank_lines - comment_lines

        # Parse AST for deeper analysis
        issues = []
        function_count = 0
        class_count = 0
        complexity_score = 0.0

        try:
            tree = ast.parse(content)

            # Count functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                elif isinstance(node, ast.ClassDef):
                    class_count += 1

            # Run all analysis passes
            issues.extend(self._check_nesting_depth(tree, file_path, lines))
            issues.extend(self._check_function_length(tree, file_path, lines))
            issues.extend(self._check_function_parameters(tree, file_path, lines))
            issues.extend(self._check_comprehension_complexity(tree, file_path, lines))
            issues.extend(self._check_unused_imports(tree, file_path, content))
            issues.extend(self._check_nested_ternary(file_path, lines))
            issues.extend(self._check_magic_numbers(tree, file_path, lines))
            issues.extend(self._check_line_length(file_path, lines))
            issues.extend(self._check_cognitive_complexity(tree, file_path, lines))

            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(tree, issues)

        except SyntaxError as e:
            issues.append(CodeIssue(
                file_path=str(file_path.relative_to(project_root)),
                line_number=e.lineno or 1,
                issue_type="syntax_error",
                severity="error",
                message=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error before analysis can continue",
            ))

        # Classify the file
        classification = self._classify_file(issues)

        return FileAnalysis(
            file_path=str(file_path.relative_to(project_root)),
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            class_count=class_count,
            complexity_score=complexity_score,
            issues=issues,
            classification=classification,
        )

    def _check_nesting_depth(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for deeply nested code blocks."""
        issues = []

        class NestingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth_nodes = []

            def visit_FunctionDef(self, node):
                self.current_depth += 1
                if self.current_depth > 0:  # Inside a function
                    self._check_body_depth(node.body, node.lineno)
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

            def _check_body_depth(self, body, start_line, depth=0):
                for node in body:
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        new_depth = depth + 1
                        if new_depth > MAX_NESTING:
                            self.max_depth_nodes.append((node.lineno, new_depth))
                        if hasattr(node, "body"):
                            self._check_body_depth(node.body, node.lineno, new_depth)
                        if hasattr(node, "orelse") and node.orelse:
                            self._check_body_depth(node.orelse, node.lineno, new_depth)
                        if hasattr(node, "handlers"):
                            for handler in node.handlers:
                                self._check_body_depth(handler.body, handler.lineno, new_depth)
                        if hasattr(node, "finalbody") and node.finalbody:
                            self._check_body_depth(node.finalbody, node.lineno, new_depth)

        MAX_NESTING = self.MAX_NESTING_DEPTH
        visitor = NestingVisitor()
        visitor.visit(tree)

        for line_no, depth in visitor.max_depth_nodes:
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else ""
            issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=line_no,
                issue_type="deep_nesting",
                severity="warning",
                message=f"Nesting depth of {depth} exceeds maximum of {MAX_NESTING}",
                suggestion="Extract nested logic into separate functions or use early returns",
                code_snippet=snippet,
            ))

        return issues

    def _check_function_length(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for overly long functions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = node.end_lineno or start_line

                func_lines = end_line - start_line + 1
                if func_lines > self.MAX_FUNCTION_LINES:
                    snippet = lines[start_line - 1].strip() if start_line <= len(lines) else ""
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=start_line,
                        issue_type="long_function",
                        severity="warning",
                        message=f"Function '{node.name}' has {func_lines} lines (max: {self.MAX_FUNCTION_LINES})",
                        suggestion="Break down into smaller, focused functions",
                        code_snippet=snippet,
                    ))

        return issues

    def _check_function_parameters(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for functions with too many parameters."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count parameters (excluding self/cls)
                args = node.args
                param_count = (
                    len(args.args)
                    + len(args.posonlyargs)
                    + len(args.kwonlyargs)
                )

                # Subtract 1 for self/cls in methods
                first_arg = args.args[0].arg if args.args else ""
                if first_arg in ("self", "cls"):
                    param_count -= 1

                if param_count > self.MAX_FUNCTION_PARAMS:
                    snippet = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="too_many_params",
                        severity="info",
                        message=f"Function '{node.name}' has {param_count} parameters (max: {self.MAX_FUNCTION_PARAMS})",
                        suggestion="Consider using a dataclass or config object to group related parameters",
                        code_snippet=snippet,
                    ))

        return issues

    def _check_comprehension_complexity(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for overly complex comprehensions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                # Check number of generators (nested loops)
                num_generators = len(node.generators)

                # Check for nested comprehensions
                has_nested = any(
                    isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
                    for child in ast.walk(node)
                    if child is not node
                )

                # Get the line and check length
                line_no = node.lineno
                if line_no <= len(lines):
                    line = lines[line_no - 1]
                    line_len = len(line.strip())

                    if num_generators > 2 or has_nested or line_len > self.MAX_COMPREHENSION_LENGTH:
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=line_no,
                            issue_type="complex_comprehension",
                            severity="info",
                            message="Complex comprehension may be hard to read",
                            suggestion="Consider using a regular loop or breaking into multiple steps",
                            code_snippet=line.strip()[:80] + ("..." if len(line.strip()) > 80 else ""),
                        ))

        return issues

    def _check_unused_imports(
        self, tree: ast.AST, file_path: Path, content: str
    ) -> list[CodeIssue]:
        """Check for potentially unused imports."""
        issues = []
        imports = []

        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imports.append((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        name = alias.asname or alias.name
                        imports.append((name, node.lineno))

        # Check if each import is used (simple heuristic)
        for name, line_no in imports:
            # Skip common false positives
            if name in ("annotations", "TYPE_CHECKING", "__future__"):
                continue

            # Count occurrences (excluding the import line itself)
            pattern = rf"\b{re.escape(name)}\b"
            matches = list(re.finditer(pattern, content))

            # If only one match (the import itself), it might be unused
            if len(matches) <= 1:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=line_no,
                    issue_type="potentially_unused_import",
                    severity="info",
                    message=f"Import '{name}' may be unused",
                    suggestion="Remove if not needed, or verify usage in type hints",
                    code_snippet=f"import {name}",
                ))

        return issues

    def _check_nested_ternary(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for nested ternary operators."""
        issues = []

        for i, line in enumerate(lines, 1):
            if self.NESTED_TERNARY_PATTERN.search(line):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="nested_ternary",
                    severity="warning",
                    message="Nested ternary operators reduce readability",
                    suggestion="Use if/elif/else blocks or a dictionary lookup instead",
                    code_snippet=line.strip()[:80],
                ))

        return issues

    def _check_magic_numbers(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for magic numbers that should be named constants."""
        issues = []
        reported_lines = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # Skip common acceptable values
                if node.value in (0, 1, -1, 2, 10, 100, 0.0, 1.0, 0.5):
                    continue

                # Skip if in a constant assignment (NAME = value)
                # This is a heuristic - we check the line content
                line_no = node.lineno
                if line_no in reported_lines:
                    continue

                if line_no <= len(lines):
                    line = lines[line_no - 1]
                    # Skip if it looks like a constant definition
                    if re.match(r"^\s*[A-Z_][A-Z0-9_]*\s*=", line):
                        continue
                    # Skip if it's in a type hint
                    if ":" in line.split("=")[0] if "=" in line else False:
                        continue

                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=line_no,
                        issue_type="magic_number",
                        severity="info",
                        message=f"Magic number {node.value} should be a named constant",
                        suggestion="Extract to a named constant with a descriptive name",
                        code_snippet=line.strip()[:60],
                    ))
                    reported_lines.add(line_no)

        return issues

    def _check_line_length(
        self, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check for lines exceeding maximum length."""
        issues = []

        for i, line in enumerate(lines, 1):
            if len(line) > self.MAX_LINE_LENGTH:
                # Skip URLs and long strings
                if "http://" in line or "https://" in line:
                    continue
                if '"""' in line or "'''" in line:
                    continue

                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="long_line",
                    severity="info",
                    message=f"Line length {len(line)} exceeds {self.MAX_LINE_LENGTH}",
                    suggestion="Break into multiple lines or extract variables",
                    code_snippet=line[:60] + "...",
                ))

        return issues

    def _check_cognitive_complexity(
        self, tree: ast.AST, file_path: Path, lines: list[str]
    ) -> list[CodeIssue]:
        """Check cognitive complexity of functions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cognitive_complexity(node)

                if complexity > self.MAX_COGNITIVE_COMPLEXITY:
                    snippet = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="high_cognitive_complexity",
                        severity="warning",
                        message=f"Function '{node.name}' has cognitive complexity of {complexity} (max: {self.MAX_COGNITIVE_COMPLEXITY})",
                        suggestion="Simplify control flow, extract helper functions, or use early returns",
                        code_snippet=snippet,
                    ))

        return issues

    def _calculate_cognitive_complexity(self, func_node: ast.AST) -> int:
        """Calculate cognitive complexity score for a function."""
        complexity = 0
        nesting = 0

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0
                self.nesting = 0

            def visit_If(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1

            def visit_For(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1

            def visit_While(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1

            def visit_Try(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1

            def visit_BoolOp(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)

            def visit_Lambda(self, node):
                self.complexity += 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(func_node)
        return visitor.complexity

    def _calculate_complexity_score(
        self, tree: ast.AST, issues: list[CodeIssue]
    ) -> float:
        """Calculate overall complexity score for a file."""
        base_score = 0.0

        # Add points for issues by severity
        for issue in issues:
            if issue.severity == "error":
                base_score += 10.0
            elif issue.severity == "warning":
                base_score += 3.0
            else:
                base_score += 1.0

        return min(100.0, base_score)

    def _classify_file(self, issues: list[CodeIssue]) -> str:
        """Classify file based on issues found."""
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        info_count = sum(1 for i in issues if i.severity == "info")

        if error_count > 0 or warning_count > 5:
            return "needs_refactor"
        elif warning_count > 0 or info_count > 10:
            return "needs_attention"
        else:
            return "clean"

    def _calculate_summary(
        self, file_analyses: list[FileAnalysis], all_issues: list[CodeIssue]
    ) -> dict[str, Any]:
        """Calculate summary statistics."""
        issues_by_severity = defaultdict(int)
        issues_by_type = defaultdict(int)

        for issue in all_issues:
            issues_by_severity[issue.severity] += 1
            issues_by_type[issue.issue_type] += 1

        classification_counts = defaultdict(int)
        for fa in file_analyses:
            classification_counts[fa.classification] += 1

        total_lines = sum(fa.total_lines for fa in file_analyses)
        total_code_lines = sum(fa.code_lines for fa in file_analyses)
        total_functions = sum(fa.function_count for fa in file_analyses)
        total_classes = sum(fa.class_count for fa in file_analyses)

        return {
            "total_files": len(file_analyses),
            "total_lines": total_lines,
            "total_code_lines": total_code_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_issues": len(all_issues),
            "issues_by_severity": dict(issues_by_severity),
            "issues_by_type": dict(issues_by_type),
            "files_by_classification": dict(classification_counts),
            "average_complexity": (
                sum(fa.complexity_score for fa in file_analyses) / len(file_analyses)
                if file_analyses else 0.0
            ),
        }

    def _file_analysis_to_dict(self, fa: FileAnalysis) -> dict[str, Any]:
        """Convert FileAnalysis to dictionary."""
        return {
            "file_path": fa.file_path,
            "total_lines": fa.total_lines,
            "code_lines": fa.code_lines,
            "comment_lines": fa.comment_lines,
            "blank_lines": fa.blank_lines,
            "function_count": fa.function_count,
            "class_count": fa.class_count,
            "complexity_score": fa.complexity_score,
            "classification": fa.classification,
            "issue_count": len(fa.issues),
        }

    def _issue_to_dict(self, issue: CodeIssue) -> dict[str, Any]:
        """Convert CodeIssue to dictionary."""
        return {
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "code_snippet": issue.code_snippet,
        }

    def _generate_markdown(
        self, output: dict[str, Any], file_analyses: list[FileAnalysis]
    ) -> str:
        """Generate markdown report of code simplifier results."""
        summary = output["summary"]

        lines = [
            "# Code Simplifier Report",
            "",
            f"**Generated**: {output['generated_at']}",
            f"**Project**: {output['project_root']}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Files Analyzed**: {summary['total_files']}",
            f"- **Total Lines**: {summary['total_lines']:,}",
            f"- **Code Lines**: {summary['total_code_lines']:,}",
            f"- **Functions**: {summary['total_functions']}",
            f"- **Classes**: {summary['total_classes']}",
            f"- **Total Issues**: {summary['total_issues']}",
            f"- **Average Complexity**: {summary['average_complexity']:.1f}",
            "",
            "### Files by Classification",
            "",
        ]

        for classification, count in summary["files_by_classification"].items():
            emoji = {"clean": "✅", "needs_attention": "⚠️", "needs_refactor": "🔴"}.get(
                classification, "❓"
            )
            lines.append(f"- {emoji} **{classification}**: {count} files")

        lines.extend([
            "",
            "### Issues by Severity",
            "",
        ])

        for severity, count in summary["issues_by_severity"].items():
            emoji = {"error": "🔴", "warning": "⚠️", "info": "ℹ️"}.get(severity, "❓")
            lines.append(f"- {emoji} **{severity}**: {count}")

        lines.extend([
            "",
            "### Issues by Type",
            "",
        ])

        for issue_type, count in sorted(
            summary["issues_by_type"].items(), key=lambda x: -x[1]
        ):
            lines.append(f"- **{issue_type}**: {count}")

        lines.extend([
            "",
            "---",
            "",
            "## Files Needing Attention",
            "",
        ])

        # List files that need attention or refactoring
        attention_files = [
            fa for fa in file_analyses if fa.classification != "clean"
        ]

        if attention_files:
            for fa in sorted(attention_files, key=lambda x: -x.complexity_score):
                emoji = {"needs_attention": "⚠️", "needs_refactor": "🔴"}.get(
                    fa.classification, "❓"
                )
                lines.append(f"### {emoji} {fa.file_path}")
                lines.append("")
                lines.append(f"- **Classification**: {fa.classification}")
                lines.append(f"- **Complexity Score**: {fa.complexity_score:.1f}")
                lines.append(f"- **Issues**: {len(fa.issues)}")
                lines.append("")

                if fa.issues:
                    lines.append("**Issues:**")
                    lines.append("")
                    for issue in fa.issues[:10]:  # Limit to top 10 per file
                        severity_emoji = {
                            "error": "🔴",
                            "warning": "⚠️",
                            "info": "ℹ️",
                        }.get(issue.severity, "❓")
                        lines.append(
                            f"- {severity_emoji} Line {issue.line_number}: {issue.message}"
                        )
                        if issue.suggestion:
                            lines.append(f"  - 💡 {issue.suggestion}")
                    if len(fa.issues) > 10:
                        lines.append(f"  - ... and {len(fa.issues) - 10} more issues")
                    lines.append("")
        else:
            lines.append("✅ All files are clean!")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## Recommendations",
            "",
            "Based on the analysis, consider the following actions:",
            "",
        ])

        # Generate actionable recommendations
        recommendations = self._generate_recommendations(summary, file_analyses)
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")

        lines.extend([
            "",
            "---",
            "",
            "*Generated by KIE Code Simplifier Skill*",
        ])

        return "\n".join(lines)

    def _generate_recommendations(
        self, summary: dict[str, Any], file_analyses: list[FileAnalysis]
    ) -> list[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        issues_by_type = summary["issues_by_type"]

        # Prioritize by most common issues
        if issues_by_type.get("long_function", 0) > 5:
            recommendations.append(
                "**Reduce function length**: Several functions exceed 50 lines. "
                "Break them into smaller, focused functions with clear responsibilities."
            )

        if issues_by_type.get("deep_nesting", 0) > 3:
            recommendations.append(
                "**Flatten nested code**: Use early returns, guard clauses, and "
                "extract helper functions to reduce nesting depth."
            )

        if issues_by_type.get("high_cognitive_complexity", 0) > 3:
            recommendations.append(
                "**Simplify control flow**: Functions with high cognitive complexity "
                "are hard to understand. Consider state machines, lookup tables, "
                "or breaking into smaller functions."
            )

        if issues_by_type.get("magic_number", 0) > 10:
            recommendations.append(
                "**Name your constants**: Extract magic numbers into named constants "
                "at the module or class level for better readability."
            )

        if issues_by_type.get("nested_ternary", 0) > 0:
            recommendations.append(
                "**Eliminate nested ternaries**: Replace nested ternary operators "
                "with if/elif/else blocks or dictionary lookups."
            )

        if issues_by_type.get("too_many_params", 0) > 3:
            recommendations.append(
                "**Reduce parameter counts**: Consider using dataclasses, "
                "configuration objects, or builder patterns for functions with many parameters."
            )

        if summary.get("average_complexity", 0) > 20:
            recommendations.append(
                "**Focus on high-complexity files first**: The average complexity score "
                "is elevated. Prioritize refactoring files marked as 'needs_refactor'."
            )

        if not recommendations:
            recommendations.append(
                "✅ **Codebase is in good shape!** Continue following current practices."
            )

        return recommendations
