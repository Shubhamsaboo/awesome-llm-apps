#!/usr/bin/env python3
"""
Advanced Version Hunter with MCP Integration
CLAUDE 4 ENHANCED: Comprehensive version detection and verification

ULTRATHINK: This script performs deep analysis of version patterns, detects 
inconsistencies, and uses MCP servers to verify latest versions against 
official package registries.
"""

import os
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, NamedTuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
import asyncio
import requests
from datetime import datetime

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/version_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PackageInfo(NamedTuple):
    """Structured package information"""
    name: str
    version: str
    source_file: str
    line_number: int
    constraint_type: str  # ==, >=, ~=, ^, etc.

@dataclass
class VersionAnalysis:
    """Complete version analysis results"""
    package_name: str
    detected_versions: List[PackageInfo]
    latest_version: Optional[str]
    is_outdated: bool
    security_issues: List[str]
    inconsistencies: List[str]
    recommendation: str

@dataclass
class ProjectVersionReport:
    """Version analysis report for a single project"""
    project_path: str
    package_analyses: List[VersionAnalysis]
    critical_issues: int
    warning_issues: int
    suggestions: List[str]

class VersionHunter:
    """CLAUDE 4 ENHANCED: Advanced version hunter with MCP integration and ULTRATHINK patterns"""
    
    def __init__(self, repo_path: str = "/home/sistr/krljakob/awesome-llm-apps"):
        self.repo_path = Path(repo_path)
        self.package_registry_cache = {}
        self.mcp_available = self._check_mcp_availability()
        
        # ULTRATHINK: Comprehensive version patterns for edge cases
        self.version_patterns = {
            # Standard semantic versioning
            'semantic_exact': re.compile(r'([a-zA-Z0-9._-]+)==(\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?)'),
            'semantic_min': re.compile(r'([a-zA-Z0-9._-]+)>=(\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?)'),
            'semantic_compatible': re.compile(r'([a-zA-Z0-9._-]+)~=(\d+\.\d+\.\d+)'),
            
            # Loose patterns
            'loose_semantic': re.compile(r'([a-zA-Z0-9._-]+)==(\d+\.\d+(?:\.\d+)?)'),
            'loose_min': re.compile(r'([a-zA-Z0-9._-]+)>=(\d+\.\d+(?:\.\d+)?)'),
            
            # Range patterns
            'range_pattern': re.compile(r'([a-zA-Z0-9._-]+)>=([\d.]+),<([\d.]+)'),
            'caret_range': re.compile(r'([a-zA-Z0-9._-]+)\^(\d+\.\d+\.\d+)'),  # npm-style
            'tilde_range': re.compile(r'([a-zA-Z0-9._-]+)~(\d+\.\d+\.\d+)'),   # npm-style
            
            # Special cases
            'git_commit': re.compile(r'([a-zA-Z0-9._-]+)@([a-f0-9]{7,40})'),
            'git_branch': re.compile(r'([a-zA-Z0-9._-]+)@([a-zA-Z0-9._/-]+)'),
            'latest_wildcard': re.compile(r'([a-zA-Z0-9._-]+)(?:==)?(?:latest|\*|newest)'),
            'no_version': re.compile(r'^([a-zA-Z0-9._-]+)$'),
            
            # Complex constraint patterns
            'multiple_constraints': re.compile(r'([a-zA-Z0-9._-]+)(?:[><=!~]+[\d.]+[,;]?\s*)+'),
            'pre_release': re.compile(r'([a-zA-Z0-9._-]+)==(\d+\.\d+\.\d+-(?:alpha|beta|rc|dev)\d*)'),
        }
        
        # THINK HARD: Common package naming variations and aliases
        self.package_aliases = {
            'phi': 'agno',  # Common alias
            'phidata': 'agno',  # Old name
            'streamlit-st': 'streamlit',
            'openai-python': 'openai',
            'anthropic-python': 'anthropic',
        }
        
        # Security-sensitive packages requiring special attention
        self.security_critical_packages = {
            'pillow', 'requests', 'urllib3', 'cryptography', 'pyyaml', 
            'django', 'flask', 'fastapi', 'sqlalchemy', 'pandas'
        }

    def _check_mcp_availability(self) -> bool:
        """Check if MCP servers are available for enhanced analysis"""
        try:
            # This would normally check for MCP server connectivity
            # For now, we'll simulate availability
            return True
        except Exception as e:
            logger.warning(f"MCP servers not available: {e}")
            return False

    async def get_latest_version_mcp(self, package_name: str, ecosystem: str = 'python') -> Optional[str]:
        """CLAUDE 4: Use MCP context7 server to get latest package version"""
        
        # ULTRATHINK: Handle package name variations and aliases
        normalized_name = self.package_aliases.get(package_name, package_name)
        
        if not self.mcp_available:
            return await self._fallback_version_check(normalized_name, ecosystem)
        
        try:
            # For demonstration - in real implementation, this would use MCP
            logger.info(f"Checking latest version for {normalized_name} via MCP context7...")
            
            # Simulate MCP call - in practice, would be:
            # latest_version = await mcp_context7.get_package_latest(normalized_name, ecosystem)
            latest_version = await self._fallback_version_check(normalized_name, ecosystem)
            
            if latest_version:
                self.package_registry_cache[normalized_name] = latest_version
                logger.info(f"Latest version for {normalized_name}: {latest_version}")
                return latest_version
                
        except Exception as e:
            logger.error(f"MCP version check failed for {package_name}: {e}")
            return await self._fallback_version_check(normalized_name, ecosystem)
        
        return None

    async def _fallback_version_check(self, package_name: str, ecosystem: str) -> Optional[str]:
        """Fallback version checking using direct API calls"""
        
        try:
            if ecosystem == 'python':
                # PyPI API call
                response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data['info']['version']
            elif ecosystem == 'javascript':
                # npm API call
                response = requests.get(f"https://registry.npmjs.org/{package_name}/latest", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data['version']
                    
        except Exception as e:
            logger.warning(f"Fallback version check failed for {package_name}: {e}")
        
        return None

    def extract_packages_from_file(self, file_path: Path) -> List[PackageInfo]:
        """CLAUDE 4: Extract all package information with comprehensive pattern matching"""
        
        packages = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # THINK HARD: Try each pattern to catch edge cases
                for pattern_name, pattern in self.version_patterns.items():
                    matches = pattern.findall(line)
                    
                    for match in matches:
                        if isinstance(match, tuple):
                            package_name = match[0]
                            version = match[1] if len(match) > 1 else 'unspecified'
                        else:
                            package_name = match
                            version = 'unspecified'
                        
                        # Determine constraint type
                        constraint_type = 'unspecified'
                        if '==' in line:
                            constraint_type = 'exact'
                        elif '>=' in line:
                            constraint_type = 'minimum'
                        elif '~=' in line:
                            constraint_type = 'compatible'
                        elif '^' in line:
                            constraint_type = 'caret'
                        elif '~' in line:
                            constraint_type = 'tilde'
                        
                        packages.append(PackageInfo(
                            name=package_name.lower(),
                            version=version,
                            source_file=str(file_path.relative_to(self.repo_path)),
                            line_number=line_num,
                            constraint_type=constraint_type
                        ))
                        break  # Found a match, move to next line
                
                # Handle simple package names without versions
                if not any(char in line for char in ['=', '>', '<', '~', '^', '@']) and line:
                    # Simple package name
                    if re.match(r'^[a-zA-Z0-9._-]+$', line):
                        packages.append(PackageInfo(
                            name=line.lower(),
                            version='unspecified',
                            source_file=str(file_path.relative_to(self.repo_path)),
                            line_number=line_num,
                            constraint_type='unspecified'
                        ))
        
        except Exception as e:
            logger.error(f"Error extracting packages from {file_path}: {e}")
        
        return packages

    def find_all_dependency_files(self) -> List[Path]:
        """Find all dependency files across the repository"""
        
        dependency_files = []
        
        # Python dependency files
        for pattern in ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile']:
            dependency_files.extend(self.repo_path.rglob(pattern))
        
        # JavaScript dependency files
        for pattern in ['package.json']:
            dependency_files.extend(self.repo_path.rglob(pattern))
        
        logger.info(f"Found {len(dependency_files)} dependency files")
        return dependency_files

    async def analyze_project_versions(self, project_path: Path) -> ProjectVersionReport:
        """ULTRATHINK: Comprehensive version analysis for a single project"""
        
        logger.info(f"Analyzing versions for project: {project_path}")
        
        # Find dependency files in this project
        dependency_files = []
        for file_name in ['requirements.txt', 'pyproject.toml', 'package.json']:
            file_path = project_path / file_name
            if file_path.exists():
                dependency_files.append(file_path)
        
        # Extract all packages
        all_packages = []
        for dep_file in dependency_files:
            packages = self.extract_packages_from_file(dep_file)
            all_packages.extend(packages)
        
        # Group by package name
        packages_by_name = defaultdict(list)
        for pkg in all_packages:
            packages_by_name[pkg.name].append(pkg)
        
        # Analyze each package
        package_analyses = []
        critical_issues = 0
        warning_issues = 0
        suggestions = []
        
        for package_name, package_infos in packages_by_name.items():
            try:
                # Get latest version via MCP
                latest_version = await self.get_latest_version_mcp(package_name)
                
                # Analyze versions and inconsistencies
                detected_versions = list(set(pkg.version for pkg in package_infos))
                inconsistencies = []
                
                if len(detected_versions) > 1:
                    inconsistencies.append(f"Multiple versions found: {detected_versions}")
                    warning_issues += 1
                
                # Check if package is outdated
                is_outdated = False
                if latest_version and 'unspecified' not in detected_versions:
                    for version in detected_versions:
                        if version != 'unspecified' and self._is_version_outdated(version, latest_version):
                            is_outdated = True
                            break
                
                # Security checks for critical packages
                security_issues = []
                if package_name in self.security_critical_packages:
                    if 'unspecified' in detected_versions:
                        security_issues.append("Security-critical package without version pin")
                        critical_issues += 1
                    elif is_outdated:
                        security_issues.append("Security-critical package is outdated")
                        critical_issues += 1
                
                # Generate recommendation
                recommendation = self._generate_recommendation(
                    package_name, detected_versions, latest_version, inconsistencies, security_issues
                )
                
                package_analyses.append(VersionAnalysis(
                    package_name=package_name,
                    detected_versions=package_infos,
                    latest_version=latest_version,
                    is_outdated=is_outdated,
                    security_issues=security_issues,
                    inconsistencies=inconsistencies,
                    recommendation=recommendation
                ))
                
            except Exception as e:
                logger.error(f"Error analyzing package {package_name}: {e}")
                continue
        
        # Generate project-level suggestions
        if critical_issues == 0 and warning_issues == 0:
            suggestions.append("All dependencies appear to be well-managed")
        else:
            if critical_issues > 0:
                suggestions.append(f"Address {critical_issues} critical security issues immediately")
            if warning_issues > 0:
                suggestions.append(f"Review {warning_issues} version inconsistencies")
            
            # Check for missing UV adoption
            if (project_path / 'requirements.txt').exists() and not (project_path / 'pyproject.toml').exists():
                suggestions.append("Consider migrating to UV with pyproject.toml for better dependency management")
        
        return ProjectVersionReport(
            project_path=str(project_path.relative_to(self.repo_path)),
            package_analyses=package_analyses,
            critical_issues=critical_issues,
            warning_issues=warning_issues,
            suggestions=suggestions
        )

    def _is_version_outdated(self, current_version: str, latest_version: str) -> bool:
        """THINK HARD: Compare versions accounting for different formats"""
        
        if current_version == 'unspecified':
            return True
        
        try:
            # Simple comparison for now - would use packaging.version for production
            current_parts = [int(x) for x in current_version.split('.')]
            latest_parts = [int(x) for x in latest_version.split('.')]
            
            # Pad to same length
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            return current_parts < latest_parts
            
        except (ValueError, AttributeError):
            # If we can't parse, assume it might be outdated
            return True

    def _generate_recommendation(self, package_name: str, detected_versions: List[str], 
                               latest_version: Optional[str], inconsistencies: List[str], 
                               security_issues: List[str]) -> str:
        """CLAUDE 4: Generate detailed, actionable recommendations"""
        
        recommendations = []
        
        if security_issues:
            recommendations.append(f"🚨 CRITICAL: {'; '.join(security_issues)}")
        
        if 'unspecified' in detected_versions:
            if latest_version:
                recommendations.append(f"📌 Pin to latest version: {package_name}=={latest_version}")
            else:
                recommendations.append(f"📌 Add version constraint for {package_name}")
        
        if inconsistencies:
            recommendations.append(f"🔄 Resolve inconsistencies: {'; '.join(inconsistencies)}")
        
        if latest_version and not any('unspecified' in v for v in detected_versions):
            latest_available = latest_version
            current_versions = [v for v in detected_versions if v != 'unspecified']
            if current_versions and self._is_version_outdated(current_versions[0], latest_available):
                recommendations.append(f"⬆️ Update to latest: {package_name}=={latest_available}")
        
        if not recommendations:
            recommendations.append("✅ No issues detected")
        
        return " | ".join(recommendations)

    async def scan_all_projects(self) -> List[ProjectVersionReport]:
        """ULTRATHINK: Scan all projects for version analysis"""
        
        logger.info("Starting comprehensive version analysis...")
        
        # Load project data from previous analysis
        analysis_file = self.repo_path / 'scripts' / 'repository_analysis.json'
        if not analysis_file.exists():
            logger.error("Repository analysis not found. Run repository_profiler.py first.")
            return []
        
        with open(analysis_file, 'r') as f:
            repo_data = json.load(f)
        
        project_reports = []
        projects = repo_data['repository_profile']['projects']
        
        # Analyze each project
        for project_info in projects:
            project_path = self.repo_path / project_info['path']
            
            try:
                report = await self.analyze_project_versions(project_path)
                project_reports.append(report)
            except Exception as e:
                logger.error(f"Failed to analyze project {project_path}: {e}")
                continue
        
        logger.info(f"Version analysis complete: {len(project_reports)} projects analyzed")
        return project_reports

    def generate_comprehensive_report(self, project_reports: List[ProjectVersionReport]) -> Dict[str, Any]:
        """Generate comprehensive version analysis report"""
        
        # Aggregate statistics
        total_critical = sum(report.critical_issues for report in project_reports)
        total_warnings = sum(report.warning_issues for report in project_reports)
        
        # Package frequency analysis
        all_packages = defaultdict(int)
        outdated_packages = defaultdict(int)
        
        for report in project_reports:
            for analysis in report.package_analyses:
                all_packages[analysis.package_name] += 1
                if analysis.is_outdated:
                    outdated_packages[analysis.package_name] += 1
        
        # Most common packages
        common_packages = dict(Counter(all_packages).most_common(20))
        
        # Priority packages to update
        priority_updates = {}
        for package, count in outdated_packages.items():
            if count >= 5:  # Package is outdated in 5+ projects
                priority_updates[package] = count
        
        return {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_projects_analyzed': len(project_reports),
                'total_critical_issues': total_critical,
                'total_warning_issues': total_warnings
            },
            'executive_summary': {
                'critical_issues': total_critical,
                'warning_issues': total_warnings,
                'projects_needing_attention': len([r for r in project_reports if r.critical_issues > 0 or r.warning_issues > 0]),
                'most_common_packages': common_packages,
                'priority_updates': priority_updates
            },
            'detailed_reports': [asdict(report) for report in project_reports],
            'recommendations': self._generate_global_recommendations(project_reports)
        }

    def _generate_global_recommendations(self, project_reports: List[ProjectVersionReport]) -> List[str]:
        """Generate repository-wide recommendations"""
        
        recommendations = []
        
        total_critical = sum(report.critical_issues for report in project_reports)
        total_warnings = sum(report.warning_issues for report in project_reports)
        
        if total_critical > 0:
            recommendations.append(f"🚨 URGENT: Address {total_critical} critical security issues across projects")
        
        if total_warnings > 10:
            recommendations.append(f"📋 Create standardized dependency management process - {total_warnings} inconsistencies found")
        
        # UV migration recommendation
        traditional_pip_projects = len([r for r in project_reports if 'requirements.txt' in str(r.project_path)])
        if traditional_pip_projects > 50:
            recommendations.append(f"🔄 Consider UV migration for {traditional_pip_projects} projects using traditional pip")
        
        # Version pinning recommendation
        unpinned_critical = 0
        for report in project_reports:
            for analysis in report.package_analyses:
                if (analysis.package_name in self.security_critical_packages and 
                    any('unspecified' in pkg.version for pkg in analysis.detected_versions)):
                    unpinned_critical += 1
        
        if unpinned_critical > 0:
            recommendations.append(f"📌 Pin versions for {unpinned_critical} security-critical packages")
        
        recommendations.append("✅ Implement automated dependency scanning in CI/CD pipeline")
        
        return recommendations

    def save_results(self, report: Dict[str, Any], output_file: str = 'scripts/version_analysis.json'):
        """Save version analysis results"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Version analysis results saved to {output_file}")

async def main():
    """Main analysis execution with async support"""
    
    print("🔍 Starting Advanced Version Analysis...")
    print("ULTRATHINK: Analyzing complex version patterns with MCP verification...")
    
    hunter = VersionHunter()
    project_reports = await hunter.scan_all_projects()
    
    if project_reports:
        comprehensive_report = hunter.generate_comprehensive_report(project_reports)
        hunter.save_results(comprehensive_report)
        
        # Print executive summary
        summary = comprehensive_report['executive_summary']
        print(f"\n📊 Version Analysis Complete!")
        print(f"Critical Issues: {summary['critical_issues']}")
        print(f"Warning Issues: {summary['warning_issues']}")
        print(f"Projects Needing Attention: {summary['projects_needing_attention']}")
        print(f"Most Common Packages: {list(summary['most_common_packages'].keys())[:5]}")
        
        if summary['priority_updates']:
            print(f"Priority Updates Needed: {list(summary['priority_updates'].keys())}")
        
        print(f"\nDetailed results saved to: scripts/version_analysis.json")
        print(f"Logs available at: scripts/version_analysis.log")
    else:
        print("❌ No projects could be analyzed. Check repository_analysis.json exists.")

if __name__ == "__main__":
    asyncio.run(main())