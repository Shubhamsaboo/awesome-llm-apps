#!/usr/bin/env python3
"""
Documentation Consistency Analyzer
CLAUDE 4 ENHANCED: Comprehensive documentation analysis with semantic understanding

ULTRATHINK: This script performs deep analysis of documentation patterns, detects 
semantic conflicts, and identifies opportunities for standardization across
the awesome-llm-apps repository.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, NamedTuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
from datetime import datetime
import difflib

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/doc_consistency_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentationIssue(NamedTuple):
    """Structured documentation issue information"""
    issue_type: str
    severity: str  # critical, warning, suggestion
    file_path: str
    line_number: Optional[int]
    description: str
    suggested_fix: str

@dataclass
class InstallationPattern:
    """Installation instruction patterns found across projects"""
    command: str
    frequency: int
    variations: List[str]
    projects: List[str]

@dataclass
class DocumentationAnalysis:
    """Complete documentation analysis results"""
    project_path: str
    readme_exists: bool
    installation_instructions: List[str]
    version_references: List[str]
    api_key_mentions: List[str]
    framework_mentions: List[str]
    consistency_issues: List[DocumentationIssue]
    readability_score: float
    completeness_score: float

@dataclass
class RepositoryDocReport:
    """Complete repository documentation analysis"""
    analysis_metadata: Dict[str, Any]
    global_patterns: Dict[str, Any]
    installation_patterns: List[InstallationPattern]
    consistency_issues: List[DocumentationIssue]
    project_analyses: List[DocumentationAnalysis]
    recommendations: List[str]

class DocumentationAnalyzer:
    """CLAUDE 4 ENHANCED: Advanced documentation analyzer with semantic understanding"""
    
    def __init__(self, repo_path: str = "/home/sistr/krljakob/awesome-llm-apps"):
        self.repo_path = Path(repo_path)
        
        # THINK HARD: Common documentation patterns and their variations
        self.installation_patterns = {
            'pip_install': [
                r'pip install -r requirements\.txt',
                r'pip install \w+',
                r'python -m pip install',
            ],
            'uv_install': [
                r'uv pip install -r requirements\.txt',
                r'uv install',
                r'uv sync',
            ],
            'poetry_install': [
                r'poetry install',
                r'poetry add \w+',
            ],
            'npm_install': [
                r'npm install',
                r'npm i',
                r'pnpm install',
                r'bun install',
            ]
        }
        
        # ULTRATHINK: Version reference patterns that could be inconsistent
        self.version_patterns = {
            'python_version': [
                r'python\s*([><=]+)\s*([\d.]+)',
                r'requires python ([\d.]+)',
                r'python ([\d.]+) or higher',
            ],
            'package_version': [
                r'(\w+)==([\d.]+)',
                r'(\w+)\s*>=\s*([\d.]+)',
                r'version ([\d.]+)',
            ],
            'framework_version': [
                r'streamlit\s*([\d.]+)',
                r'fastapi\s*([\d.]+)',
                r'nextjs?\s*([\d.]+)',
            ]
        }
        
        # Common API key patterns for documentation consistency
        self.api_key_patterns = [
            r'OPENAI_API_KEY',
            r'ANTHROPIC_API_KEY', 
            r'GOOGLE_API_KEY',
            r'GEMINI_API_KEY',
            r'TOGETHER_API_KEY',
            r'export \w+_API_KEY',
            r'\.env.*API_KEY',
        ]
        
        # Framework mention patterns
        self.framework_patterns = {
            'streamlit': [r'streamlit', r'st\.', r'streamlit run'],
            'fastapi': [r'fastapi', r'uvicorn', r'FastAPI'],
            'agno': [r'agno', r'phi(?:data)?', r'Agent'],
            'nextjs': [r'next\.?js', r'next dev', r'next build'],
            'react': [r'react', r'jsx', r'tsx'],
        }
        
        # Standard documentation sections that should be present
        self.expected_sections = {
            'title': [r'^#\s+(.+)', r'^(.+)\n=+'],
            'description': [r'description', r'about', r'overview'],
            'installation': [r'install', r'setup', r'getting started'],
            'usage': [r'usage', r'how to', r'running', r'example'],
            'requirements': [r'requirements', r'dependencies', r'prerequisites'],
            'api_keys': [r'api.*key', r'environment', r'configuration'],
        }

    def extract_installation_instructions(self, content: str) -> List[str]:
        """CLAUDE 4: Extract all installation-related commands with context"""
        
        instructions = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for code blocks or command indicators
            if any(indicator in line.lower() for indicator in ['```', '`', '$', 'pip', 'npm', 'uv', 'poetry']):
                # Extract the actual command
                clean_line = re.sub(r'^[`$\s]*', '', line)
                clean_line = re.sub(r'[`]*$', '', clean_line)
                
                if clean_line.strip():
                    # Check if it matches our installation patterns
                    for pattern_type, patterns in self.installation_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, clean_line, re.IGNORECASE):
                                instructions.append(clean_line.strip())
                                break
        
        return list(set(instructions))  # Remove duplicates

    def extract_version_references(self, content: str) -> List[str]:
        """Extract version references from documentation"""
        
        versions = []
        
        for pattern_type, patterns in self.version_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        versions.append(f"{pattern_type}: {' '.join(match)}")
                    else:
                        versions.append(f"{pattern_type}: {match}")
        
        return versions

    def extract_api_key_mentions(self, content: str) -> List[str]:
        """Extract API key configuration mentions"""
        
        api_keys = []
        
        for pattern in self.api_key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            api_keys.extend(matches)
        
        return list(set(api_keys))

    def extract_framework_mentions(self, content: str) -> List[str]:
        """Extract framework mentions and their contexts"""
        
        frameworks = []
        
        for framework, patterns in self.framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    frameworks.append(framework)
                    break
        
        return frameworks

    def calculate_readability_score(self, content: str) -> float:
        """THINK HARD: Calculate documentation readability score"""
        
        score = 10.0  # Start with perfect score
        
        # Penalize for very long lines
        lines = content.split('\n')
        long_lines = [line for line in lines if len(line) > 120]
        if long_lines:
            score -= min(2.0, len(long_lines) * 0.1)
        
        # Penalize for missing headings
        headings = [line for line in lines if line.startswith('#')]
        if len(headings) < 3:
            score -= 1.0
        
        # Penalize for no code blocks
        if '```' not in content and '`' not in content:
            score -= 1.0
        
        # Reward for good structure indicators
        if any(section in content.lower() for section in ['installation', 'usage', 'example']):
            score += 0.5
        
        return max(0.0, min(10.0, score))

    def calculate_completeness_score(self, content: str, project_type: str) -> float:
        """ULTRATHINK: Calculate documentation completeness score"""
        
        score = 0.0
        max_score = 10.0
        
        # Check for essential sections
        section_weights = {
            'title': 1.0,
            'description': 2.0,
            'installation': 2.5,
            'usage': 2.0,
            'requirements': 1.5,
            'api_keys': 1.0 if 'openai' in content.lower() or 'api' in content.lower() else 0.0
        }
        
        for section, weight in section_weights.items():
            if section in self.expected_sections:
                for pattern in self.expected_sections[section]:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += weight
                        break
        
        return min(10.0, score)

    def detect_consistency_issues(self, content: str, file_path: str, 
                                 global_patterns: Dict[str, Any]) -> List[DocumentationIssue]:
        """CLAUDE 4: Detect semantic and structural consistency issues"""
        
        issues = []
        lines = content.split('\n')
        
        # Check for installation command consistency
        installation_commands = self.extract_installation_instructions(content)
        for cmd in installation_commands:
            if 'pip install -r requirements.txt' in cmd:
                # Check if this project actually has requirements.txt
                req_file = Path(file_path).parent / 'requirements.txt'
                if not req_file.exists():
                    issues.append(DocumentationIssue(
                        issue_type="missing_file",
                        severity="critical",
                        file_path=file_path,
                        line_number=None,
                        description="Documentation mentions requirements.txt but file doesn't exist",
                        suggested_fix="Create requirements.txt or update installation instructions"
                    ))
        
        # Check for API key configuration inconsistency
        api_mentions = self.extract_api_key_mentions(content)
        if api_mentions and '.env' not in content.lower():
            issues.append(DocumentationIssue(
                issue_type="incomplete_config",
                severity="warning",
                file_path=file_path,
                line_number=None,
                description="API keys mentioned but no .env configuration instructions",
                suggested_fix="Add .env file setup instructions"
            ))
        
        # Check for Python version inconsistency
        python_versions = []
        for line_num, line in enumerate(lines, 1):
            for pattern in self.version_patterns['python_version']:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    python_versions.extend(matches)
        
        if len(set(python_versions)) > 1:
            issues.append(DocumentationIssue(
                issue_type="version_inconsistency",
                severity="warning",
                file_path=file_path,
                line_number=None,
                description=f"Multiple Python versions mentioned: {set(python_versions)}",
                suggested_fix="Standardize Python version requirements"
            ))
        
        # Check for missing essential sections
        essential_missing = []
        for section in ['installation', 'usage']:
            if not any(re.search(pattern, content, re.IGNORECASE) 
                      for pattern in self.expected_sections.get(section, [])):
                essential_missing.append(section)
        
        if essential_missing:
            issues.append(DocumentationIssue(
                issue_type="missing_sections",
                severity="warning",
                file_path=file_path,
                line_number=None,
                description=f"Missing essential sections: {', '.join(essential_missing)}",
                suggested_fix=f"Add {', '.join(essential_missing)} sections to README"
            ))
        
        # Check for outdated framework references
        if 'phidata' in content.lower() and 'agno' not in content.lower():
            issues.append(DocumentationIssue(
                issue_type="outdated_reference",
                severity="suggestion",
                file_path=file_path,
                line_number=None,
                description="References old 'phidata' instead of current 'agno'",
                suggested_fix="Update references from 'phidata' to 'agno'"
            ))
        
        return issues

    def analyze_project_documentation(self, project_path: Path, 
                                     global_patterns: Dict[str, Any]) -> DocumentationAnalysis:
        """ULTRATHINK: Comprehensive documentation analysis for a single project"""
        
        logger.info(f"Analyzing documentation for: {project_path}")
        
        # Find README file
        readme_files = []
        for readme_name in ['README.md', 'README.rst', 'README.txt', 'readme.md']:
            readme_path = project_path / readme_name
            if readme_path.exists():
                readme_files.append(readme_path)
        
        if not readme_files:
            return DocumentationAnalysis(
                project_path=str(project_path.relative_to(self.repo_path)),
                readme_exists=False,
                installation_instructions=[],
                version_references=[],
                api_key_mentions=[],
                framework_mentions=[],
                consistency_issues=[DocumentationIssue(
                    issue_type="missing_readme",
                    severity="critical",
                    file_path=str(project_path.relative_to(self.repo_path)),
                    line_number=None,
                    description="No README file found",
                    suggested_fix="Create README.md with project documentation"
                )],
                readability_score=0.0,
                completeness_score=0.0
            )
        
        # Analyze the README content
        readme_path = readme_files[0]  # Use the first one found
        try:
            content = readme_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error reading {readme_path}: {e}")
            return DocumentationAnalysis(
                project_path=str(project_path.relative_to(self.repo_path)),
                readme_exists=True,
                installation_instructions=[],
                version_references=[],
                api_key_mentions=[],
                framework_mentions=[],
                consistency_issues=[DocumentationIssue(
                    issue_type="unreadable_readme",
                    severity="critical",
                    file_path=str(readme_path.relative_to(self.repo_path)),
                    line_number=None,
                    description=f"README file cannot be read: {e}",
                    suggested_fix="Fix file encoding or corruption issues"
                )],
                readability_score=0.0,
                completeness_score=0.0
            )
        
        # Extract documentation elements
        installation_instructions = self.extract_installation_instructions(content)
        version_references = self.extract_version_references(content)
        api_key_mentions = self.extract_api_key_mentions(content)
        framework_mentions = self.extract_framework_mentions(content)
        
        # Calculate scores
        readability_score = self.calculate_readability_score(content)
        completeness_score = self.calculate_completeness_score(content, 'ai_agent')
        
        # Detect consistency issues
        consistency_issues = self.detect_consistency_issues(
            content, str(readme_path.relative_to(self.repo_path)), global_patterns
        )
        
        return DocumentationAnalysis(
            project_path=str(project_path.relative_to(self.repo_path)),
            readme_exists=True,
            installation_instructions=installation_instructions,
            version_references=version_references,
            api_key_mentions=api_key_mentions,
            framework_mentions=framework_mentions,
            consistency_issues=consistency_issues,
            readability_score=readability_score,
            completeness_score=completeness_score
        )

    def analyze_repository_patterns(self, project_analyses: List[DocumentationAnalysis]) -> Dict[str, Any]:
        """Analyze global patterns across all documentation"""
        
        # Installation command frequency
        all_install_commands = []
        for analysis in project_analyses:
            all_install_commands.extend(analysis.installation_instructions)
        
        install_frequency = Counter(all_install_commands)
        
        # Framework frequency
        all_frameworks = []
        for analysis in project_analyses:
            all_frameworks.extend(analysis.framework_mentions)
        
        framework_frequency = Counter(all_frameworks)
        
        # API key patterns
        all_api_keys = []
        for analysis in project_analyses:
            all_api_keys.extend(analysis.api_key_mentions)
        
        api_key_frequency = Counter(all_api_keys)
        
        # Quality metrics
        avg_readability = sum(a.readability_score for a in project_analyses) / len(project_analyses) if project_analyses else 0
        avg_completeness = sum(a.completeness_score for a in project_analyses) / len(project_analyses) if project_analyses else 0
        
        return {
            'installation_commands': dict(install_frequency.most_common(10)),
            'framework_usage': dict(framework_frequency),
            'api_key_patterns': dict(api_key_frequency),
            'quality_metrics': {
                'average_readability': avg_readability,
                'average_completeness': avg_completeness,
                'projects_with_readme': len([a for a in project_analyses if a.readme_exists]),
                'projects_missing_readme': len([a for a in project_analyses if not a.readme_exists])
            }
        }

    def generate_installation_patterns(self, project_analyses: List[DocumentationAnalysis]) -> List[InstallationPattern]:
        """Generate standardized installation pattern recommendations"""
        
        # Group similar installation commands
        command_groups = defaultdict(list)
        
        for analysis in project_analyses:
            for cmd in analysis.installation_instructions:
                # Normalize the command for grouping
                normalized = re.sub(r'\s+', ' ', cmd.lower().strip())
                command_groups[normalized].append((cmd, analysis.project_path))
        
        patterns = []
        for normalized_cmd, instances in command_groups.items():
            if len(instances) >= 3:  # Commands that appear in 3+ projects
                variations = list(set(inst[0] for inst in instances))
                projects = [inst[1] for inst in instances]
                
                patterns.append(InstallationPattern(
                    command=normalized_cmd,
                    frequency=len(instances),
                    variations=variations,
                    projects=projects[:10]  # Limit project list
                ))
        
        return sorted(patterns, key=lambda x: x.frequency, reverse=True)

    def generate_recommendations(self, project_analyses: List[DocumentationAnalysis], 
                               global_patterns: Dict[str, Any]) -> List[str]:
        """CLAUDE 4: Generate actionable recommendations"""
        
        recommendations = []
        
        # Critical issues first
        critical_count = sum(
            len([issue for issue in analysis.consistency_issues if issue.severity == 'critical'])
            for analysis in project_analyses
        )
        
        if critical_count > 0:
            recommendations.append(f"🚨 CRITICAL: Fix {critical_count} critical documentation issues (missing READMEs, broken references)")
        
        # Quality improvements
        low_quality_count = len([a for a in project_analyses if a.readability_score < 5.0 or a.completeness_score < 5.0])
        if low_quality_count > 10:
            recommendations.append(f"📚 Improve documentation quality for {low_quality_count} projects with low readability/completeness scores")
        
        # Standardization opportunities
        if len(global_patterns['installation_commands']) > 5:
            recommendations.append("🔄 Standardize installation instructions - found multiple command variations")
        
        # Specific improvement opportunities
        pip_projects = len([a for a in project_analyses if any('pip install' in cmd for cmd in a.installation_instructions)])
        if pip_projects > 50:
            recommendations.append(f"📦 Consider UV migration guidance - {pip_projects} projects still using traditional pip")
        
        # Framework reference consistency
        if 'phidata' in str(global_patterns) and 'agno' in str(global_patterns):
            recommendations.append("🔄 Update framework references from 'phidata' to 'agno' for consistency")
        
        # API key standardization
        if len(global_patterns['api_key_patterns']) > 0:
            recommendations.append("🔑 Standardize API key configuration instructions across projects")
        
        recommendations.append("✅ Implement documentation linting in CI/CD pipeline")
        
        return recommendations

    def scan_all_projects(self) -> RepositoryDocReport:
        """ULTRATHINK: Comprehensive documentation analysis across all projects"""
        
        logger.info("Starting comprehensive documentation analysis...")
        
        # Load project data from previous analysis
        analysis_file = self.repo_path / 'scripts' / 'repository_analysis.json'
        if not analysis_file.exists():
            logger.error("Repository analysis not found. Run repository_profiler.py first.")
            return RepositoryDocReport(
                analysis_metadata={},
                global_patterns={},
                installation_patterns=[],
                consistency_issues=[],
                project_analyses=[],
                recommendations=["❌ Run repository_profiler.py first"]
            )
        
        with open(analysis_file, 'r') as f:
            repo_data = json.load(f)
        
        projects = repo_data['repository_profile']['projects']
        project_analyses = []
        
        # Analyze each project
        for project_info in projects:
            project_path = self.repo_path / project_info['path']
            
            try:
                analysis = self.analyze_project_documentation(project_path, {})
                project_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze documentation for {project_path}: {e}")
                continue
        
        # Analyze global patterns
        global_patterns = self.analyze_repository_patterns(project_analyses)
        
        # Generate installation patterns
        installation_patterns = self.generate_installation_patterns(project_analyses)
        
        # Collect all consistency issues
        all_issues = []
        for analysis in project_analyses:
            all_issues.extend(analysis.consistency_issues)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(project_analyses, global_patterns)
        
        # Create comprehensive report
        report = RepositoryDocReport(
            analysis_metadata={
                'timestamp': datetime.now().isoformat(),
                'total_projects_analyzed': len(project_analyses),
                'total_issues_found': len(all_issues),
                'critical_issues': len([i for i in all_issues if i.severity == 'critical']),
                'warning_issues': len([i for i in all_issues if i.severity == 'warning']),
                'suggestion_issues': len([i for i in all_issues if i.severity == 'suggestion'])
            },
            global_patterns=global_patterns,
            installation_patterns=installation_patterns,
            consistency_issues=all_issues,
            project_analyses=project_analyses,
            recommendations=recommendations
        )
        
        logger.info(f"Documentation analysis complete: {len(project_analyses)} projects analyzed")
        logger.info(f"Found {len(all_issues)} total issues across all projects")
        
        return report

    def save_results(self, report: RepositoryDocReport, output_file: str = 'scripts/doc_consistency_analysis.json'):
        """Save documentation analysis results"""
        
        # Convert report to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Documentation analysis results saved to {output_file}")

def main():
    """Main analysis execution"""
    
    print("📚 Starting Documentation Consistency Analysis...")
    print("ULTRATHINK: Analyzing documentation patterns and semantic consistency...")
    
    analyzer = DocumentationAnalyzer()
    report = analyzer.scan_all_projects()
    analyzer.save_results(report)
    
    # Print executive summary
    metadata = report.analysis_metadata
    print(f"\n📊 Documentation Analysis Complete!")
    print(f"Projects Analyzed: {metadata['total_projects_analyzed']}")
    print(f"Total Issues Found: {metadata['total_issues_found']}")
    print(f"Critical Issues: {metadata['critical_issues']}")
    print(f"Warning Issues: {metadata['warning_issues']}")
    print(f"Suggestion Issues: {metadata['suggestion_issues']}")
    
    if report.global_patterns['quality_metrics']:
        quality = report.global_patterns['quality_metrics']
        print(f"Average Readability Score: {quality['average_readability']:.1f}/10")
        print(f"Average Completeness Score: {quality['average_completeness']:.1f}/10")
        print(f"Projects with README: {quality['projects_with_readme']}")
        print(f"Projects missing README: {quality['projects_missing_readme']}")
    
    print(f"\nTop Installation Commands:")
    for cmd, freq in list(report.global_patterns['installation_commands'].items())[:3]:
        print(f"  {cmd}: {freq} projects")
    
    print(f"\nDetailed results saved to: scripts/doc_consistency_analysis.json")
    print(f"Logs available at: scripts/doc_consistency_analysis.log")

if __name__ == "__main__":
    main()