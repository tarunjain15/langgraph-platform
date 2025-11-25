"""
LangGraph Platform CLI

Main entry point for all commands: run, serve, create, deploy
"""

import click
from pathlib import Path


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LangGraph Platform - Workflow Runtime

    A workflow runtime for rapid experimentation and hosting of LangGraph workflows.
    """
    pass


@cli.command()
@click.argument('workflow', type=click.Path(exists=True))
@click.option('--watch', is_flag=True, help='Enable hot reload (experiment mode)')
@click.option('--verbose', is_flag=True, help='Show detailed logs')
@click.option('--input', '-i', 'input_data', help='Input data as JSON string')
def run(workflow: str, watch: bool, verbose: bool, input_data: str):
    """Execute workflow in experiment mode

    WORKFLOW: Path to workflow Python file (e.g., workflows/my_workflow.py)

    Examples:
        lgp run workflows/basic_workflow.py
        lgp run workflows/my_workflow.py --watch
        lgp run workflows/my_workflow.py --watch --verbose
        echo '{"topic": "test"}' | lgp run workflows/my_workflow.py
        lgp run workflows/my_workflow.py --input '{"topic": "test"}'
    """
    import sys
    import json
    from runtime.executor import WorkflowExecutor

    click.echo(f"[lgp] Loading workflow: {workflow}")
    click.echo(f"[lgp] Environment: experiment")
    click.echo(f"[lgp] Hot reload: {'ON' if watch else 'OFF'}")
    click.echo(f"[lgp] Verbose: {'ON' if verbose else 'OFF'}")
    click.echo()

    # Parse input data from stdin, --input flag, or use default
    parsed_input = None
    if input_data:
        # From --input flag
        try:
            parsed_input = json.loads(input_data)
        except json.JSONDecodeError as e:
            click.echo(f"[lgp] ❌ Invalid JSON in --input: {e}")
            raise click.Abort()
    elif not sys.stdin.isatty():
        # From stdin (piped input)
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                parsed_input = json.loads(stdin_data)
        except json.JSONDecodeError as e:
            click.echo(f"[lgp] ❌ Invalid JSON from stdin: {e}")
            raise click.Abort()

    executor = WorkflowExecutor(environment="experiment", verbose=verbose)

    if watch:
        # Hot reload mode
        from runtime.hot_reload import watch_and_execute
        watch_and_execute(workflow, executor)
    else:
        # Single execution
        executor.execute(workflow, input_data=parsed_input)


@cli.command()
@click.argument('workflow', type=click.Path(exists=True))
@click.option('--port', default=8000, help='Port to run server on')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
def serve(workflow: str, port: int, host: str):
    """Start workflow API server (hosted mode)

    WORKFLOW: Path to workflow Python file

    Examples:
        lgp serve workflows/my_workflow.py
        lgp serve workflows/my_workflow.py --port 8001
    """
    from runtime.server import serve_workflow

    click.echo(f"[lgp] Starting API server...")
    click.echo(f"[lgp] Environment: hosted")
    click.echo(f"[lgp] Workflow: {workflow}")
    click.echo(f"[lgp] Server: http://{host}:{port}")
    click.echo()

    serve_workflow(workflow, host=host, port=port)


@cli.command()
@click.argument('name')
@click.option('--template', default='basic', help='Template to use (basic, multi_agent, with_claude_code)')
def create(name: str, template: str):
    """Create workflow from template

    NAME: Name for the new workflow

    Examples:
        lgp create my_workflow
        lgp create research_pipeline --template multi_agent
        lgp create claude_workflow --template with_claude_code
    """
    from cli.commands.create import create_workflow_from_template

    click.echo(f"[lgp] Creating workflow: {name}")
    click.echo(f"[lgp] Template: {template}")
    click.echo()

    # Create workflow
    result = create_workflow_from_template(name, template)

    if result["success"]:
        click.echo(f"✅ Created: {result['workflow_path']}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  1. Edit your workflow: {result['workflow_path']}")
        click.echo(f"  2. Run: lgp run workflows/{name}.py")
        click.echo(f"  3. Serve: lgp serve workflows/{name}.py")
    else:
        click.echo(f"❌ Error: {result['message']}")
        raise click.Abort()


@cli.command()
@click.argument('workflow')
def deploy(workflow: str):
    """Deploy workflow to production

    WORKFLOW: Name of the workflow to deploy

    Examples:
        lgp deploy my_workflow
    """
    click.echo(f"[lgp] Deploying workflow: {workflow}")
    click.echo(f"[lgp] ⚠️  Not implemented yet (R7)")


@cli.command()
def templates():
    """List available workflow templates"""
    click.echo("Available Templates:")
    click.echo()
    click.echo("  basic             ⭐ Simple single-node workflow")
    click.echo("  multi_agent       ⭐⭐ 3-agent pipeline (research → write → review)")
    click.echo("  with_claude_code  ⭐⭐⭐ Stateful Claude Code agents")
    click.echo()
    click.echo("Usage:")
    click.echo("  lgp create my_workflow --template basic")
    click.echo()
    click.echo("Documentation:")
    click.echo("  See templates/README.md for detailed guide")


if __name__ == '__main__':
    cli()
