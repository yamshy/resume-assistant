from __future__ import annotations

import re
from typing import Any

from resume_core.agents.base_agent import FunctionBackedAgent
from resume_core.models.job_analysis import JobAnalysis, JobContext, JobRequirement


class JobAnalysisAgent(FunctionBackedAgent[JobAnalysis]):
    _REQUIREMENT_TEMPLATES = {
        "python": {
            "name": "Python Expertise",
            "keywords": ["python", "backend"],
            "importance": "high",
            "description": "Build and maintain production Python services.",
        },
        "fastapi": {
            "name": "FastAPI Services",
            "keywords": ["fastapi", "api"],
            "importance": "high",
            "description": "Design and optimize FastAPI-based systems.",
        },
        "aws": {
            "name": "Cloud Infrastructure (AWS)",
            "keywords": ["aws", "cloud"],
            "importance": "high",
            "description": "Operate and improve workloads running on AWS.",
        },
        "azure": {
            "name": "Cloud Infrastructure (Azure)",
            "keywords": ["azure", "cloud"],
            "importance": "medium",
            "description": "Deploy and manage services in Azure environments.",
        },
        "sql": {
            "name": "Data Querying",
            "keywords": ["sql", "data"],
            "importance": "medium",
            "description": "Leverage SQL and analytics to inform decisions.",
        },
        "mentoring": {
            "name": "Team Leadership",
            "keywords": ["mentor", "mentoring", "lead"],
            "importance": "medium",
            "description": "Coach and develop junior teammates.",
        },
        "communication": {
            "name": "Communication",
            "keywords": ["communication", "stakeholder"],
            "importance": "medium",
            "description": "Communicate insights and plans clearly across teams.",
        },
        "cicd": {
            "name": "Automation & CI/CD",
            "keywords": ["ci/cd", "automation", "pipeline"],
            "importance": "medium",
            "description": "Maintain automated testing and deployment pipelines.",
        },
        "security": {
            "name": "Security Mindset",
            "keywords": ["security", "threat"],
            "importance": "medium",
            "description": "Design with security and reliability in mind.",
        },
    }

    _STOPWORDS = {
        "the",
        "and",
        "with",
        "for",
        "team",
        "skills",
        "ability",
        "experience",
        "years",
        "including",
        "strong",
        "work",
        "collaboration",
        "develop",
        "build",
        "support",
        "services",
        "developers",
        "needed",
    }

    def __init__(self) -> None:
        super().__init__(
            name="job-analysis-agent",
            instructions=(
                "Analyze job posting text, extract the intended role, seniority, company references, "
                "and synthesise structured requirement objects."
            ),
            output_model=JobAnalysis,
        )

    def build_output(self, payload: dict[str, Any]) -> JobAnalysis:
        job_posting = str(payload.get("job_posting") or payload.get("text") or "").strip()
        summary = self._build_summary(job_posting)
        keywords = self._extract_keywords(job_posting)
        requirements = self._build_requirements(job_posting, keywords)
        context = JobContext(
            role=self._extract_role(job_posting),
            company=self._extract_company(job_posting),
            seniority=self._infer_seniority(job_posting),
            raw_text=job_posting,
        )
        return JobAnalysis(
            summary=summary,
            requirements=requirements,
            keywords=keywords,
            context=context,
        )

    def _build_summary(self, text: str) -> str:
        if not text:
            return "No job description provided."
        sentences = re.split(r"[\n\.]+", text)
        for sentence in sentences:
            stripped = sentence.strip()
            if stripped:
                return stripped[:280]
        return text[:280]

    def _extract_keywords(self, text: str) -> list[str]:
        normalized = text.lower()
        collected: set[str] = set()
        for template in self._REQUIREMENT_TEMPLATES.values():
            for keyword in template["keywords"]:
                if keyword in normalized:
                    collected.add(keyword.replace("/", "/").lower())
        if not collected:
            words = re.findall(r"[a-zA-Z]{4,}", normalized)
            for word in words:
                if word not in self._STOPWORDS:
                    collected.add(word)
                    if len(collected) >= 10:
                        break
        ordered = sorted(collected)
        return ordered

    def _build_requirements(self, text: str, keywords: list[str]) -> list[JobRequirement]:
        normalized = text.lower()
        requirements: list[JobRequirement] = []
        for template in self._REQUIREMENT_TEMPLATES.values():
            if any(token in normalized for token in template["keywords"]):
                requirements.append(
                    JobRequirement(
                        name=template["name"],
                        importance=template["importance"],
                        keywords=template["keywords"],
                        description=template["description"],
                    )
                )
        if not requirements:
            fallback_keywords = keywords[:5] if keywords else ["collaboration", "delivery"]
            requirements.append(
                JobRequirement(
                    name="Core Competencies",
                    importance="medium",
                    keywords=fallback_keywords,
                    description="Identify core technical and collaboration capabilities for the role.",
                )
            )
        return requirements

    def _extract_role(self, text: str) -> str | None:
        if not text:
            return None
        patterns = [
            r"(?:seeking|seeks|seeking an|seeking a|looking for an|looking for a|hiring an|hiring a|need an|need a)\s+(?P<title>[^\n,\.]+)",
            r"join our\s+(?P<title>[a-zA-Z0-9 /&-]+)\s+team",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group("title").strip().title()
        first_line = text.splitlines()[0] if text.splitlines() else text
        first_sentence = re.split(r"[\.!?]", first_line)[0]
        cleaned = first_sentence.replace("We are", "").replace("Join", "").strip()
        return cleaned.title() if cleaned else None

    def _extract_company(self, text: str) -> str | None:
        if not text:
            return None
        match = re.search(r"join (?:our|the) ([a-zA-Z0-9 &-]+) team", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
        match = re.search(r"at ([A-Z][A-Za-z0-9 &-]+)", text)
        if match:
            return match.group(1).strip()
        return None

    def _infer_seniority(self, text: str) -> str | None:
        lowered = text.lower()
        for level in ["principal", "staff", "senior", "lead", "junior"]:
            if level in lowered:
                return level
        return None

    async def analyze(self, *, job_posting: str) -> JobAnalysis:
        return await self.run({"job_posting": job_posting})
