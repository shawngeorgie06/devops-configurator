#!/usr/bin/env python3
"""
DevOps Pipeline Configurator

A conversational tool that helps users generate CI/CD configurations
without needing deep DevOps knowledge.

Usage:
    python configurator.py                    # Interactive mode
    python configurator.py --input "..."      # Direct input mode
    python configurator.py --output ./output  # Specify output directory
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List

from .parser import RequirementsParser, ProjectRequirements, get_missing_info
from .generators import ConfigGenerator


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''
        cls.END = ''


def print_header(text: str) -> None:
    """Print a header line."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print("=" * len(text))


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}[OK]{Colors.END} {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.END} {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")


def print_file_content(filepath: str, content: str, max_lines: int = 50) -> None:
    """Print file content with syntax highlighting hint."""
    lines = content.split('\n')
    truncated = len(lines) > max_lines

    print(f"\n{Colors.BOLD}--- {filepath} ---{Colors.END}")

    for line in lines[:max_lines]:
        print(f"  {line}")

    if truncated:
        print(f"  {Colors.YELLOW}... ({len(lines) - max_lines} more lines){Colors.END}")

    print()


def ask_question(question: str, options: List[str], default: Optional[int] = None) -> str:
    """Ask a multiple choice question."""
    print(f"\n{Colors.BOLD}{question}{Colors.END}")
    for i, option in enumerate(options, 1):
        default_marker = " (default)" if default == i else ""
        print(f"  {i}. {option}{default_marker}")

    while True:
        try:
            prompt = f"Enter choice [1-{len(options)}]: "
            response = input(prompt).strip()

            if not response and default:
                return options[default - 1]

            choice = int(response)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print_warning(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_warning("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes/no question."""
    default_hint = "Y/n" if default else "y/N"
    while True:
        try:
            response = input(f"{question} [{default_hint}]: ").strip().lower()
            if not response:
                return default
            if response in ('y', 'yes'):
                return True
            if response in ('n', 'no'):
                return False
            print_warning("Please enter 'y' or 'n'")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def get_user_input(prompt: str) -> str:
    """Get free-form input from user."""
    try:
        return input(f"{prompt}: ").strip()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)


def display_welcome() -> None:
    """Display welcome message."""
    print(f"""
{Colors.BOLD}{Colors.CYAN}================================================
     DevOps Pipeline Configurator
================================================{Colors.END}

Generate production-ready CI/CD configurations
by describing your project in plain language.

Supported:
  - Languages: Node.js, Python
  - Platforms: Heroku, AWS, GCP, Azure
  - Features: Testing, Staging/Production, Databases
""")


def display_summary(requirements: ProjectRequirements, files: Dict[str, str]) -> None:
    """Display a summary of what will be generated."""
    print_header("Configuration Summary")

    print(f"""
{Colors.BOLD}Project Configuration:{Colors.END}
  Name:           {requirements.project_name}
  Language:       {requirements.language.title()} {requirements.language_version}
  Framework:      {requirements.framework.title() if requirements.framework else 'None specified'}
  Platform:       {requirements.deployment_platform.title()}
  Environments:   {', '.join(e.title() for e in requirements.environments)}
""")

    if requirements.databases or requirements.services:
        print(f"{Colors.BOLD}Services:{Colors.END}")
        if requirements.databases:
            print(f"  Databases:    {', '.join(d.title() for d in requirements.databases)}")
        if requirements.services:
            print(f"  Other:        {', '.join(s.title() for s in requirements.services)}")
        print()

    print(f"{Colors.BOLD}Files to Generate:{Colors.END}")
    for filepath in sorted(files.keys()):
        lines = len(files[filepath].split('\n'))
        print(f"  - {filepath} ({lines} lines)")


def interactive_refinement(requirements: ProjectRequirements) -> ProjectRequirements:
    """Allow user to refine detected requirements."""
    print_header("Detected Configuration")

    # Show what was detected
    print(f"""
Based on your description, I detected:
  - Language: {requirements.language.title()}
  - Framework: {requirements.framework or 'Not specified'}
  - Platform: {requirements.deployment_platform.title()}
  - Environments: {', '.join(requirements.environments)}
""")

    if not ask_yes_no("Does this look correct?"):
        # Let user adjust
        print("\nLet me ask a few questions to refine the configuration:\n")

        # Language
        lang_choice = ask_question(
            "What programming language is your project?",
            ['Node.js', 'Python', 'Go', 'Java'],
            1 if requirements.language == 'nodejs' else 2
        )
        requirements.language = lang_choice.lower().replace('.', '')
        if requirements.language == 'nodejs':
            requirements.language = 'nodejs'

        # Framework (if Node.js or Python)
        if requirements.language == 'nodejs':
            fw_choice = ask_question(
                "What Node.js framework are you using?",
                ['Express', 'Next.js', 'NestJS', 'None/Other'],
                1
            )
            requirements.framework = fw_choice.lower().replace('.', '') if fw_choice != 'None/Other' else None

        elif requirements.language == 'python':
            fw_choice = ask_question(
                "What Python framework are you using?",
                ['Django', 'Flask', 'FastAPI', 'None/Other'],
                1
            )
            requirements.framework = fw_choice.lower() if fw_choice != 'None/Other' else None

        # Platform
        platform_choice = ask_question(
            "Where do you want to deploy?",
            ['Heroku', 'AWS', 'Google Cloud (GCP)', 'Azure'],
            1
        )
        platform_map = {
            'Heroku': 'heroku',
            'AWS': 'aws',
            'Google Cloud (GCP)': 'gcp',
            'Azure': 'azure'
        }
        requirements.deployment_platform = platform_map[platform_choice]

        # Environments
        if ask_yes_no("Do you need a staging environment?", True):
            if 'staging' not in requirements.environments:
                requirements.environments.insert(0, 'staging')
        else:
            requirements.environments = [e for e in requirements.environments if e != 'staging']

    # Additional refinements
    print()
    if ask_yes_no("Do you need Docker configuration?", requirements.use_docker):
        requirements.use_docker = True
    else:
        requirements.use_docker = False

    # Databases
    if not requirements.databases:
        if ask_yes_no("Do you need a database?", False):
            db_choice = ask_question(
                "What database are you using?",
                ['PostgreSQL', 'MySQL', 'MongoDB', 'None'],
                1
            )
            if db_choice != 'None':
                requirements.databases = [db_choice.lower()]

    # Redis
    if 'redis' not in requirements.services:
        if ask_yes_no("Do you need Redis (caching/sessions)?", False):
            requirements.services.append('redis')

    return requirements


def write_files(files: Dict[str, str], output_dir: Path) -> None:
    """Write generated files to disk."""
    print_header("Writing Files")

    for filepath, content in sorted(files.items()):
        full_path = output_dir / filepath

        # Create directory if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print_success(f"Created {filepath}")


def preview_files(files: Dict[str, str]) -> None:
    """Preview generated files."""
    print_header("Generated Files Preview")

    for filepath in sorted(files.keys()):
        content = files[filepath]
        print_file_content(filepath, content)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='DevOps Pipeline Configurator - Generate CI/CD configurations easily'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Project description (skip interactive prompt)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./pipeline-config',
        help='Output directory for generated files (default: ./pipeline-config)'
    )
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='Preview files without writing'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Skip interactive refinement questions'
    )
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Quick mode: minimal questions, smart defaults'
    )
    parser.add_argument(
        '--lang', '-l',
        choices=['node', 'python'],
        help='Shortcut: specify language directly'
    )
    parser.add_argument(
        '--platform', '-P',
        choices=['heroku', 'aws', 'gcp', 'azure'],
        help='Shortcut: specify platform directly'
    )
    parser.add_argument(
        '--here',
        action='store_true',
        help='Output files to current directory'
    )

    args = parser.parse_args()

    # Handle --here flag
    if args.here:
        args.output = '.'

    # Handle colors
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Display welcome
    display_welcome()

    # Get project description
    if args.input:
        user_input = args.input
        print_info(f"Using provided description: {user_input[:100]}...")
    else:
        print(f"{Colors.BOLD}Describe your project:{Colors.END}")
        print("(Include language, framework, where you want to deploy, and any special needs)")
        print()
        print("Examples:")
        print('  "Node.js Express app deploying to Heroku with PostgreSQL"')
        print('  "Python FastAPI with staging and production on AWS"')
        print()

        user_input = get_user_input("Your project description")

        if not user_input:
            print_error("No description provided. Exiting.")
            sys.exit(1)

    # Parse requirements
    print()
    print_info("Analyzing your requirements...")
    req_parser = RequirementsParser()
    requirements = req_parser.parse(user_input)

    # Apply shortcut flags
    if args.lang:
        requirements.language = 'nodejs' if args.lang == 'node' else args.lang
    if args.platform:
        requirements.deployment_platform = args.platform

    # Interactive refinement (skip in quick mode)
    if args.quick:
        print_info("Quick mode - using smart defaults")
    elif not args.non_interactive and sys.stdin.isatty():
        requirements = interactive_refinement(requirements)
    else:
        print_info("Running in non-interactive mode")

    # Update defaults based on final configuration
    req_parser.requirements = requirements
    req_parser._set_defaults()
    requirements = req_parser.requirements

    # Generate configurations
    print()
    print_info("Generating configurations...")
    generator = ConfigGenerator(requirements)
    files = generator.generate_all()

    # Display summary
    display_summary(requirements, files)

    # Determine if we should interact
    is_interactive = not args.non_interactive and not args.quick and sys.stdin.isatty()

    # Preview files
    print()
    if args.preview:
        # Preview mode - always show preview
        preview_files(files)
        print_warning("Preview mode - files not written")
    elif is_interactive:
        if ask_yes_no("Would you like to preview the generated files?", True):
            preview_files(files)

        output_dir = Path(args.output).resolve()
        print()
        if ask_yes_no(f"Write files to {output_dir}?", True):
            write_files(files, output_dir)

            print()
            print_header("Next Steps")
            print(f"""
1. Review the generated files in: {output_dir}

2. Copy the files to your project:
   - .github/workflows/ci-cd.yml -> your-project/.github/workflows/
   - Other files -> your-project root

3. Configure GitHub Secrets (see PIPELINE_README.md for list)

4. Push to GitHub and watch your pipeline run!

{Colors.BOLD}Need help?{Colors.END} Check PIPELINE_README.md for detailed instructions.
""")
        else:
            print_warning("Files not written")
    else:
        # Non-interactive mode - just write the files
        output_dir = Path(args.output).resolve()
        write_files(files, output_dir)

        print()
        print_header("Next Steps")
        print(f"""
1. Review the generated files in: {output_dir}

2. Copy the files to your project:
   - .github/workflows/ci-cd.yml -> your-project/.github/workflows/
   - Other files -> your-project root

3. Configure GitHub Secrets (see PIPELINE_README.md for list)

4. Push to GitHub and watch your pipeline run!
""")

    print_success("Done!")


if __name__ == '__main__':
    main()
