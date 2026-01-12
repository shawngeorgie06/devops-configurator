# DevOps Pipeline Configurator

Generate production-ready CI/CD configurations from plain English descriptions. No DevOps expertise required.

## Features

- **Natural Language Input**: Describe your project in plain English
- **Smart Detection**: Automatically detects language, framework, and requirements
- **Multiple Platforms**: Supports Heroku, AWS, GCP, and Azure
- **Complete Configs**: Generates GitHub Actions workflows, Dockerfiles, and documentation
- **Database Support**: PostgreSQL, MySQL, MongoDB, Redis configurations included

## Installation

```bash
pip install devops-configurator
```

Or install from source:

```bash
git clone https://github.com/yourusername/devops-configurator.git
cd devops-configurator
pip install -e .
```

## Quick Start

```bash
# Interactive mode
devops

# One-liner with quick mode
devops -q -i "Node.js Express app with PostgreSQL deploying to Heroku"

# Specify output directory
devops -i "Python FastAPI to AWS" -o ./my-pipeline
```

## Usage

### Interactive Mode

Simply run `devops` and describe your project:

```bash
$ devops

Describe your project:
> Node.js Express API with PostgreSQL database, deploying to Heroku with staging and production environments
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--input` | `-i` | Project description (skip interactive prompt) |
| `--output` | `-o` | Output directory (default: ./pipeline-config) |
| `--quick` | `-q` | Quick mode: skip questions, use smart defaults |
| `--lang` | `-l` | Set language: `node` or `python` |
| `--platform` | `-P` | Set platform: `heroku`, `aws`, `gcp`, `azure` |
| `--here` | | Output files to current directory |
| `--preview` | `-p` | Preview files without writing |
| `--non-interactive` | | Skip all interactive prompts |

### Examples

```bash
# Node.js to Heroku (quick mode)
devops -q -i "Express app with PostgreSQL" -P heroku --here

# Python to AWS
devops -q -i "FastAPI with Redis" -l python -P aws -o ./pipeline

# Preview without writing files
devops -i "Django app with PostgreSQL" --preview

# Full interactive experience
devops
```

## Supported Technologies

### Languages & Frameworks

| Language | Frameworks |
|----------|------------|
| Node.js | Express, Next.js, NestJS |
| Python | Django, Flask, FastAPI |

### Deployment Platforms

| Platform | Features |
|----------|----------|
| Heroku | Procfile, app.json, add-ons |
| AWS | ECR, ECS, Docker |
| GCP | Cloud Run, Docker |
| Azure | Web Apps |

### Databases & Services

- PostgreSQL
- MySQL
- MongoDB
- Redis

## Generated Files

Depending on your configuration, the tool generates:

```
your-project/
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # GitHub Actions pipeline
├── .env.example             # Environment variables template
├── Dockerfile               # (for AWS/GCP)
├── .dockerignore            # (for AWS/GCP)
├── Procfile                 # (for Heroku)
├── app.json                 # (for Heroku)
└── PIPELINE_README.md       # Setup documentation
```

### GitHub Actions Workflow Includes

- **Test Stage**: Linting, unit tests, coverage reports
- **Build Stage**: Production build, artifact upload
- **Deploy Stages**: Staging and production deployments
- **Service Containers**: Database and cache services for testing

## Configuration

### GitHub Secrets

After generating your pipeline, configure these secrets in your GitHub repository:

**For Heroku:**
- `HEROKU_API_KEY`
- `HEROKU_EMAIL`
- `HEROKU_APP_NAME_STAGING`
- `HEROKU_APP_NAME_PRODUCTION`

**For AWS:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

**For GCP:**
- `GCP_SA_KEY`
- `GCP_REGION`

**For Azure:**
- `AZURE_CREDENTIALS`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] GitLab CI/CD support
- [ ] Bitbucket Pipelines support
- [ ] More language support (Go, Java, Ruby)
- [ ] Kubernetes deployment configs
- [ ] Terraform infrastructure templates
- [ ] Web UI version

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/devops-configurator/issues).
