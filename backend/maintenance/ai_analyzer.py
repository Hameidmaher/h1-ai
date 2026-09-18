"""AI Analyzer — uses LLM to analyze audit issues and suggest fixes.

Uses Ollama (local) by default, or Groq/OpenAI for better quality.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import json
import re
import structlog

from maintenance.self_audit import Issue, AuditReport

logger = structlog.get_logger()


@dataclass
class AIAnalysis:
    """AI analysis of an issue."""
    issue: Issue
    explanation: str
    root_cause: str
    fix_steps: list[str]
    risk_level: str
    estimated_time: str
    can_auto_fix: bool


class AIAnalyzer:
    """Uses LLM to analyze audit issues."""
    
    def __init__(self):
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM (Ollama by default)."""
        try:
            from llm.factory import create_llm
            self.llm = create_llm(temperature=0.1)
            logger.info("ai_analyzer.llm_ready")
        except Exception as e:
            logger.warning("ai_analyzer.llm_unavailable", error=str(e)[:100])
            self.llm = None
    
    def analyze_issue(self, issue: Issue) -> AIAnalysis:
        """Analyze a single issue with LLM."""
        if not self.llm:
            return self._fallback_analysis(issue)
        
        prompt = f"""أنت مهندس برمجيات خبير. حلل المشكلة دي وقترح حل عملي:

**الفئة:** {issue.category}
**الخطورة:** {issue.severity}
**العنوان:** {issue.title}
**الوصف:** {issue.description}
{f'**الملف:** {issue.file}:{issue.line}' if issue.file else ''}

الرد بصيغة JSON فقط (بدون نص إضافي):
{{
  "explanation": "شرح مبسط للمشكلة بالعربي",
  "root_cause": "السبب الجذري",
  "fix_steps": ["خطوة 1", "خطوة 2", "خطوة 3"],
  "risk_level": "low|medium|high",
  "estimated_time": "5 دقائق"
}}
"""
        
        try:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("LLM timeout (60s)")
            
            # Set 30-second timeout (Unix only)
            old_handler = None
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)
            except (ValueError, AttributeError):
                pass  # Not on Unix or signal unavailable
            
            try:
                response = self.llm.invoke(prompt)
            finally:
                try:
                    signal.alarm(60)
                    if old_handler is not None:
                        signal.signal(signal.SIGALRM, old_handler)
                except (ValueError, AttributeError):
                    pass
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON — handle markdown code blocks
            # 1. Remove markdown code fences
            cleaned = re.sub(r'```(?:json)?\s*', '', content)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            cleaned = cleaned.strip()
            
            # 2. Find first { and last }
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = cleaned[start:end]
                data = json.loads(json_str)
            else:
                raise ValueError(f"No JSON found in: {content[:200]}")
            
            return AIAnalysis(
                issue=issue,
                explanation=data.get("explanation", issue.description),
                root_cause=data.get("root_cause", ""),
                fix_steps=data.get("fix_steps", [issue.fix_suggestion] if issue.fix_suggestion else []),
                risk_level=data.get("risk_level", "medium"),
                estimated_time=data.get("estimated_time", "5 دقائق"),
                can_auto_fix=issue.auto_fixable,
            )
        except Exception as e:
            logger.warning("ai_analyzer.parse_failed", error=str(e)[:100])
            return self._fallback_analysis(issue)
    
    def _fallback_analysis(self, issue: Issue) -> AIAnalysis:
        """Fallback when LLM unavailable."""
        return AIAnalysis(
            issue=issue,
            explanation=issue.description,
            root_cause="تحليل يدوي مطلوب",
            fix_steps=[issue.fix_suggestion] if issue.fix_suggestion else ["مراجعة يدوية"],
            risk_level="medium",
            estimated_time="5-10 دقائق",
            can_auto_fix=issue.auto_fixable,
        )
    
    def analyze_report(self, report: AuditReport) -> list[AIAnalysis]:
        """Analyze all issues in a report."""
        analyses = []
        for issue in report.issues:
            try:
                analyses.append(self.analyze_issue(issue))
            except Exception as e:
                logger.error("ai_analyzer.issue_failed", error=str(e))
        return analyses


# Singleton
ai_analyzer = AIAnalyzer()
