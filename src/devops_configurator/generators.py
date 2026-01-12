"""
Configuration Generators for DevOps Pipeline Configurator.
Generates GitHub Actions workflows, Heroku configs, Docker files, and documentation.
"""

import json
from typing import Dict, List, Optional
from .parser import ProjectRequirements
from . import templates


class GitHubActionsGenerator:
    """Generates GitHub Actions workflow files."""

    def __init__(self, requirements: ProjectRequirements):
        self.req = requirements

    def generate(self) -> Dict[str, str]:
        """Generate all GitHub Actions workflow files."""
        files = {}

        # Main CI/CD workflow
        files['.github/workflows/ci-cd.yml'] = self._generate_main_workflow()

        return files

    def _generate_main_workflow(self) -> str:
        """Generate the main CI/CD workflow."""
        if self.req.language == 'nodejs':
            return self._generate_nodejs_workflow()
        elif self.req.language == 'python':
            return self._generate_python_workflow()
        else:
            # Default to Node.js style
            return self._generate_nodejs_workflow()

    def _generate_nodejs_workflow(self) -> str:
        """Generate Node.js GitHub Actions workflow."""
        # Determine branches
        push_branches = self.req.main_branch
        pr_branches = self.req.main_branch

        # Build services block
        services_block = self._build_services_block()

        # Build deploy jobs
        deploy_jobs = self._build_deploy_jobs()

        # Build test env vars
        test_env_vars = self._build_test_env_vars()

        # Determine commands
        pm = self.req.package_manager
        if pm == 'yarn':
            install_cmd = 'yarn install --frozen-lockfile'
        elif pm == 'pnpm':
            install_cmd = 'pnpm install --frozen-lockfile'
        else:
            install_cmd = 'npm ci'

        workflow = templates.GITHUB_ACTIONS_NODEJS.format(
            workflow_name='CI/CD Pipeline',
            push_branches=push_branches,
            pr_branches=pr_branches,
            node_version=self.req.language_version,
            package_manager=pm,
            install_command=install_cmd,
            lint_command=self.req.lint_command or 'npm run lint',
            test_command=self.req.test_command or 'npm test',
            test_env_vars=test_env_vars,
            build_command=self.req.build_command or 'npm run build',
            build_output_path='dist/',
            services_block=services_block,
            deploy_jobs=deploy_jobs,
        )

        return workflow

    def _generate_python_workflow(self) -> str:
        """Generate Python GitHub Actions workflow."""
        push_branches = self.req.main_branch
        pr_branches = self.req.main_branch

        services_block = self._build_services_block()
        deploy_jobs = self._build_deploy_jobs()
        test_env_vars = self._build_test_env_vars()

        # Determine install command
        if self.req.package_manager == 'poetry':
            install_cmd = 'pip install poetry && poetry install'
        else:
            install_cmd = 'pip install -r requirements.txt'

        # Determine main module for import check
        main_module = self.req.framework or 'app'

        workflow = templates.GITHUB_ACTIONS_PYTHON.format(
            workflow_name='CI/CD Pipeline',
            push_branches=push_branches,
            pr_branches=pr_branches,
            python_version=self.req.language_version,
            install_command=install_cmd,
            lint_command=self.req.lint_command or 'flake8 . --count --show-source --statistics',
            test_command=self.req.test_command or 'pytest --cov=. --cov-report=xml',
            test_env_vars=test_env_vars,
            coverage_path='coverage.xml',
            main_module=main_module,
            services_block=services_block,
            deploy_jobs=deploy_jobs,
        )

        return workflow

    def _build_services_block(self) -> str:
        """Build the services block for databases/cache."""
        if not self.req.databases and 'redis' not in self.req.services:
            return ''

        services = []

        for db in self.req.databases:
            if db == 'postgresql':
                services.append(templates.POSTGRES_SERVICE)
            elif db == 'mysql':
                services.append(templates.MYSQL_SERVICE)
            elif db == 'mongodb':
                services.append(templates.MONGODB_SERVICE)

        if 'redis' in self.req.services:
            services.append(templates.REDIS_SERVICE)

        if services:
            # Build the services block with proper indentation
            # The {services_block} is inserted at 4-space indent in the template
            # services: is at 4 spaces, service names at 6, properties at 8
            lines = ['services:']
            for service in services:
                for line in service.split('\n'):
                    # Add 4 spaces to each line (to account for template position)
                    lines.append('    ' + line)
            return '\n'.join(lines)

        return ''

    def _build_test_env_vars(self) -> str:
        """Build environment variables for test job."""
        env_vars = []

        for db in self.req.databases:
            if db == 'postgresql':
                env_vars.append('DATABASE_URL: postgresql://test:test@localhost:5432/test_db')
            elif db == 'mysql':
                env_vars.append('DATABASE_URL: mysql://root:test@localhost:3306/test_db')
            elif db == 'mongodb':
                env_vars.append('MONGODB_URI: mongodb://localhost:27017/test_db')

        if 'redis' in self.req.services:
            env_vars.append('REDIS_URL: redis://localhost:6379')

        return '\n          '.join(env_vars)

    def _build_deploy_jobs(self) -> str:
        """Build deployment jobs for each environment."""
        deploy_jobs = []

        platform = self.req.deployment_platform

        for i, env in enumerate(self.req.environments):
            # Determine dependencies
            if i == 0:
                needs = 'build'
            else:
                needs = f'deploy-{self.req.environments[i-1]}'

            # Environment block (for production, require approval)
            if env == 'production':
                env_block = f'''environment:
      name: {env}
      url: ${{{{ secrets.PRODUCTION_URL }}}}'''
            elif env == 'staging':
                env_block = f'''environment:
      name: {env}
      url: ${{{{ secrets.STAGING_URL }}}}'''
            else:
                env_block = ''

            if platform == 'heroku':
                job = templates.HEROKU_DEPLOY_JOB.format(
                    environment=env,
                    environment_title=env.title(),
                    environment_upper=env.upper(),
                    needs=needs,
                    environment_block=env_block,
                    heroku_extra_options='',
                )
            elif platform == 'aws':
                job = templates.AWS_DEPLOY_JOB.format(
                    environment=env,
                    environment_title=env.title(),
                    environment_upper=env.upper(),
                    needs=needs,
                    environment_block=env_block,
                    ecr_repository=self.req.project_name,
                    cluster_name=f'{self.req.project_name}-cluster',
                    service_name=self.req.project_name,
                )
            elif platform == 'gcp':
                job = templates.GCP_DEPLOY_JOB.format(
                    environment=env,
                    environment_title=env.title(),
                    environment_upper=env.upper(),
                    needs=needs,
                    environment_block=env_block,
                    service_name=self.req.project_name,
                )
            elif platform == 'azure':
                job = templates.AZURE_DEPLOY_JOB.format(
                    environment=env,
                    environment_title=env.title(),
                    environment_upper=env.upper(),
                    needs=needs,
                    environment_block=env_block,
                    app_name=self.req.project_name,
                )
            else:
                continue

            deploy_jobs.append(job)

        return '\n'.join(deploy_jobs)


class HerokuGenerator:
    """Generates Heroku configuration files."""

    def __init__(self, requirements: ProjectRequirements):
        self.req = requirements

    def generate(self) -> Dict[str, str]:
        """Generate all Heroku configuration files."""
        if self.req.deployment_platform != 'heroku':
            return {}

        files = {}

        # Procfile
        files['Procfile'] = self._generate_procfile()

        # app.json
        files['app.json'] = self._generate_app_json()

        return files

    def _generate_procfile(self) -> str:
        """Generate Heroku Procfile."""
        start_cmd = self.req.start_command

        if self.req.language == 'nodejs':
            return templates.PROCFILE_WEB_NODEJS.format(start_command=start_cmd)
        elif self.req.language == 'python':
            return templates.PROCFILE_WEB_PYTHON.format(start_command=start_cmd)
        else:
            return f'web: {start_cmd}\n'

    def _generate_app_json(self) -> str:
        """Generate Heroku app.json."""
        # Build addons list
        addons = []
        for db in self.req.databases:
            if db == 'postgresql':
                addons.append('heroku-postgresql:mini')
            elif db == 'mysql':
                addons.append('jawsdb:kitefin')
        if 'redis' in self.req.services:
            addons.append('heroku-redis:mini')

        # Build buildpacks
        if self.req.language == 'nodejs':
            buildpacks = [{'url': 'heroku/nodejs'}]
        elif self.req.language == 'python':
            buildpacks = [{'url': 'heroku/python'}]
        else:
            buildpacks = []

        # Build env vars
        env_vars = {
            'NODE_ENV': {'value': 'production'} if self.req.language == 'nodejs' else None,
        }
        env_vars = {k: v for k, v in env_vars.items() if v is not None}

        return templates.HEROKU_APP_JSON.format(
            app_name=self.req.project_name,
            description=self.req.description,
            repository_url=self.req.repository_url or 'https://github.com/username/repo',
            keywords=json.dumps(['ci-cd', self.req.language]),
            env_vars=json.dumps(env_vars, indent=4),
            addons=json.dumps(addons),
            buildpacks=json.dumps(buildpacks),
            test_command=self.req.test_command,
        )


class DockerGenerator:
    """Generates Docker configuration files."""

    def __init__(self, requirements: ProjectRequirements):
        self.req = requirements

    def generate(self) -> Dict[str, str]:
        """Generate Docker configuration files."""
        if not self.req.use_docker:
            return {}

        files = {}

        # Dockerfile
        files['Dockerfile'] = self._generate_dockerfile()

        # .dockerignore
        files['.dockerignore'] = templates.DOCKERIGNORE

        return files

    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile based on language."""
        if self.req.language == 'nodejs':
            pm = self.req.package_manager
            if pm == 'yarn':
                install_cmd = 'yarn install --frozen-lockfile'
                prod_install = 'yarn install --production --frozen-lockfile'
            elif pm == 'pnpm':
                install_cmd = 'pnpm install --frozen-lockfile'
                prod_install = 'pnpm install --prod --frozen-lockfile'
            else:
                install_cmd = 'npm ci'
                prod_install = 'npm ci --only=production'

            return templates.DOCKERFILE_NODEJS.format(
                install_command=install_cmd,
                build_command=self.req.build_command or 'npm run build',
                prod_install_command=prod_install,
                build_output='dist',
                port=self.req.port,
                start_cmd=json.dumps(self.req.start_command.split()),
            )

        elif self.req.language == 'python':
            return templates.DOCKERFILE_PYTHON.format(
                port=self.req.port,
                start_cmd=json.dumps(self.req.start_command.split()),
            )

        return ''


class DocumentationGenerator:
    """Generates documentation files."""

    def __init__(self, requirements: ProjectRequirements):
        self.req = requirements

    def generate(self) -> Dict[str, str]:
        """Generate documentation files."""
        files = {}

        # README.md
        files['PIPELINE_README.md'] = self._generate_readme()

        # .env.example
        files['.env.example'] = self._generate_env_example()

        return files

    def _generate_readme(self) -> str:
        """Generate README documentation."""
        # Prerequisites
        prerequisites = self._get_prerequisites()

        # Install instructions
        install_instructions = self._get_install_instructions()

        # Test instructions
        test_instructions = self.req.test_command

        # Dev instructions
        dev_instructions = self._get_dev_instructions()

        # Deployment stages
        deploy_stages = self._get_deploy_stages()

        # Environment variables table
        env_var_table = self._get_env_var_table()

        # Secrets table
        secrets_table = self._get_secrets_table()

        # Deployment instructions
        deployment_instructions = self._get_deployment_instructions()

        # Manual deployment
        manual_deploy = self._get_manual_deploy_instructions()

        # Troubleshooting
        troubleshooting = self._get_troubleshooting()

        return templates.README_TEMPLATE.format(
            project_name=self.req.project_name,
            description=self.req.description,
            main_branch=self.req.main_branch,
            repository_url=self.req.repository_url or 'https://github.com/username/repo',
            prerequisites=prerequisites,
            install_instructions=install_instructions,
            test_instructions=test_instructions,
            dev_instructions=dev_instructions,
            deploy_stages=deploy_stages,
            env_var_table=env_var_table,
            secrets_table=secrets_table,
            deployment_instructions=deployment_instructions,
            manual_deploy_instructions=manual_deploy,
            troubleshooting_section=troubleshooting,
            test_command=self.req.test_command,
            license='MIT',
        )

    def _get_prerequisites(self) -> str:
        """Get prerequisites list."""
        prereqs = []

        if self.req.language == 'nodejs':
            prereqs.append(f'- Node.js {self.req.language_version}.x or higher')
            prereqs.append(f'- {self.req.package_manager.upper()}')
        elif self.req.language == 'python':
            prereqs.append(f'- Python {self.req.language_version} or higher')
            prereqs.append('- pip or poetry')

        for db in self.req.databases:
            prereqs.append(f'- {db.title()} (for local development)')

        if 'redis' in self.req.services:
            prereqs.append('- Redis (for local development)')

        return '\n'.join(prereqs)

    def _get_install_instructions(self) -> str:
        """Get installation instructions."""
        if self.req.language == 'nodejs':
            if self.req.package_manager == 'yarn':
                return 'yarn install'
            elif self.req.package_manager == 'pnpm':
                return 'pnpm install'
            return 'npm install'
        elif self.req.language == 'python':
            return 'pip install -r requirements.txt'
        return ''

    def _get_dev_instructions(self) -> str:
        """Get development server instructions."""
        if self.req.language == 'nodejs':
            return 'npm run dev'
        elif self.req.language == 'python':
            if self.req.framework == 'django':
                return 'python manage.py runserver'
            elif self.req.framework == 'flask':
                return 'flask run'
            elif self.req.framework == 'fastapi':
                return 'uvicorn main:app --reload'
        return ''

    def _get_deploy_stages(self) -> str:
        """Get deployment stages description."""
        stages = []
        for i, env in enumerate(self.req.environments, start=3):
            stages.append(f'{i}. **Deploy to {env.title()}** - Deploys to {env} environment')
        return '\n'.join(stages)

    def _get_env_var_table(self) -> str:
        """Get environment variables table."""
        rows = ['| `NODE_ENV` | Application environment | Yes |'] if self.req.language == 'nodejs' else []
        rows.append(f'| `PORT` | Server port (default: {self.req.port}) | No |')

        for db in self.req.databases:
            if db == 'postgresql':
                rows.append('| `DATABASE_URL` | PostgreSQL connection string | Yes |')
            elif db == 'mongodb':
                rows.append('| `MONGODB_URI` | MongoDB connection string | Yes |')

        if 'redis' in self.req.services:
            rows.append('| `REDIS_URL` | Redis connection string | Yes |')

        return '\n'.join(rows)

    def _get_secrets_table(self) -> str:
        """Get GitHub secrets table."""
        platform = self.req.deployment_platform
        rows = []

        if platform == 'heroku':
            rows.extend([
                '| `HEROKU_API_KEY` | Heroku API key for deployments |',
                '| `HEROKU_EMAIL` | Email associated with Heroku account |',
            ])
            for env in self.req.environments:
                rows.append(f'| `HEROKU_APP_NAME_{env.upper()}` | Heroku app name for {env} |')
                rows.append(f'| `{env.upper()}_URL` | URL of the {env} deployment |')

        elif platform == 'aws':
            rows.extend([
                '| `AWS_ACCESS_KEY_ID` | AWS access key |',
                '| `AWS_SECRET_ACCESS_KEY` | AWS secret key |',
                '| `AWS_REGION` | AWS region for deployment |',
            ])

        elif platform == 'gcp':
            rows.extend([
                '| `GCP_SA_KEY` | Google Cloud service account JSON key |',
                '| `GCP_REGION` | GCP region for deployment |',
            ])

        elif platform == 'azure':
            rows.append('| `AZURE_CREDENTIALS` | Azure service principal credentials |')

        return '\n'.join(rows)

    def _get_deployment_instructions(self) -> str:
        """Get deployment instructions."""
        platform = self.req.deployment_platform

        if platform == 'heroku':
            return '''Deployments are automated via GitHub Actions when changes are pushed to the main branch.

### Environment Setup

1. Create Heroku apps for each environment:
   ```bash
   heroku create {}-staging
   heroku create {}-production
   ```

2. Add the Heroku API key to GitHub Secrets

3. Configure environment-specific settings in each Heroku app'''.format(
                self.req.project_name, self.req.project_name
            )

        elif platform == 'aws':
            return '''Deployments use AWS ECS with Docker containers.

### Initial Setup

1. Create an ECR repository for your Docker images
2. Set up an ECS cluster with services for each environment
3. Configure AWS credentials in GitHub Secrets'''

        return 'Automated deployments are configured via GitHub Actions.'

    def _get_manual_deploy_instructions(self) -> str:
        """Get manual deployment instructions."""
        platform = self.req.deployment_platform

        if platform == 'heroku':
            return '''```bash
# Deploy to staging
git push heroku-staging main

# Deploy to production
git push heroku-production main

# Or use Heroku CLI
heroku container:push web -a {}-staging
heroku container:release web -a {}-staging
```'''.format(self.req.project_name, self.req.project_name)

        elif platform == 'aws':
            return '''```bash
# Build and push Docker image
docker build -t your-ecr-repo:latest .
docker push your-ecr-repo:latest

# Update ECS service
aws ecs update-service --cluster your-cluster --service your-service --force-new-deployment
```'''

        return 'Follow the automated deployment process via GitHub Actions.'

    def _get_troubleshooting(self) -> str:
        """Get troubleshooting section."""
        dep_file = 'package.json' if self.req.language == 'nodejs' else 'requirements.txt'
        install_cmd = self._get_install_instructions()

        return templates.TROUBLESHOOTING_COMMON.format(
            dependency_file=dep_file,
            install_command=install_cmd,
            platform=self.req.deployment_platform.title(),
        )

    def _generate_env_example(self) -> str:
        """Generate .env.example file."""
        # Database env
        db_env = []
        for db in self.req.databases:
            if db == 'postgresql':
                db_env.append('DATABASE_URL=postgresql://user:password@localhost:5432/dbname')
            elif db == 'mysql':
                db_env.append('DATABASE_URL=mysql://user:password@localhost:3306/dbname')
            elif db == 'mongodb':
                db_env.append('MONGODB_URI=mongodb://localhost:27017/dbname')

        # Services env
        services_env = []
        if 'redis' in self.req.services:
            services_env.append('REDIS_URL=redis://localhost:6379')

        # Deployment env
        deploy_env = []
        if self.req.deployment_platform == 'heroku':
            deploy_env.append('# HEROKU_API_KEY=your-api-key')
        elif self.req.deployment_platform == 'aws':
            deploy_env.extend([
                '# AWS_ACCESS_KEY_ID=your-access-key',
                '# AWS_SECRET_ACCESS_KEY=your-secret-key',
                '# AWS_REGION=us-east-1',
            ])

        return templates.ENV_EXAMPLE.format(
            port=self.req.port,
            database_env='\n'.join(db_env) if db_env else '# No database configured',
            services_env='\n'.join(services_env) if services_env else '# No external services configured',
            deployment_env='\n'.join(deploy_env) if deploy_env else '# Configure deployment credentials',
        )


class ConfigGenerator:
    """Main generator that orchestrates all configuration generation."""

    def __init__(self, requirements: ProjectRequirements):
        self.req = requirements
        self.generators = [
            GitHubActionsGenerator(requirements),
            HerokuGenerator(requirements),
            DockerGenerator(requirements),
            DocumentationGenerator(requirements),
        ]

    def generate_all(self) -> Dict[str, str]:
        """Generate all configuration files."""
        all_files = {}

        for generator in self.generators:
            files = generator.generate()
            all_files.update(files)

        return all_files

    def get_summary(self) -> str:
        """Get a summary of what will be generated."""
        summary = []
        summary.append(f"Project: {self.req.project_name}")
        summary.append(f"Language: {self.req.language.title()}")
        if self.req.framework:
            summary.append(f"Framework: {self.req.framework.title()}")
        summary.append(f"Deploy to: {self.req.deployment_platform.title()}")
        summary.append(f"Environments: {', '.join(e.title() for e in self.req.environments)}")

        if self.req.databases:
            summary.append(f"Databases: {', '.join(d.title() for d in self.req.databases)}")

        if self.req.services:
            summary.append(f"Services: {', '.join(s.title() for s in self.req.services)}")

        summary.append("")
        summary.append("Files to generate:")

        files = self.generate_all()
        for filepath in sorted(files.keys()):
            summary.append(f"  - {filepath}")

        return '\n'.join(summary)
