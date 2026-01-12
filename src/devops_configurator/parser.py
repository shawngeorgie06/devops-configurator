"""
Requirements Parser for DevOps Pipeline Configurator.
Parses conversational input to extract project requirements.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ProjectRequirements:
    """Data class holding all parsed project requirements."""

    # Project basics
    project_name: str = "my-app"
    description: str = "Application deployed via CI/CD pipeline"
    repository_url: str = ""

    # Language/Framework
    language: str = "nodejs"  # nodejs, python, go, java
    framework: Optional[str] = None  # express, fastapi, django, flask, gin, spring
    language_version: str = "20"  # Node 20, Python 3.11, etc.

    # Package manager
    package_manager: str = "npm"  # npm, yarn, pnpm, pip, poetry

    # Deployment
    deployment_platform: str = "heroku"  # heroku, aws, gcp, azure
    environments: List[str] = field(default_factory=lambda: ["production"])

    # Testing
    has_unit_tests: bool = True
    has_integration_tests: bool = False
    has_e2e_tests: bool = False
    test_framework: Optional[str] = None  # jest, pytest, mocha, etc.

    # Services/Databases
    databases: List[str] = field(default_factory=list)  # postgresql, mysql, mongodb, redis
    services: List[str] = field(default_factory=list)  # redis, elasticsearch, etc.

    # Build configuration
    build_command: str = ""
    start_command: str = ""
    test_command: str = ""
    lint_command: str = ""

    # Port
    port: int = 3000

    # Docker
    use_docker: bool = False

    # Main branch
    main_branch: str = "main"

    # Additional features
    needs_preview_deployments: bool = False
    needs_notifications: bool = False


class RequirementsParser:
    """Parses conversational input to extract project requirements."""

    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'nodejs': [
            r'\bnode\.?js\b', r'\bnode\b', r'\bjavascript\b', r'\bjs\b',
            r'\btypescript\b', r'\bts\b', r'\bnpm\b', r'\byarn\b',
            r'\bexpress\b', r'\bnext\.?js\b', r'\bnest\.?js\b', r'\breact\b',
        ],
        'python': [
            r'\bpython\b', r'\bpy\b', r'\bdjango\b', r'\bflask\b',
            r'\bfastapi\b', r'\bpip\b', r'\bpoetry\b', r'\bpytest\b',
        ],
        'go': [
            r'\bgolang\b', r'\bgo\b(?!\s+to)', r'\bgin\b', r'\becho\b',
        ],
        'java': [
            r'\bjava\b', r'\bspring\b', r'\bmaven\b', r'\bgradle\b',
            r'\bspring\s*boot\b',
        ],
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'express': [r'\bexpress\b', r'\bexpress\.?js\b'],
        'nextjs': [r'\bnext\.?js\b', r'\bnext\b'],
        'nestjs': [r'\bnest\.?js\b', r'\bnest\b'],
        'react': [r'\breact\b', r'\bcreate.react.app\b'],
        'django': [r'\bdjango\b'],
        'flask': [r'\bflask\b'],
        'fastapi': [r'\bfastapi\b', r'\bfast\s*api\b'],
        'gin': [r'\bgin\b'],
        'spring': [r'\bspring\b', r'\bspring\s*boot\b'],
    }

    # Platform detection patterns
    PLATFORM_PATTERNS = {
        'heroku': [r'\bheroku\b'],
        'aws': [r'\baws\b', r'\bamazon\b', r'\bec2\b', r'\becs\b', r'\blambda\b', r'\bs3\b'],
        'gcp': [r'\bgcp\b', r'\bgoogle\s*cloud\b', r'\bcloud\s*run\b', r'\bgke\b'],
        'azure': [r'\bazure\b', r'\bmicrosoft\b', r'\baks\b'],
    }

    # Database detection patterns
    DATABASE_PATTERNS = {
        'postgresql': [r'\bpostgres\b', r'\bpostgresql\b', r'\bpg\b'],
        'mysql': [r'\bmysql\b', r'\bmariadb\b'],
        'mongodb': [r'\bmongo\b', r'\bmongodb\b'],
        'redis': [r'\bredis\b'],
        'sqlite': [r'\bsqlite\b'],
        'elasticsearch': [r'\belastic\b', r'\belasticsearch\b'],
    }

    # Environment detection patterns
    ENVIRONMENT_PATTERNS = {
        'staging': [r'\bstaging\b', r'\bstage\b'],
        'production': [r'\bprod\b', r'\bproduction\b'],
        'preview': [r'\bpreview\b', r'\bpr\s*deploy\b'],
        'development': [r'\bdev\b', r'\bdevelopment\b'],
    }

    # Test type patterns
    TEST_PATTERNS = {
        'unit': [r'\bunit\s*test', r'\bunit\b'],
        'integration': [r'\bintegration\s*test', r'\bintegration\b'],
        'e2e': [r'\be2e\b', r'\bend.to.end\b', r'\bend\s*to\s*end\b', r'\bcypress\b', r'\bplaywright\b'],
    }

    def __init__(self):
        self.requirements = ProjectRequirements()

    def parse(self, user_input: str) -> ProjectRequirements:
        """Parse user input and extract requirements."""
        text = user_input.lower()

        # Detect language
        self._detect_language(text)

        # Detect framework
        self._detect_framework(text)

        # Detect deployment platform
        self._detect_platform(text)

        # Detect databases and services
        self._detect_databases(text)

        # Detect environments
        self._detect_environments(text)

        # Detect testing requirements
        self._detect_tests(text)

        # Detect Docker usage
        self._detect_docker(text)

        # Detect preview deployments
        self._detect_preview(text)

        # Extract project name if mentioned
        self._extract_project_name(user_input)

        # Set sensible defaults based on detected language/framework
        self._set_defaults()

        return self.requirements

    def _detect_language(self, text: str) -> None:
        """Detect programming language from text."""
        for language, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    self.requirements.language = language
                    return

    def _detect_framework(self, text: str) -> None:
        """Detect framework from text."""
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    self.requirements.framework = framework
                    return

    def _detect_platform(self, text: str) -> None:
        """Detect deployment platform from text."""
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    self.requirements.deployment_platform = platform
                    return

    def _detect_databases(self, text: str) -> None:
        """Detect databases and services from text."""
        databases = []
        for db, patterns in self.DATABASE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if db == 'redis':
                        if 'redis' not in self.requirements.services:
                            self.requirements.services.append('redis')
                    elif db == 'elasticsearch':
                        if 'elasticsearch' not in self.requirements.services:
                            self.requirements.services.append('elasticsearch')
                    else:
                        if db not in databases:
                            databases.append(db)
                    break
        self.requirements.databases = databases

    def _detect_environments(self, text: str) -> None:
        """Detect deployment environments from text."""
        environments = []
        for env, patterns in self.ENVIRONMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if env not in environments:
                        environments.append(env)
                    break

        # Always ensure production is included if any environment is mentioned
        if environments:
            if 'production' not in environments:
                environments.append('production')
            self.requirements.environments = environments
        else:
            self.requirements.environments = ['production']

    def _detect_tests(self, text: str) -> None:
        """Detect testing requirements from text."""
        # Check for explicit test mentions
        for test_type, patterns in self.TEST_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if test_type == 'unit':
                        self.requirements.has_unit_tests = True
                    elif test_type == 'integration':
                        self.requirements.has_integration_tests = True
                    elif test_type == 'e2e':
                        self.requirements.has_e2e_tests = True

        # Generic test mention
        if re.search(r'\btest', text, re.IGNORECASE):
            self.requirements.has_unit_tests = True

    def _detect_docker(self, text: str) -> None:
        """Detect if Docker is needed."""
        if re.search(r'\bdocker\b|\bcontainer\b', text, re.IGNORECASE):
            self.requirements.use_docker = True
        # AWS and GCP usually need Docker for container deployments
        if self.requirements.deployment_platform in ['aws', 'gcp']:
            self.requirements.use_docker = True

    def _detect_preview(self, text: str) -> None:
        """Detect if preview deployments are needed."""
        if re.search(r'\bpreview\b|\bpr\s*deploy', text, re.IGNORECASE):
            self.requirements.needs_preview_deployments = True

    def _extract_project_name(self, text: str) -> None:
        """Try to extract project name from text."""
        # Words that should not be extracted as project names
        stop_words = {
            'i', 'a', 'an', 'the', 'my', 'our', 'this', 'that',
            'to', 'want', 'need', 'have', 'will', 'would', 'should',
            'node', 'nodejs', 'python', 'express', 'django', 'flask', 'fastapi',
            'heroku', 'aws', 'gcp', 'azure', 'docker',
            'unit', 'test', 'tests', 'staging', 'production', 'deploy', 'deployment',
            'with', 'and', 'or', 'for', 'using', 'on',
        }

        # Look for common patterns like "my X app", "called X", "named X"
        patterns = [
            r'(?:called|named)\s+["\']?(\w+(?:-\w+)*)["\']?',
            r'project\s+["\']?(\w+(?:-\w+)*)["\']?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).lower()
                if name not in stop_words and len(name) > 1:
                    self.requirements.project_name = name
                    return

        # If no project name found, keep the default "my-app"

    def _set_defaults(self) -> None:
        """Set sensible defaults based on detected configuration."""
        lang = self.requirements.language
        framework = self.requirements.framework

        if lang == 'nodejs':
            self.requirements.language_version = '20'
            self.requirements.port = 3000
            self.requirements.package_manager = 'npm'
            self.requirements.build_command = 'npm run build'
            self.requirements.test_command = 'npm test'
            self.requirements.lint_command = 'npm run lint'

            if framework == 'express':
                self.requirements.start_command = 'node server.js'
            elif framework == 'nextjs':
                self.requirements.start_command = 'npm start'
                self.requirements.build_command = 'npm run build'
            elif framework == 'nestjs':
                self.requirements.start_command = 'node dist/main.js'
            else:
                self.requirements.start_command = 'npm start'

        elif lang == 'python':
            self.requirements.language_version = '3.11'
            self.requirements.port = 8000
            self.requirements.package_manager = 'pip'
            self.requirements.test_command = 'pytest'
            self.requirements.lint_command = 'flake8 . || ruff check .'

            if framework == 'django':
                self.requirements.start_command = 'gunicorn myproject.wsgi:application'
            elif framework == 'flask':
                self.requirements.start_command = 'gunicorn app:app'
            elif framework == 'fastapi':
                self.requirements.start_command = 'uvicorn main:app --host 0.0.0.0 --port $PORT'
            else:
                self.requirements.start_command = 'python app.py'

        elif lang == 'go':
            self.requirements.language_version = '1.21'
            self.requirements.port = 8080
            self.requirements.build_command = 'go build -o app .'
            self.requirements.test_command = 'go test ./...'
            self.requirements.start_command = './app'

        elif lang == 'java':
            self.requirements.language_version = '17'
            self.requirements.port = 8080
            self.requirements.build_command = './mvnw package -DskipTests'
            self.requirements.test_command = './mvnw test'
            self.requirements.start_command = 'java -jar target/*.jar'


def parse_requirements(user_input: str) -> ProjectRequirements:
    """Convenience function to parse requirements from user input."""
    parser = RequirementsParser()
    return parser.parse(user_input)


def get_missing_info(requirements: ProjectRequirements) -> List[Dict[str, Any]]:
    """Identify what information is missing and return questions to ask."""
    questions = []

    # Check if language is generic/unclear
    if requirements.language == 'nodejs' and not requirements.framework:
        questions.append({
            'id': 'framework',
            'question': 'What Node.js framework are you using?',
            'options': ['Express', 'Next.js', 'NestJS', 'Other/None'],
            'current': requirements.framework,
        })

    if requirements.language == 'python' and not requirements.framework:
        questions.append({
            'id': 'framework',
            'question': 'What Python framework are you using?',
            'options': ['Django', 'Flask', 'FastAPI', 'Other/None'],
            'current': requirements.framework,
        })

    # Check if deployment platform needs clarification
    if not requirements.deployment_platform:
        questions.append({
            'id': 'platform',
            'question': 'Where would you like to deploy your application?',
            'options': ['Heroku', 'AWS', 'Google Cloud (GCP)', 'Azure'],
            'current': None,
        })

    return questions
