"""
Project management endpoints.
"""

import json
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Project(BaseModel):
    """Project model."""

    id: str
    name: str
    type: str
    client: str | None = None
    created_at: str
    updated_at: str
    kie_version: str = "v3"


class ProjectListResponse(BaseModel):
    """Response model for project list."""

    projects: list[Project]
    total: int


class ProjectSpec(BaseModel):
    """Project specification model."""

    project_id: str
    spec: dict


class OutputFile(BaseModel):
    """Output file model."""

    name: str
    path: str
    type: str
    size: int
    created_at: str


class ProjectOutputsResponse(BaseModel):
    """Response model for project outputs."""

    project_id: str
    outputs: list[OutputFile]
    total: int


def get_workspace_root() -> Path:
    """Get workspace root directory (searches upward for kie.yaml or uses cwd)."""
    current = Path.cwd()

    # Search upward for kie.yaml
    for parent in [current, *current.parents]:
        if (parent / "kie.yaml").exists():
            return parent

    # Default to cwd
    return current


def scan_for_projects(workspace_root: Path) -> list[Project]:
    """
    Scan workspace for KIE projects.

    Projects are identified by:
    - .kie_version file in directory
    - kie.yaml file in directory

    Args:
        workspace_root: Root directory to scan

    Returns:
        List of discovered projects
    """
    projects = []

    # Search for .kie_version files (max depth 3)
    for kie_version_file in workspace_root.rglob(".kie_version"):
        if kie_version_file.is_file():
            project_dir = kie_version_file.parent

            # Skip if too deep (> 3 levels from workspace root)
            try:
                relative = project_dir.relative_to(workspace_root)
                if len(relative.parts) > 3:
                    continue
            except ValueError:
                continue

            # Read version
            version = kie_version_file.read_text().strip()

            # Look for kie.yaml for metadata
            kie_yaml = project_dir / "kie.yaml"
            if kie_yaml.exists():
                try:
                    with open(kie_yaml) as f:
                        metadata = yaml.safe_load(f)

                    project_name = metadata.get("name", project_dir.name)
                    project_type = metadata.get("type", "analysis")
                    client = metadata.get("client")
                except Exception:
                    project_name = project_dir.name
                    project_type = "analysis"
                    client = None
            else:
                project_name = project_dir.name
                project_type = "analysis"
                client = None

            # Get timestamps
            created_at = datetime.fromtimestamp(project_dir.stat().st_ctime).isoformat()
            updated_at = datetime.fromtimestamp(project_dir.stat().st_mtime).isoformat()

            projects.append(
                Project(
                    id=project_dir.name,
                    name=project_name,
                    type=project_type,
                    client=client,
                    created_at=created_at,
                    updated_at=updated_at,
                    kie_version=version,
                )
            )

    return projects


@router.get("/", response_model=ProjectListResponse)
async def list_projects():
    """
    List all KIE projects in workspace.

    Scans for projects with .kie_version files.

    Returns:
        List of projects found in workspace
    """
    workspace_root = get_workspace_root()
    projects = scan_for_projects(workspace_root)

    return ProjectListResponse(
        projects=projects,
        total=len(projects)
    )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """
    Get project by ID.

    Args:
        project_id: Project identifier

    Returns:
        Project details

    Raises:
        HTTPException: 404 if project not found
    """
    workspace_root = get_workspace_root()
    projects = scan_for_projects(workspace_root)

    # Find project by ID
    for project in projects:
        if project.id == project_id:
            return project

    raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


@router.get("/{project_id}/spec", response_model=ProjectSpec)
async def get_project_spec(project_id: str):
    """
    Get project specification.

    Loads and returns the kie.yaml file for the project.

    Args:
        project_id: Project identifier

    Returns:
        Project spec YAML as JSON

    Raises:
        HTTPException: 404 if project or spec not found
    """
    workspace_root = get_workspace_root()
    projects = scan_for_projects(workspace_root)

    # Find project
    project_dir = None
    for project in projects:
        if project.id == project_id:
            project_dir = workspace_root / project_id
            break

    if project_dir is None or not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Load spec
    spec_file = project_dir / "kie.yaml"
    if not spec_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project spec not found for {project_id}"
        )

    try:
        with open(spec_file) as f:
            spec = yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse project spec: {str(e)}"
        )

    return ProjectSpec(project_id=project_id, spec=spec)


@router.get("/{project_id}/outputs", response_model=ProjectOutputsResponse)
async def list_project_outputs(project_id: str):
    """
    List outputs for a project.

    Scans the project's outputs/ directory for generated files.

    Args:
        project_id: Project identifier

    Returns:
        List of output artifacts

    Raises:
        HTTPException: 404 if project not found
    """
    workspace_root = get_workspace_root()
    projects = scan_for_projects(workspace_root)

    # Find project
    project_dir = None
    for project in projects:
        if project.id == project_id:
            project_dir = workspace_root / project_id
            break

    if project_dir is None or not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Scan outputs directory
    outputs_dir = project_dir / "outputs"
    outputs = []

    if outputs_dir.exists() and outputs_dir.is_dir():
        # Scan for chart JSONs, images, tables
        for file_path in outputs_dir.rglob("*"):
            if file_path.is_file():
                # Determine file type
                suffix = file_path.suffix.lower()
                if suffix == ".json":
                    file_type = "chart_config"
                elif suffix in [".png", ".jpg", ".jpeg", ".svg"]:
                    file_type = "image"
                elif suffix in [".csv", ".xlsx"]:
                    file_type = "table"
                elif suffix == ".pdf":
                    file_type = "pdf"
                else:
                    file_type = "other"

                # Get file stats
                stat = file_path.stat()

                # Relative path from outputs dir
                relative_path = file_path.relative_to(outputs_dir)

                outputs.append(
                    OutputFile(
                        name=file_path.name,
                        path=str(relative_path),
                        type=file_type,
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    )
                )

    # Sort by created date (newest first)
    outputs.sort(key=lambda x: x.created_at, reverse=True)

    return ProjectOutputsResponse(
        project_id=project_id,
        outputs=outputs,
        total=len(outputs)
    )
