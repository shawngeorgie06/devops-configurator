"""
Templates for CI/CD configuration files.
Contains all the template strings for GitHub Actions, Heroku, and documentation.
"""

# =============================================================================
# GITHUB ACTIONS TEMPLATES
# =============================================================================

GITHUB_ACTIONS_NODEJS = '''name: {workflow_name}

on:
  push:
    branches: [{push_branches}]
  pull_request:
    branches: [{pr_branches}]

env:
  NODE_VERSION: '{node_version}'

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    {services_block}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: '{package_manager}'

      - name: Install dependencies
        run: {install_command}

      - name: Run linter
        run: {lint_command}
        continue-on-error: true

      - name: Run tests
        run: {test_command}
        env:
          CI: true
          {test_env_vars}

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/
          retention-days: 7

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: '{package_manager}'

      - name: Install dependencies
        run: {install_command}

      - name: Build application
        run: {build_command}
        env:
          NODE_ENV: production

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: {build_output_path}
          retention-days: 7
{deploy_jobs}
'''

GITHUB_ACTIONS_PYTHON = '''name: {workflow_name}

on:
  push:
    branches: [{push_branches}]
  pull_request:
    branches: [{pr_branches}]

env:
  PYTHON_VERSION: '{python_version}'

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    {services_block}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          {install_command}

      - name: Run linter
        run: {lint_command}
        continue-on-error: true

      - name: Run tests
        run: {test_command}
        env:
          CI: true
          {test_env_vars}

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: {coverage_path}
          retention-days: 7

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          {install_command}

      - name: Verify application
        run: python -c "import {main_module}; print('Application imports successfully')"
{deploy_jobs}
'''

# =============================================================================
# DEPLOYMENT JOB TEMPLATES
# =============================================================================

HEROKU_DEPLOY_JOB = '''
  deploy-{environment}:
    name: Deploy to {environment_title}
    runs-on: ubuntu-latest
    needs: {needs}
    {environment_block}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{{{ secrets.HEROKU_API_KEY }}}}
          heroku_app_name: ${{{{ secrets.HEROKU_APP_NAME_{environment_upper} }}}}
          heroku_email: ${{{{ secrets.HEROKU_EMAIL }}}}
          {heroku_extra_options}

      - name: Verify deployment
        run: |
          sleep 30
          curl -f ${{{{ secrets.{environment_upper}_URL }}}}/health || echo "Health check endpoint not available"
'''

AWS_DEPLOY_JOB = '''
  deploy-{environment}:
    name: Deploy to {environment_title}
    runs-on: ubuntu-latest
    needs: {needs}
    {environment_block}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: ${{{{ secrets.AWS_REGION }}}}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{{{ steps.login-ecr.outputs.registry }}}}
          ECR_REPOSITORY: {ecr_repository}
          IMAGE_TAG: ${{{{ github.sha }}}}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster {cluster_name} --service {service_name}-{environment} --force-new-deployment
'''

GCP_DEPLOY_JOB = '''
  deploy-{environment}:
    name: Deploy to {environment_title}
    runs-on: ubuntu-latest
    needs: {needs}
    {environment_block}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{{{ secrets.GCP_SA_KEY }}}}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy {service_name}-{environment} \\
            --source . \\
            --region ${{{{ secrets.GCP_REGION }}}} \\
            --allow-unauthenticated
'''

AZURE_DEPLOY_JOB = '''
  deploy-{environment}:
    name: Deploy to {environment_title}
    runs-on: ubuntu-latest
    needs: {needs}
    {environment_block}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Azure
        uses: azure/login@v2
        with:
          creds: ${{{{ secrets.AZURE_CREDENTIALS }}}}

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v3
        with:
          app-name: {app_name}-{environment}
          package: .
'''

# =============================================================================
# SERVICES TEMPLATES (for databases, cache, etc.)
# =============================================================================

POSTGRES_SERVICE = '''  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5'''

REDIS_SERVICE = '''  redis:
    image: redis:7
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5'''

MYSQL_SERVICE = '''  mysql:
    image: mysql:8
    env:
      MYSQL_ROOT_PASSWORD: test
      MYSQL_DATABASE: test_db
    ports:
      - 3306:3306
    options: >-
      --health-cmd "mysqladmin ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5'''

MONGODB_SERVICE = '''  mongodb:
    image: mongo:6
    ports:
      - 27017:27017
    options: >-
      --health-cmd "mongosh --eval 'db.runCommand({{ping:1}})'"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5'''

# =============================================================================
# HEROKU CONFIGURATION TEMPLATES
# =============================================================================

PROCFILE_WEB_NODEJS = '''web: {start_command}
'''

PROCFILE_WEB_PYTHON = '''web: {start_command}
'''

HEROKU_APP_JSON = '''{{
  "name": "{app_name}",
  "description": "{description}",
  "repository": "{repository_url}",
  "keywords": {keywords},
  "env": {env_vars},
  "formation": {{
    "web": {{
      "quantity": 1,
      "size": "basic"
    }}
  }},
  "addons": {addons},
  "buildpacks": {buildpacks},
  "environments": {{
    "test": {{
      "scripts": {{
        "test": "{test_command}"
      }}
    }}
  }}
}}
'''

# =============================================================================
# DOCKER TEMPLATES
# =============================================================================

DOCKERFILE_NODEJS = '''# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN {install_command}

# Copy source code
COPY . .

# Build application
RUN {build_command}

# Production stage
FROM node:20-alpine AS production

WORKDIR /app

# Copy package files and install production dependencies only
COPY package*.json ./
RUN {prod_install_command}

# Copy built application
COPY --from=builder /app/{build_output} ./{build_output}

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs

# Expose port
EXPOSE {port}

# Start application
CMD {start_cmd}
'''

DOCKERFILE_PYTHON = '''# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 appuser
USER appuser

# Expose port
EXPOSE {port}

# Start application
CMD {start_cmd}
'''

DOCKERIGNORE = '''# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Build outputs
dist/
build/
*.egg-info/

# Test and coverage
coverage/
.coverage
htmlcov/
.pytest_cache/
.nyc_output/

# IDE and editor
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Environment and secrets
.env
.env.*
*.pem
*.key

# Git
.git/
.gitignore

# Documentation
*.md
docs/

# CI/CD
.github/
.gitlab-ci.yml
'''

# =============================================================================
# DOCUMENTATION TEMPLATES
# =============================================================================

README_TEMPLATE = '''# {project_name}

{description}

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment.

### Pipeline Stages

1. **Test** - Runs linting and automated tests
2. **Build** - Builds the application for production
{deploy_stages}

### Workflow Triggers

- **Push** to `{main_branch}` branch triggers full pipeline
- **Pull requests** to `{main_branch}` trigger test and build stages only

## Setup Instructions

### Prerequisites

{prerequisites}

### Local Development

```bash
# Clone the repository
git clone {repository_url}
cd {project_name}

# Install dependencies
{install_instructions}

# Run tests
{test_instructions}

# Start development server
{dev_instructions}
```

### Environment Variables

The following environment variables are required:

| Variable | Description | Required |
|----------|-------------|----------|
{env_var_table}

### GitHub Secrets

Configure these secrets in your GitHub repository settings:

| Secret | Description |
|--------|-------------|
{secrets_table}

## Deployment

{deployment_instructions}

### Manual Deployment

{manual_deploy_instructions}

## Troubleshooting

{troubleshooting_section}

## Contributing

1. Create a feature branch from `{main_branch}`
2. Make your changes
3. Run tests locally: `{test_command}`
4. Create a pull request

## License

{license}
'''

TROUBLESHOOTING_COMMON = '''### Common Issues

#### Build Fails with "Module not found"

- Ensure all dependencies are listed in {dependency_file}
- Run `{install_command}` locally to verify
- Check that the module name matches the import exactly

#### Tests Fail in CI but Pass Locally

- Check for environment-specific configurations
- Ensure test database is properly configured
- Verify all environment variables are set in GitHub Secrets

#### Deployment Fails with Authentication Error

- Verify {platform} API key/credentials are correct
- Check that secrets are properly named in GitHub repository settings
- Ensure the deployment account has proper permissions

#### Cache Issues

- Clear the GitHub Actions cache by updating the cache key
- Delete the `node_modules` or `.venv` folder and reinstall
'''

ENV_EXAMPLE = '''# Application
NODE_ENV=development
PORT={port}

# Database
{database_env}

# External Services
{services_env}

# Deployment (do not commit real values)
{deployment_env}
'''
