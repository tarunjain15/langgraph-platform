"""
Workflow Creation Command

Creates a new workflow from a template with parameterization.
"""

import os
import shutil
from pathlib import Path
from typing import Optional


class TemplateManager:
    """Manages workflow template operations"""

    # Valid template names
    VALID_TEMPLATES = ["basic", "multi_agent", "with_claude_code"]

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            project_root: Root directory of the project (auto-detected if None)
        """
        if project_root is None:
            # Auto-detect project root (look for cli/ directory)
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "cli").exists() and (current / "templates").exists():
                    project_root = current
                    break
                current = current.parent

        self.project_root = project_root
        self.templates_dir = project_root / "templates"
        self.workflows_dir = project_root / "workflows"

    def list_templates(self) -> list[str]:
        """
        Get list of available templates.

        Returns:
            List of template names
        """
        return self.VALID_TEMPLATES

    def template_exists(self, template_name: str) -> bool:
        """
        Check if template exists.

        Args:
            template_name: Name of the template

        Returns:
            True if template exists
        """
        return template_name in self.VALID_TEMPLATES

    def get_template_path(self, template_name: str) -> Path:
        """
        Get path to template directory.

        Args:
            template_name: Name of the template

        Returns:
            Path to template directory
        """
        return self.templates_dir / template_name

    def workflow_exists(self, workflow_name: str) -> bool:
        """
        Check if workflow already exists.

        Args:
            workflow_name: Name of the workflow

        Returns:
            True if workflow file exists
        """
        workflow_path = self.workflows_dir / f"{workflow_name}.py"
        return workflow_path.exists()

    def create_workflow(self, workflow_name: str, template_name: str) -> Path:
        """
        Create workflow from template.

        Args:
            workflow_name: Name for the new workflow
            template_name: Template to use

        Returns:
            Path to created workflow file

        Raises:
            ValueError: If template doesn't exist or workflow already exists
        """
        # Validate template
        if not self.template_exists(template_name):
            raise ValueError(
                f"Template '{template_name}' not found. "
                f"Available templates: {', '.join(self.VALID_TEMPLATES)}"
            )

        # Check if workflow already exists
        if self.workflow_exists(workflow_name):
            raise ValueError(
                f"Workflow '{workflow_name}' already exists at "
                f"workflows/{workflow_name}.py"
            )

        # Get template source
        template_path = self.get_template_path(template_name)
        template_file = template_path / "workflow.py"

        if not template_file.exists():
            raise ValueError(f"Template file not found: {template_file}")

        # Read template content
        with open(template_file, 'r') as f:
            template_content = f.read()

        # Parameterize template (simple string replacement for now)
        # Future: Add Jinja2 templating if more complex parameterization needed
        workflow_content = self._parameterize_template(
            template_content,
            workflow_name,
            template_name
        )

        # Ensure workflows directory exists
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Write workflow file
        workflow_path = self.workflows_dir / f"{workflow_name}.py"
        with open(workflow_path, 'w') as f:
            f.write(workflow_content)

        return workflow_path

    def _parameterize_template(
        self,
        content: str,
        workflow_name: str,
        template_name: str
    ) -> str:
        """
        Parameterize template content with workflow-specific values.

        Args:
            content: Template file content
            workflow_name: Name of the workflow being created
            template_name: Name of the template used

        Returns:
            Parameterized content
        """
        # For now, templates are self-contained and don't need parameterization
        # In the future, we could add template variables like {{workflow_name}}
        return content


def create_workflow_from_template(
    workflow_name: str,
    template_name: str = "basic"
) -> dict:
    """
    Create a new workflow from a template.

    Args:
        workflow_name: Name for the new workflow
        template_name: Template to use (default: basic)

    Returns:
        Dict with workflow creation results:
            - success: bool
            - workflow_path: Path to created workflow
            - template_used: Template name
            - message: Status message
    """
    try:
        manager = TemplateManager()

        # Create workflow
        workflow_path = manager.create_workflow(workflow_name, template_name)

        return {
            "success": True,
            "workflow_path": workflow_path,
            "template_used": template_name,
            "message": f"Workflow created: {workflow_path}"
        }

    except ValueError as e:
        return {
            "success": False,
            "workflow_path": None,
            "template_used": template_name,
            "message": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "workflow_path": None,
            "template_used": template_name,
            "message": f"Error creating workflow: {e}"
        }
