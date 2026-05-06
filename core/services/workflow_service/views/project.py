from fastapi import APIRouter, Depends, HTTPException, Response
from uuid import UUID

import yaml
from services.workflow_service.schemas.compute_block import (
    BlockStatus,
    EdgeDTO,
    GetNodesByProjectResponse,
    SimpleNodeDTO,
)
from utils.errors.error import handle_error
import logging
from sqlalchemy.orm import Session

from services.workflow_service.controllers import (
    project_controller,
    share_controller,
    template_controller,
    workflow_controller,
)
from services.workflow_service.schemas.project import (
    AcceptTemplateRequest,
    CreateProjectRequest,
    CreateProjectResponse,
    ReadByUserResponse,
    ReadAllResponse,
    RenameProjectRequest,
    CreateProjectFromTemplateResponse,
    CreateProjectFromTemplateRequest,
    Project,
)
from utils.database.session_injector import get_database
from utils.security.token import User, get_user

router = APIRouter(prefix="/project", tags=["project"])


@router.post("/", response_model=CreateProjectResponse)
async def create_project(
    data: CreateProjectRequest,
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    try:
        with db.begin():
            project_uuid = project_controller.create_project(
                db, data.name, user.uuid
            )
        return CreateProjectResponse(project_uuid=project_uuid)
    except Exception as e:
        logging.exception(f"Error creating project: {e}")
        raise handle_error(e)


@router.post(
    "/from_template", response_model=CreateProjectFromTemplateResponse
)
async def create_project_from_template(
    data: CreateProjectFromTemplateRequest,
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    try:
        with db.begin():
            id = project_controller.create_project_from_template_file(
                db, data.name, data.template_identifier, user.uuid
            )
        return CreateProjectResponse(project_uuid=id)
    except Exception as e:
        logging.error(f"Error creating project from template: {e}")
        raise handle_error(e)


@router.get("/read_all", response_model=ReadAllResponse)
async def read_all_projects():
    try:
        projects = project_controller.read_all_projects()
        return ReadAllResponse(projects=projects)
    except Exception as e:
        logging.error(f"Error reading all projects: {e}")
        raise handle_error(e)


@router.get("/read_by_user", response_model=ReadByUserResponse)
async def read_projects_by_user(
    user: User = Depends(get_user),
):
    try:
        projects = project_controller.read_projects_by_user_uuid(user.uuid)
        return ReadByUserResponse(projects=projects)
    except Exception as e:
        logging.exception(f"Error reading project by user: {e}")
        raise handle_error(e)


@router.get("/{project_id}", response_model=Project)
async def read_project(
    project_id: UUID | None = None,
):
    try:
        if project_id is None:
            raise HTTPException(
                status_code=422, detail="Project ID is required"
            )

        project = project_controller.read_project(project_id)
        return project
    except Exception as e:
        logging.error(f"Error reading project: {e}")
        raise handle_error(e)


@router.post("/{project_id}/share")
async def invite_to_project(
    project_id: UUID | None = None,
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    try:
        if project_id is None:
            raise HTTPException(
                status_code=422, detail="Project ID is required"
            )

        token = share_controller.generate_project_token(
            db, project_id, user.uuid
        )
        return {"token": token}
    except Exception as e:
        logging.error(f"Error reading project: {e}")
        raise handle_error(e)


@router.get(
    "/{project_uuid}/export",
)
async def workflow_template_export(
    project_uuid: UUID | None = None,
    db: Session = Depends(get_database),
):
    try:
        if project_uuid is None:
            return HTTPException(
                status_code=422, detail="Project ID is required."
            )
        exported = template_controller.export_workflow_to_template(
            db, project_uuid
        )

        yaml_str = yaml.safe_dump(
            exported.model_dump(exclude_none=True), sort_keys=False
        )

        return Response(
            content=yaml_str,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": f'attachment; filename="{
                    project_uuid
                }.yaml"'
            },
        )
    except Exception as e:
        logging.error(f"Error exporting project: {e}")
        raise handle_error(e)


@router.get("/invite/{token}/accept")
async def accept_invite(
    token: str | None = None,
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    try:
        if token is None:
            raise HTTPException(status_code=422, detail="Token is required")

        with db.begin():
            response = share_controller.accept_invite(db, token, user.uuid)
        return response
    except Exception as e:
        logging.error(f"Error accepting invite: {e}")
        raise handle_error(e)


@router.get("/template/{token}/preview")
async def preview_template(
    token: str | None = None,
    db: Session = Depends(get_database),
):
    try:
        if token is None:
            raise HTTPException(status_code=422, detail="Token is required.")

        with db.begin():
            compute_blocks, dependencies = (
                share_controller.load_blocks_and_dependencies_from_token(
                    db, token
                )
            )

        return GetNodesByProjectResponse(
            blocks=[
                SimpleNodeDTO.from_compute_block(cb, BlockStatus.IDLE)
                for cb in compute_blocks
            ],
            edges=[EdgeDTO.from_block_dependencies(dp) for dp in dependencies],
        )
    except Exception as e:
        logging.error(f"Error generating preview: {e}")
        raise handle_error(e)


@router.post("/template/{token}/accept")
async def accept_template(
    body: AcceptTemplateRequest,
    token: str | None = None,
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    try:
        if token is None:
            raise HTTPException(status_code=422, detail="Token is required")

        with db.begin():
            created_id = share_controller.accept_from_template_share(
                db, token, body.project_name, user.uuid
            )

        return {"project_uuid": created_id}
    except Exception as e:
        logging.error(f"Error accepting template invite: {e}")
        raise handle_error(e)


@router.put("/", response_model=Project)
async def rename_project(
    data: RenameProjectRequest, db: Session = Depends(get_database)
):
    try:
        with db.begin():
            updated_project = project_controller.rename_project(
                data.project_uuid, data.new_name, db
            )
        return updated_project
    except Exception as e:
        raise handle_error(e)


@router.delete("/{project_id}", status_code=200)
async def delete_project(project_id: UUID, _: User = Depends(get_user)):
    try:
        project_controller.delete_project(project_id)
        workflow_controller.delete_dag_from_airflow(project_id)
    except Exception as e:
        logging.exception(f"Error deleting project with id {project_id}: {e}")
        raise handle_error(e)
