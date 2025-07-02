#!/usr/bin/env python3
"""
Issue Classification & Automated Prioritization
CLAUDE 4 ENHANCED: Sophisticated priority scoring with multi-dimensional analysis

ULTRATHINK: This script consolidates findings from all analyses and applies
sophisticated scoring algorithms to prioritize fixes based on security impact,
user experience, maintenance burden, and strategic value.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, NamedTuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
from datetime import datetime
import math

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/issue_prioritization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Issue(NamedTuple):
    """Comprehensive issue representation"""
    id: str
    category: str  # version, documentation, security, consistency
    type: str
    severity: str  # critical, high, medium, low
    priority_score: float  # 0-100
    affected_projects: List[str]
    description: str
    impact_assessment: Dict[str, float]  # security, usability, maintenance, strategic
    effort_estimate: str  # trivial, simple, moderate, complex, major
    suggested_fix: str
    dependencies: List[str]  # Other issues that should be fixed first
    batching_group: Optional[str]  # Issues that can be fixed together

@dataclass
class PriorityMatrix:
    """Multi-dimensional priority scoring matrix"""
    security_weight: float = 40.0      # Security issues get highest weight
    usability_weight: float = 25.0     # User experience impact
    maintenance_weight: float = 20.0   # Long-term maintenance burden
    strategic_weight: float = 15.0     # Strategic value (UV migration, etc.)

@dataclass
class BatchGroup:
    """Group of issues that can be addressed together"""
    group_id: str
    name: str
    description: str
    issues: List[str]
    total_priority_score: float
    estimated_effort: str
    strategic_value: str

@dataclass
class PrioritizationReport:
    """Complete issue prioritization analysis"""
    analysis_metadata: Dict[str, Any]
    priority_summary: Dict[str, Any]
    high_priority_issues: List[Issue]
    batching_opportunities: List[BatchGroup]
    strategic_recommendations: List[str]
    all_issues: List[Issue]

class IssuePrioritizer:
    """CLAUDE 4 ENHANCED: Sophisticated priority calculator with ULTRATHINK logic"""
    
    def __init__(self, repo_path: str = "/home/sistr/krljakob/awesome-llm-apps"):
        self.repo_path = Path(repo_path)
        self.priority_matrix = PriorityMatrix()
        
        # THINK HARD: Security-critical packages requiring immediate attention
        self.security_critical_packages = {
            'pillow', 'requests', 'urllib3', 'cryptography', 'pyyaml', 
            'django', 'flask', 'fastapi', 'sqlalchemy', 'pandas',
            'numpy', 'openai', 'anthropic', 'google-genai'
        }
        
        # ULTRATHINK: Effort estimation factors
        self.effort_factors = {
            'file_count': {1: 'trivial', 5: 'simple', 20: 'moderate', 50: 'complex', 100: 'major'},
            'pattern_complexity': {'simple_replace': 1, 'regex_replace': 2, 'structural_change': 4},
            'testing_required': {'none': 1, 'basic': 2, 'integration': 3, 'full_system': 4}
        }
        
        # Strategic batching opportunities
        self.batching_groups = {
            'version_pinning': 'Add version constraints to security-critical packages',
            'uv_migration': 'Migrate projects from pip to UV package management',
            'readme_standardization': 'Standardize README structure and content',
            'api_key_docs': 'Standardize API key configuration documentation',
            'framework_updates': 'Update framework references and examples'
        }

    def load_analysis_data(self) -> Tuple[Dict, Dict, Dict]:
        """Load all previous analysis results"""
        
        repo_analysis = {}
        version_analysis = {}
        doc_analysis = {}
        
        # Load repository analysis
        repo_file = self.repo_path / 'scripts' / 'repository_analysis.json'
        if repo_file.exists():
            with open(repo_file, 'r') as f:
                repo_analysis = json.load(f)
        
        # Load version analysis
        version_file = self.repo_path / 'scripts' / 'version_analysis.json'
        if version_file.exists():
            with open(version_file, 'r') as f:
                version_analysis = json.load(f)
        
        # Load documentation analysis
        doc_file = self.repo_path / 'scripts' / 'doc_consistency_analysis.json'
        if doc_file.exists():
            with open(doc_file, 'r') as f:
                doc_analysis = json.load(f)
        
        return repo_analysis, version_analysis, doc_analysis

    def calculate_security_impact(self, issue_data: Dict[str, Any]) -> float:
        """THINK HARD: Calculate security impact score (0-10)"""
        
        score = 0.0
        
        # Check if it involves security-critical packages
        if issue_data.get('package_name', '').lower() in self.security_critical_packages:
            score += 8.0
            
            # Unpinned security-critical packages are extremely high risk
            if 'unspecified' in str(issue_data.get('versions', '')):
                score += 2.0
        
        # API key and credential issues
        if any(term in str(issue_data).lower() for term in ['api_key', 'secret', 'credential', 'token']):
            score += 3.0
        
        # Outdated packages with known vulnerabilities
        if issue_data.get('is_outdated', False):
            score += 2.0
        
        return min(10.0, score)

    def calculate_usability_impact(self, issue_data: Dict[str, Any]) -> float:
        """Calculate user experience impact score (0-10)"""
        
        score = 0.0
        
        # Installation instruction issues are high impact
        if 'installation' in str(issue_data).lower() or 'setup' in str(issue_data).lower():
            score += 6.0
        
        # Missing README files prevent users from getting started
        if 'readme' in str(issue_data).lower() and 'missing' in str(issue_data).lower():
            score += 7.0
        
        # Broken examples or commands
        if any(term in str(issue_data).lower() for term in ['broken', 'error', 'fail', 'command']):
            score += 4.0
        
        # Documentation quality issues
        if 'documentation' in str(issue_data).lower():
            score += 2.0
        
        # Frequency factor - issues affecting many projects have higher impact
        affected_count = len(issue_data.get('affected_projects', []))
        if affected_count > 20:
            score += 3.0
        elif affected_count > 10:
            score += 2.0
        elif affected_count > 5:
            score += 1.0
        
        return min(10.0, score)

    def calculate_maintenance_impact(self, issue_data: Dict[str, Any]) -> float:
        """Calculate long-term maintenance burden score (0-10)"""
        
        score = 0.0
        
        # Version inconsistencies create ongoing maintenance burden
        inconsistency_count = len(issue_data.get('inconsistencies', []))
        score += min(5.0, inconsistency_count * 0.5)
        
        # Multiple variations of the same thing
        variation_count = len(issue_data.get('variations', []))
        score += min(3.0, variation_count * 0.3)
        
        # Frequency of the issue across projects
        frequency = issue_data.get('frequency', 0)
        if frequency > 50:
            score += 4.0
        elif frequency > 20:
            score += 3.0
        elif frequency > 10:
            score += 2.0
        
        # Technical debt indicators
        if any(term in str(issue_data).lower() for term in ['outdated', 'deprecated', 'legacy']):
            score += 2.0
        
        return min(10.0, score)

    def calculate_strategic_impact(self, issue_data: Dict[str, Any]) -> float:
        """ULTRATHINK: Calculate strategic value score (0-10)"""
        
        score = 0.0
        
        # UV migration opportunities are strategically valuable
        if 'uv' in str(issue_data).lower() or 'migration' in str(issue_data).lower():
            score += 6.0
        
        # Standardization opportunities
        if 'standard' in str(issue_data).lower() or 'consistent' in str(issue_data).lower():
            score += 4.0
        
        # Framework modernization
        if any(term in str(issue_data).lower() for term in ['agno', 'streamlit', 'fastapi']):
            score += 3.0
        
        # Community impact (affects learning and adoption)
        if 'tutorial' in str(issue_data).lower() or 'example' in str(issue_data).lower():
            score += 3.0
        
        # Automation opportunities
        if any(term in str(issue_data).lower() for term in ['automat', 'ci', 'pipeline', 'workflow']):
            score += 2.0
        
        return min(10.0, score)

    def estimate_effort(self, issue_data: Dict[str, Any]) -> str:
        """Estimate effort required to fix the issue"""
        
        effort_points = 0
        
        # Number of affected files/projects
        affected_count = len(issue_data.get('affected_projects', []))
        if affected_count > 50:
            effort_points += 4
        elif affected_count > 20:
            effort_points += 3
        elif affected_count > 5:
            effort_points += 2
        else:
            effort_points += 1
        
        # Complexity of the fix
        if any(term in str(issue_data).lower() for term in ['migration', 'restructure', 'refactor']):
            effort_points += 3
        elif any(term in str(issue_data).lower() for term in ['update', 'change', 'modify']):
            effort_points += 2
        else:
            effort_points += 1
        
        # Testing requirements
        if any(term in str(issue_data).lower() for term in ['security', 'critical', 'breaking']):
            effort_points += 2
        
        # Map effort points to categories
        if effort_points <= 3:
            return 'trivial'
        elif effort_points <= 5:
            return 'simple'
        elif effort_points <= 7:
            return 'moderate'
        elif effort_points <= 9:
            return 'complex'
        else:
            return 'major'

    def calculate_priority_score(self, security: float, usability: float, 
                                maintenance: float, strategic: float) -> float:
        """Calculate weighted priority score (0-100)"""
        
        matrix = self.priority_matrix
        
        weighted_score = (
            security * matrix.security_weight +
            usability * matrix.usability_weight +
            maintenance * matrix.maintenance_weight +
            strategic * matrix.strategic_weight
        ) / 100.0  # Normalize to 0-100 scale
        
        return min(100.0, weighted_score * 10.0)  # Scale to 0-100

    def extract_version_issues(self, version_analysis: Dict) -> List[Issue]:
        """Extract and prioritize version-related issues"""
        
        issues = []
        
        if 'detailed_reports' not in version_analysis:
            return issues
        
        issue_id = 0
        
        for project_report in version_analysis['detailed_reports']:
            project_path = project_report['project_path']
            
            for package_analysis in project_report['package_analyses']:
                package_name = package_analysis['package_name']
                
                # Create issue for unpinned security-critical packages
                # detected_versions is a list of lists: [name, version, file, line, constraint]
                versions = [pkg[1] for pkg in package_analysis['detected_versions']]
                
                if (package_name in self.security_critical_packages and 
                    any('unspecified' in version for version in versions)):
                    
                    issue_data = {
                        'package_name': package_name,
                        'affected_projects': [project_path],
                        'versions': versions,
                        'security_critical': True
                    }
                    
                    security_score = self.calculate_security_impact(issue_data)
                    usability_score = self.calculate_usability_impact(issue_data)
                    maintenance_score = self.calculate_maintenance_impact(issue_data)
                    strategic_score = self.calculate_strategic_impact(issue_data)
                    
                    priority_score = self.calculate_priority_score(
                        security_score, usability_score, maintenance_score, strategic_score
                    )
                    
                    issues.append(Issue(
                        id=f"version_{issue_id}",
                        category="version",
                        type="unpinned_security_package",
                        severity="critical",
                        priority_score=priority_score,
                        affected_projects=[project_path],
                        description=f"Security-critical package '{package_name}' lacks version constraint",
                        impact_assessment={
                            'security': security_score,
                            'usability': usability_score,
                            'maintenance': maintenance_score,
                            'strategic': strategic_score
                        },
                        effort_estimate=self.estimate_effort(issue_data),
                        suggested_fix=f"Pin {package_name} to latest version: {package_analysis.get('latest_version', 'latest')}",
                        dependencies=[],
                        batching_group="version_pinning"
                    ))
                    
                    issue_id += 1
        
        return issues

    def extract_documentation_issues(self, doc_analysis: Dict) -> List[Issue]:
        """Extract and prioritize documentation-related issues"""
        
        issues = []
        
        if 'consistency_issues' not in doc_analysis:
            return issues
        
        issue_id = 0
        
        for consistency_issue in doc_analysis['consistency_issues']:
            # consistency_issue is a list: [issue_type, severity, file_path, line_number, description, suggested_fix]
            if len(consistency_issue) >= 5:
                issue_type = consistency_issue[0]
                severity = consistency_issue[1] 
                file_path = consistency_issue[2]
                description = consistency_issue[4] if len(consistency_issue) > 4 else f"{issue_type} issue"
                suggested_fix = consistency_issue[5] if len(consistency_issue) > 5 else f"Fix {issue_type}"
            else:
                continue  # Skip malformed issues
                
            issue_data = {
                'type': issue_type,
                'severity': severity,
                'affected_projects': [file_path],
                'description': description
            }
            
            security_score = self.calculate_security_impact(issue_data)
            usability_score = self.calculate_usability_impact(issue_data)
            maintenance_score = self.calculate_maintenance_impact(issue_data)
            strategic_score = self.calculate_strategic_impact(issue_data)
            
            priority_score = self.calculate_priority_score(
                security_score, usability_score, maintenance_score, strategic_score
            )
            
            # Determine batching group
            batching_group = None
            if 'readme' in issue_type.lower():
                batching_group = "readme_standardization"
            elif 'api_key' in description.lower():
                batching_group = "api_key_docs"
            
            issues.append(Issue(
                id=f"doc_{issue_id}",
                category="documentation",
                type=issue_type,
                severity=severity,
                priority_score=priority_score,
                affected_projects=[file_path],
                description=description,
                impact_assessment={
                    'security': security_score,
                    'usability': usability_score,
                    'maintenance': maintenance_score,
                    'strategic': strategic_score
                },
                effort_estimate=self.estimate_effort(issue_data),
                suggested_fix=suggested_fix,
                dependencies=[],
                batching_group=batching_group
            ))
            
            issue_id += 1
        
        return issues

    def extract_strategic_issues(self, repo_analysis: Dict, version_analysis: Dict) -> List[Issue]:
        """Extract strategic improvement opportunities"""
        
        issues = []
        
        # UV migration opportunity
        if 'package_manager_distribution' in repo_analysis.get('repository_profile', {}):
            pm_dist = repo_analysis['repository_profile']['package_manager_distribution']
            pip_projects = pm_dist.get('pip', 0)
            
            if pip_projects > 50:  # Significant migration opportunity
                issue_data = {
                    'type': 'uv_migration',
                    'affected_projects': [f"{pip_projects} projects using pip"],
                    'strategic_value': True
                }
                
                security_score = self.calculate_security_impact(issue_data)
                usability_score = self.calculate_usability_impact(issue_data)
                maintenance_score = self.calculate_maintenance_impact(issue_data)
                strategic_score = self.calculate_strategic_impact(issue_data)
                
                priority_score = self.calculate_priority_score(
                    security_score, usability_score, maintenance_score, strategic_score
                )
                
                issues.append(Issue(
                    id="strategic_uv_migration",
                    category="strategic",
                    type="uv_migration_opportunity",
                    severity="medium",
                    priority_score=priority_score,
                    affected_projects=[f"{pip_projects} projects"],
                    description=f"Opportunity to migrate {pip_projects} projects from pip to UV",
                    impact_assessment={
                        'security': security_score,
                        'usability': usability_score,
                        'maintenance': maintenance_score,
                        'strategic': strategic_score
                    },
                    effort_estimate="major",
                    suggested_fix="Create UV migration guide and gradually migrate high-impact projects",
                    dependencies=[],
                    batching_group="uv_migration"
                ))
        
        return issues

    def create_batching_groups(self, all_issues: List[Issue]) -> List[BatchGroup]:
        """Create batching opportunities for related issues"""
        
        batches = defaultdict(list)
        
        # Group issues by batching_group
        for issue in all_issues:
            if issue.batching_group:
                batches[issue.batching_group].append(issue)
        
        batch_groups = []
        
        for group_id, group_issues in batches.items():
            if len(group_issues) >= 3:  # Only create batches with 3+ issues
                total_score = sum(issue.priority_score for issue in group_issues)
                
                # Estimate batch effort
                effort_counts = Counter(issue.effort_estimate for issue in group_issues)
                if effort_counts.get('major', 0) > 0:
                    batch_effort = 'major'
                elif effort_counts.get('complex', 0) > 0:
                    batch_effort = 'complex'
                elif effort_counts.get('moderate', 0) > 0:
                    batch_effort = 'moderate'
                else:
                    batch_effort = 'simple'
                
                # Determine strategic value
                strategic_scores = [issue.impact_assessment['strategic'] for issue in group_issues]
                avg_strategic = sum(strategic_scores) / len(strategic_scores)
                
                if avg_strategic > 7:
                    strategic_value = 'high'
                elif avg_strategic > 4:
                    strategic_value = 'medium'
                else:
                    strategic_value = 'low'
                
                batch_groups.append(BatchGroup(
                    group_id=group_id,
                    name=self.batching_groups.get(group_id, group_id.replace('_', ' ').title()),
                    description=f"Batch of {len(group_issues)} related issues",
                    issues=[issue.id for issue in group_issues],
                    total_priority_score=total_score,
                    estimated_effort=batch_effort,
                    strategic_value=strategic_value
                ))
        
        return sorted(batch_groups, key=lambda x: x.total_priority_score, reverse=True)

    def generate_strategic_recommendations(self, all_issues: List[Issue], 
                                         batching_groups: List[BatchGroup]) -> List[str]:
        """Generate high-level strategic recommendations"""
        
        recommendations = []
        
        # Critical security recommendations
        critical_security = [i for i in all_issues if i.severity == 'critical' and i.impact_assessment['security'] > 7]
        if critical_security:
            recommendations.append(f"🚨 IMMEDIATE: Address {len(critical_security)} critical security issues before any other work")
        
        # High-impact batching opportunities
        high_impact_batches = [b for b in batching_groups if b.strategic_value == 'high']
        if high_impact_batches:
            recommendations.append(f"🎯 STRATEGIC: Prioritize {len(high_impact_batches)} high-impact batch opportunities for maximum efficiency")
        
        # Automation recommendations
        if len(all_issues) > 50:
            recommendations.append("🤖 AUTOMATION: Implement automated dependency scanning and documentation linting to prevent future issues")
        
        # Standardization opportunities
        version_issues = [i for i in all_issues if i.category == 'version']
        if len(version_issues) > 20:
            recommendations.append("📋 STANDARDIZATION: Create repository-wide dependency management standards")
        
        # Resource allocation
        total_priority = sum(issue.priority_score for issue in all_issues)
        if total_priority > 1000:
            recommendations.append("👥 RESOURCES: Consider dedicating focused sprint(s) to documentation and dependency hygiene")
        
        return recommendations

    def analyze_all_issues(self) -> PrioritizationReport:
        """ULTRATHINK: Comprehensive issue analysis and prioritization"""
        
        logger.info("Starting comprehensive issue prioritization...")
        
        # Load all analysis data
        repo_analysis, version_analysis, doc_analysis = self.load_analysis_data()
        
        # Extract issues from each analysis
        version_issues = self.extract_version_issues(version_analysis)
        doc_issues = self.extract_documentation_issues(doc_analysis)
        strategic_issues = self.extract_strategic_issues(repo_analysis, version_analysis)
        
        # Combine all issues
        all_issues = version_issues + doc_issues + strategic_issues
        
        # Sort by priority score
        all_issues.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Create batching opportunities
        batching_groups = self.create_batching_groups(all_issues)
        
        # Generate strategic recommendations
        strategic_recommendations = self.generate_strategic_recommendations(all_issues, batching_groups)
        
        # Calculate summary statistics
        priority_summary = {
            'total_issues': len(all_issues),
            'critical_severity': len([i for i in all_issues if i.severity == 'critical']),
            'high_priority': len([i for i in all_issues if i.priority_score > 80]),
            'medium_priority': len([i for i in all_issues if 50 < i.priority_score <= 80]),
            'low_priority': len([i for i in all_issues if i.priority_score <= 50]),
            'average_priority_score': sum(i.priority_score for i in all_issues) / len(all_issues) if all_issues else 0,
            'categories': {
                'version': len([i for i in all_issues if i.category == 'version']),
                'documentation': len([i for i in all_issues if i.category == 'documentation']),
                'strategic': len([i for i in all_issues if i.category == 'strategic'])
            }
        }
        
        # High priority issues (top 20%)
        high_priority_count = max(1, len(all_issues) // 5)
        high_priority_issues = all_issues[:high_priority_count]
        
        return PrioritizationReport(
            analysis_metadata={
                'timestamp': datetime.now().isoformat(),
                'total_issues_analyzed': len(all_issues),
                'prioritization_algorithm': 'multi_dimensional_weighted_scoring',
                'weight_matrix': asdict(self.priority_matrix)
            },
            priority_summary=priority_summary,
            high_priority_issues=high_priority_issues,
            batching_opportunities=batching_groups,
            strategic_recommendations=strategic_recommendations,
            all_issues=all_issues
        )

    def save_results(self, report: PrioritizationReport, output_file: str = 'scripts/issue_prioritization.json'):
        """Save prioritization analysis results"""
        
        # Convert report to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Issue prioritization results saved to {output_file}")

def main():
    """Main analysis execution"""
    
    print("🎯 Starting Issue Classification & Prioritization...")
    print("ULTRATHINK: Applying sophisticated multi-dimensional scoring algorithms...")
    
    prioritizer = IssuePrioritizer()
    report = prioritizer.analyze_all_issues()
    prioritizer.save_results(report)
    
    # Print executive summary
    summary = report.priority_summary
    print(f"\n📊 Issue Prioritization Complete!")
    print(f"Total Issues Identified: {summary['total_issues']}")
    print(f"Critical Severity: {summary['critical_severity']}")
    print(f"High Priority (>80): {summary['high_priority']}")
    print(f"Medium Priority (50-80): {summary['medium_priority']}")
    print(f"Low Priority (<50): {summary['low_priority']}")
    print(f"Average Priority Score: {summary['average_priority_score']:.1f}/100")
    
    print(f"\nIssue Categories:")
    for category, count in summary['categories'].items():
        print(f"  {category.title()}: {count}")
    
    print(f"\nTop High-Priority Issues:")
    for issue in report.high_priority_issues[:3]:
        print(f"  • {issue.description} (Score: {issue.priority_score:.1f})")
    
    print(f"\nBatching Opportunities: {len(report.batching_opportunities)}")
    for batch in report.batching_opportunities[:2]:
        print(f"  • {batch.name}: {len(batch.issues)} issues (Score: {batch.total_priority_score:.1f})")
    
    print(f"\nStrategic Recommendations:")
    for rec in report.strategic_recommendations[:3]:
        print(f"  • {rec}")
    
    print(f"\nDetailed results saved to: scripts/issue_prioritization.json")
    print(f"Logs available at: scripts/issue_prioritization.log")

if __name__ == "__main__":
    main()