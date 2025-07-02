#!/usr/bin/env python3
"""
Advanced Repository Profiler with MCP Integration
CLAUDE 4 ENHANCED: Comprehensive repository analysis with edge case handling

This script provides deep analysis of the awesome-llm-apps repository structure,
dependencies, documentation patterns, and complexity indicators.
"""

import os
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/repository_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProjectInfo:
    """Comprehensive project information structure"""
    path: str
    name: str
    language: str
    framework: str
    package_manager: str
    dependencies: Dict[str, List[str]]
    version_info: Dict[str, str]
    readme_path: Optional[str]
    complexity_score: int
    special_features: List[str]
    documentation_files: List[str]

@dataclass 
class RepositoryProfile:
    """Complete repository analysis results"""
    total_projects: int
    language_distribution: Dict[str, int]
    framework_distribution: Dict[str, int]
    package_manager_distribution: Dict[str, int]
    projects: List[ProjectInfo]
    dependency_conflicts: List[Dict[str, Any]]
    documentation_inconsistencies: List[Dict[str, Any]]
    complexity_indicators: Dict[str, Any]

class RepositoryProfiler:
    """CLAUDE 4 ENHANCED: Comprehensive repository analysis with ULTRATHINK"""
    
    def __init__(self, repo_path: str = "/home/sistr/krljakob/awesome-llm-apps"):
        self.repo_path = Path(repo_path)
        self.profile = RepositoryProfile(
            total_projects=0,
            language_distribution={},
            framework_distribution={},
            package_manager_distribution={},
            projects=[],
            dependency_conflicts=[],
            documentation_inconsistencies=[],
            complexity_indicators={}
        )
        
        # THINK HARD: What file patterns indicate different ecosystems?
        self.ecosystem_indicators = {
            'python': {
                'files': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile', 'poetry.lock', 'uv.lock'],
                'patterns': [r'\.py$', r'__init__\.py', r'__pycache__'],
                'frameworks': {
                    'streamlit': ['streamlit', 'st.'],
                    'fastapi': ['fastapi', 'uvicorn'], 
                    'django': ['django', 'manage.py'],
                    'flask': ['flask', 'app.py'],
                    'agno': ['agno', 'phi']
                }
            },
            'javascript': {
                'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb'],
                'patterns': [r'\.js$', r'\.jsx$', r'node_modules'],
                'frameworks': {
                    'nextjs': ['next.config', 'next/'],
                    'react': ['react', 'jsx'],
                    'vue': ['vue', '.vue'],
                    'svelte': ['svelte']
                }
            },
            'typescript': {
                'files': ['tsconfig.json', 'types.d.ts'],
                'patterns': [r'\.ts$', r'\.tsx$'],
                'frameworks': {
                    'nextjs': ['next.config.ts', 'next/'],
                    'react': ['react', 'tsx']
                }
            }
        }
        
        # ULTRATHINK: Complex version patterns that might exist
        self.version_patterns = {
            'semantic': re.compile(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?'),
            'loose_semantic': re.compile(r'\d+\.\d+(?:\.\d+)?'),
            'date_based': re.compile(r'\d{4}\.\d{1,2}\.\d{1,2}'),
            'git_hash': re.compile(r'[a-f0-9]{7,40}'),
            'pre_release': re.compile(r'\d+\.\d+\.\d+-(?:alpha|beta|rc|dev)\d*'),
            'caret_range': re.compile(r'\^\d+\.\d+\.\d+'),
            'tilde_range': re.compile(r'~\d+\.\d+\.\d+'),
            'latest': re.compile(r'latest|newest|\*'),
        }

    def analyze_ecosystem(self, project_path: Path) -> Tuple[str, str, str]:
        """CLAUDE 4: Detect language, framework, and package manager with edge cases"""
        
        logger.info(f"Analyzing ecosystem for {project_path}")
        
        detected_languages = []
        detected_frameworks = []
        detected_package_managers = []
        
        # Check for ecosystem indicator files
        for lang, indicators in self.ecosystem_indicators.items():
            for file_indicator in indicators['files']:
                if (project_path / file_indicator).exists():
                    detected_languages.append(lang)
                    
                    # Detect package manager from specific files
                    if file_indicator in ['requirements.txt', 'pyproject.toml']:
                        if (project_path / 'uv.lock').exists():
                            detected_package_managers.append('uv')
                        elif (project_path / 'poetry.lock').exists():
                            detected_package_managers.append('poetry')
                        else:
                            detected_package_managers.append('pip')
                    elif file_indicator == 'package.json':
                        if (project_path / 'pnpm-lock.yaml').exists():
                            detected_package_managers.append('pnpm')
                        elif (project_path / 'bun.lockb').exists():
                            detected_package_managers.append('bun')
                        elif (project_path / 'yarn.lock').exists():
                            detected_package_managers.append('yarn')
                        else:
                            detected_package_managers.append('npm')
        
        # Analyze file contents for framework detection
        try:
            for file_path in project_path.rglob('*.py'):
                if file_path.is_file() and file_path.stat().st_size < 1024*1024:  # Skip large files
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for lang, indicators in self.ecosystem_indicators.items():
                        if lang == 'python':
                            for framework, patterns in indicators['frameworks'].items():
                                if any(pattern in content for pattern in patterns):
                                    detected_frameworks.append(framework)
        except Exception as e:
            logger.warning(f"Error analyzing files in {project_path}: {e}")
        
        # THINK HARD: How to handle multiple detections?
        primary_language = detected_languages[0] if detected_languages else 'unknown'
        primary_framework = detected_frameworks[0] if detected_frameworks else 'unknown'
        primary_package_manager = detected_package_managers[0] if detected_package_managers else 'unknown'
        
        return primary_language, primary_framework, primary_package_manager

    def extract_dependencies(self, project_path: Path, language: str, package_manager: str) -> Dict[str, List[str]]:
        """CLAUDE 4: Parse ALL package files with comprehensive version extraction"""
        
        dependencies = defaultdict(list)
        
        try:
            if language == 'python':
                # Handle requirements.txt
                req_file = project_path / 'requirements.txt'
                if req_file.exists():
                    content = req_file.read_text(encoding='utf-8', errors='ignore')
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # THINK HARD: Handle complex pip requirement formats
                            match = re.match(r'([a-zA-Z0-9._-]+)([><=!~]+.+)?', line)
                            if match:
                                package, version = match.groups()
                                dependencies['production'].append(f"{package}:{version or 'unspecified'}")
                
                # Handle pyproject.toml
                pyproject_file = project_path / 'pyproject.toml'
                if pyproject_file.exists():
                    # Would need tomli/tomllib for proper parsing, simplified for now
                    content = pyproject_file.read_text(encoding='utf-8', errors='ignore')
                    dependencies['pyproject'] = [f"pyproject.toml detected: {len(content.split('dependencies'))} dependency sections"]
                
            elif language in ['javascript', 'typescript']:
                # Handle package.json
                package_file = project_path / 'package.json'
                if package_file.exists():
                    try:
                        package_data = json.loads(package_file.read_text(encoding='utf-8'))
                        
                        for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                            if dep_type in package_data:
                                for pkg, version in package_data[dep_type].items():
                                    dependencies[dep_type].append(f"{pkg}:{version}")
                                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in {package_file}: {e}")
                        dependencies['error'] = [f"JSON parsing error: {e}"]
        
        except Exception as e:
            logger.error(f"Error extracting dependencies from {project_path}: {e}")
            dependencies['extraction_error'] = [str(e)]
        
        return dict(dependencies)

    def calculate_complexity_score(self, project_path: Path, dependencies: Dict[str, List[str]]) -> Tuple[int, List[str]]:
        """CLAUDE 4: Multi-dimensional complexity assessment"""
        
        score = 0
        features = []
        
        # File count complexity
        try:
            py_files = list(project_path.rglob('*.py'))
            js_files = list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
            
            total_files = len(py_files) + len(js_files)
            if total_files > 20:
                score += 3 
                features.append(f"large_codebase_{total_files}_files")
            elif total_files > 5:
                score += 1
                features.append(f"medium_codebase_{total_files}_files")
        except Exception:
            pass
        
        # Dependency complexity
        total_deps = sum(len(deps) for deps in dependencies.values())
        if total_deps > 20:
            score += 3
            features.append(f"heavy_dependencies_{total_deps}")
        elif total_deps > 10:
            score += 1
            features.append(f"moderate_dependencies_{total_deps}")
        
        # Multi-technology complexity
        if (project_path / 'package.json').exists() and (project_path / 'requirements.txt').exists():
            score += 2
            features.append("multi_language_project")
        
        # Special architecture patterns
        if (project_path / 'docker-compose.yml').exists() or (project_path / 'Dockerfile').exists():
            score += 1
            features.append("containerized")
            
        if any(dir_name in str(project_path) for dir_name in ['multi_agent', 'team', 'microservice']):
            score += 2
            features.append("multi_agent_architecture")
        
        # Database/Vector store complexity
        for file_path in project_path.rglob('*.py'):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')[:5000]  # Sample
                    if any(db in content for db in ['lancedb', 'pinecone', 'weaviate', 'chroma', 'pgvector']):
                        score += 1
                        features.append("vector_database")
                        break
                except Exception:
                    pass
        
        return score, features

    def find_documentation_files(self, project_path: Path) -> List[str]:
        """Find all documentation files with comprehensive patterns"""
        
        doc_patterns = ['README*', '*.md', 'docs/', 'documentation/', 'guides/', 'tutorial*']
        doc_files = []
        
        for pattern in doc_patterns:
            try:
                if '*' in pattern:
                    doc_files.extend([str(f.relative_to(project_path)) for f in project_path.glob(pattern)])
                else:
                    path = project_path / pattern
                    if path.exists():
                        if path.is_dir():
                            doc_files.extend([str(f.relative_to(project_path)) for f in path.rglob('*') if f.is_file()])
                        else:
                            doc_files.append(str(path.relative_to(project_path)))
            except Exception as e:
                logger.warning(f"Error finding docs in {project_path} with pattern {pattern}: {e}")
        
        return doc_files

    def scan_repository(self) -> None:
        """ULTRATHINK: Comprehensive repository scanning with intelligent filtering"""
        
        logger.info(f"Starting comprehensive repository scan of {self.repo_path}")
        
        # THINK HARD: What directories should we exclude?
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.next', 'dist', 'build', 
            '.venv', 'venv', '.env', 'logs', 'temp', 'tmp'
        }
        
        project_directories = []
        
        # Find all project directories (those with key indicator files)
        for root, dirs, files in os.walk(self.repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            root_path = Path(root)
            
            # Check if this directory contains project indicators
            has_project_files = any(
                indicator in files 
                for ecosystem in self.ecosystem_indicators.values()
                for indicator in ecosystem['files']
            )
            
            if has_project_files:
                project_directories.append(root_path)
        
        logger.info(f"Found {len(project_directories)} potential project directories")
        
        # Analyze each project
        for project_path in project_directories:
            try:
                logger.info(f"Analyzing project: {project_path}")
                
                # Basic project info
                project_name = project_path.name
                relative_path = str(project_path.relative_to(self.repo_path))
                
                # Ecosystem detection
                language, framework, package_manager = self.analyze_ecosystem(project_path)
                
                # Dependency extraction
                dependencies = self.extract_dependencies(project_path, language, package_manager)
                
                # Complexity analysis
                complexity_score, special_features = self.calculate_complexity_score(project_path, dependencies)
                
                # Documentation discovery
                doc_files = self.find_documentation_files(project_path)
                
                # Find README
                readme_path = None
                for doc_file in doc_files:
                    if 'readme' in doc_file.lower():
                        readme_path = doc_file
                        break
                
                # Create project info
                project_info = ProjectInfo(
                    path=relative_path,
                    name=project_name,
                    language=language,
                    framework=framework,
                    package_manager=package_manager,
                    dependencies=dependencies,
                    version_info={},  # Will be populated in version analysis
                    readme_path=readme_path,
                    complexity_score=complexity_score,
                    special_features=special_features,
                    documentation_files=doc_files
                )
                
                self.profile.projects.append(project_info)
                
            except Exception as e:
                logger.error(f"Error analyzing project {project_path}: {e}")
        
        # Update profile statistics
        self.profile.total_projects = len(self.profile.projects)
        
        # Calculate distributions - convert Counter to dict for JSON serialization
        self.profile.language_distribution = dict(Counter(p.language for p in self.profile.projects))
        self.profile.framework_distribution = dict(Counter(p.framework for p in self.profile.projects))  
        self.profile.package_manager_distribution = dict(Counter(p.package_manager for p in self.profile.projects))
        
        # Complexity indicators
        self.profile.complexity_indicators = {
            'high_complexity_projects': len([p for p in self.profile.projects if p.complexity_score >= 5]),
            'multi_language_projects': len([p for p in self.profile.projects if 'multi_language_project' in p.special_features]),
            'containerized_projects': len([p for p in self.profile.projects if 'containerized' in p.special_features]),
            'average_complexity': sum(p.complexity_score for p in self.profile.projects) / len(self.profile.projects) if self.profile.projects else 0
        }
        
        logger.info(f"Repository analysis complete: {self.profile.total_projects} projects analyzed")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        
        return {
            'repository_profile': asdict(self.profile),
            'analysis_metadata': {
                'timestamp': str(Path('scripts/repository_analysis.log').stat().st_mtime),
                'analyzer_version': '1.0.0',
                'total_files_analyzed': sum(len(p.documentation_files) for p in self.profile.projects)
            }
        }

    def save_results(self, output_file: str = 'scripts/repository_analysis.json') -> None:
        """Save analysis results to JSON file"""
        
        report = self.generate_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis results saved to {output_file}")

def main():
    """Main analysis execution"""
    
    print("🔍 Starting Comprehensive Repository Analysis...")
    print("THINK HARD: Analyzing complex multi-framework repository structure...")
    
    profiler = RepositoryProfiler()
    profiler.scan_repository()
    profiler.save_results()
    
    # Print summary
    profile = profiler.profile
    print(f"\n📊 Analysis Complete!")
    print(f"Total Projects: {profile.total_projects}")
    print(f"Languages: {dict(profile.language_distribution)}")
    print(f"Frameworks: {dict(profile.framework_distribution)}")
    print(f"Package Managers: {dict(profile.package_manager_distribution)}")
    print(f"High Complexity Projects: {profile.complexity_indicators['high_complexity_projects']}")
    print(f"Average Complexity Score: {profile.complexity_indicators['average_complexity']:.2f}")
    
    print(f"\nDetailed results saved to: scripts/repository_analysis.json")
    print(f"Logs available at: scripts/repository_analysis.log")

if __name__ == "__main__":
    main()