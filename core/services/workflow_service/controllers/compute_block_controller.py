from fastapi import HTTPException
import os
import tempfile
import logging
import subprocess
import base64

from git import Repo
from typing import Literal
from uuid import UUID, uuid4
from sqlalchemy import select, case, asc, delete
from sqlalchemy.orm import Session, contains_eager
from utils.database.session_injector import get_database
from utils.config.defaults import (
    get_file_cfg_defaults_dict,
    get_pg_cfg_defaults_dict,
    SETTINGS_CLASS, extract_default_keys_from_io
)
import utils.data.file_handling as fh
from services.workflow_service.models.block import Block, block_dependencies
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.input_output import (
    InputOutput, InputOutputType, DataType
)
from services.workflow_service.schemas.compute_block import (
    ConfigType,
    InputOutputDTO,
)
from services.workflow_service.schemas.workflow import (
    WorkflowTemplate,
    Block as BlockTemplate,
    Input as InputTemplate,
    Output as OutputTemplate
)
from scystream.sdk.config import load_config
from scystream.sdk.config.models import (
    ComputeBlock,
    Entrypoint as SDKEntrypoint,
    InputOutputModel
)


CBC_FILE_IDENTIFIER = "cbc.yaml"


def _get_cb_info_from_repo(repo_url: str) -> ComputeBlock:
    logging.debug(f"Cloning ComputeBlock Repo from: {repo_url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            Repo.clone_from(
                repo_url,
                tmpdir,
                multi_options=[
                    "--depth=1",
                    "-c",
                    "core.sshCommand=ssh -o StrictHostKeyChecking=no"
                ],
                allow_unsafe_options=True
            )

            cbc_path = os.path.join(tmpdir, CBC_FILE_IDENTIFIER)

            if not os.path.isfile(cbc_path):
                raise HTTPException(
                    status_code=422,
                    detail=f"Repository {repo_url} does not contain a cbc.yaml"
                )

            return load_config(cbc_path)
        except subprocess.CalledProcessError as e:
            logging.error(f"Could not clone the repository {repo_url}: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Couldn't clone the repository: {repo_url}"
            )
        except HTTPException as e:
            raise e


def request_cb_info(repo_url: str) -> ComputeBlock:
    logging.debug(f"Requesting ComputeBlock info for: {repo_url}")
    cb = _get_cb_info_from_repo(repo_url)

    for entry_name, entry in cb.entrypoints.items():
        for on, output in entry.outputs.items():
            # Determine the type and the default values
            o_type = DataType(output.type)
            default_values = (
                get_file_cfg_defaults_dict(on)
                if o_type is DataType.FILE
                else get_pg_cfg_defaults_dict(on)
            )

            # Update the config with default values
            output.config = updated_configs_with_values(
                output, default_values, o_type
            )

    return cb


def updated_configs_with_values(
        io: InputOutput,
        default_values: dict,
        type: DataType
) -> dict:
    """
    Returns a new config dict with default keys replaced by values from
    default_values.

    Parameters:
    - io: InputOutput object whose config will be updated.
    - default_values: Dict mapping default keys to their replacement values.

    Returns:
    - A new config dictionary with updated values.
    """
    logging.debug(f"Get update configs for source config {
        io.config} and values {default_values}.")
    new_config = io.config.copy() if io.config else {}

    settings_class = SETTINGS_CLASS.get(type)
    if not settings_class:
        return new_config

    default_keys = settings_class.__annotations__.keys()
    cfg_keys = {key: key for key in new_config}

    for dk in default_keys:
        key = next((k for k in cfg_keys if dk in k), None)
        if key and dk in default_values:
            # Only replace if default_values[dk] is set
            new_config[key] = default_values[dk]

    logging.debug(f"Update config: {new_config}.")
    return new_config


def _extract_block_urls_from_template(template: WorkflowTemplate) -> list[str]:
    """
    Extracts the urls of all blocks used in the template.
    Makes sure that there are no duplicates in the returned list.
    """
    seen = set()
    urls = []

    for template_block in template.blocks:
        url = template_block.repo_url
        if url not in seen:
            seen.add(url)
            urls.append(url)

    return urls


def _upload_file_to_bucket(
    file_b64: str,
    file_ext: str
):
    ext = file_ext.lstrip(".")
    file_uuid = uuid4()
    configs = get_file_cfg_defaults_dict(file_uuid, ext)
    target_file_name = configs["FILE_NAME"]

    s3_url = fh.get_minio_url(
        configs["S3_HOST"], configs["S3_PORT"])
    client = fh.get_s3_client(
        s3_url=s3_url,
        access_key=configs["S3_ACCESS_KEY"],
        secret_key=configs["S3_SECRET_KEY"]
    )

    # Decode and upload
    file_bytes = base64.b64decode(file_b64)
    client.put_object(
        Bucket=configs["BUCKET_NAME"],
        Key=target_file_name,
        Body=file_bytes
    )

    return configs


def bulk_upload_files(
    data: list[InputOutputDTO]
) -> list[InputOutput]:
    for inp in data:
        if inp.selected_file_b64 and inp.selected_file_type:
            file_loc_desc = _upload_file_to_bucket(
                inp.selected_file_b64,
                inp.selected_file_type.lstrip(".")
            )
            updated_cfgs = updated_configs_with_values(
                inp, file_loc_desc, DataType.FILE)
            inp.config = updated_cfgs

    return data


def _bulk_query_blocks(repo_urls: list[str]) -> dict[str, ComputeBlock]:
    """
    Returns a mapping of repo_url to a ComputeBlock instance
    """
    blocks: dict[str, Block] = {}

    for repo_url in repo_urls:
        logging.debug(f"Querying block from: {repo_url}")
        blocks[repo_url] = _get_cb_info_from_repo(repo_url)

    return blocks


def _build_io(
    identifier: str,
    io_type: InputOutputType,
    data_type: DataType,
    description: str,
    config: dict,
    template_settings: dict | None = None
) -> InputOutput:
    """
    Constructs an InputOutput object, applying default values for outputs
    and merging template settings if provided.
    """
    io = InputOutput(
        type=io_type,
        name=identifier,
        data_type=data_type,
        description=description,
        config=config
    )

    if io_type is InputOutputType.OUTPUT:
        default_values = (
            get_file_cfg_defaults_dict(identifier)
            if data_type is DataType.FILE
            else get_pg_cfg_defaults_dict(identifier)
        )
        io.config = updated_configs_with_values(io, default_values, data_type)

    if template_settings:
        io.config = {**io.config, **template_settings}

    return io


def _configure_io_items(
    template_ios: list[InputTemplate] | list[OutputTemplate],
    unconfigured_ios: dict[str, InputOutputModel],
    io_type: InputOutputType
) -> list[InputOutput]:
    """
    Iterates over the compute blocks ios.
    If the template provides configs to overwrite the compute blocks configs,
    this will be configured.
    If not, default values will be used where appropriate.
    """

    configured: list[InputOutput] = []
    template_map = {t.identifier: t for t in template_ios}

    for identifier, unconfigured_io in unconfigured_ios.items():
        template = template_map.get(identifier)
        data_type = DataType(unconfigured_io.type)

        if template:
            if not do_config_keys_match(
                config_type="io",
                original_config=unconfigured_io.config,
                update_config=template.settings or {},
            ):
                logging.error(f"""
                    Keys used in template to configure {template.identifier}
                    do not match the compute block IO definition.
                """)
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"The keys used in the template to configure IO '{
                            template.identifier}' "
                        f"do not match those in the compute block definition."
                    )
                )

            configured.append(
                _build_io(
                    identifier=template.identifier,
                    io_type=io_type,
                    data_type=data_type,
                    description=unconfigured_io.description,
                    config=unconfigured_io.config,
                    template_settings=template.settings
                )
            )
        else:
            configured.append(
                _build_io(
                    identifier=identifier,
                    io_type=io_type,
                    data_type=data_type,
                    description=unconfigured_io.description,
                    config=unconfigured_io.config
                )
            )

    return configured


def _configure_block(
    block_template: BlockTemplate,
    unconfigured_entry: SDKEntrypoint
) -> (
    ConfigType,
    list[InputOutput],
    list[InputOutput]
):
    """
    This method returns:
        :dict: the configuration from the template applied to the configuration
            of the compute block
        :list[InputOutput]: All Inputs with the configurations from the
            template applied
        :list[InputOutput]: All Outputs with the configurations from the
            template applied
    """
    envs = unconfigured_entry.envs
    envs_from_template = block_template.settings

    if do_config_keys_match(
        config_type="envs",
        original_config=envs,
        update_config=envs_from_template or {},
    ):
        # TODO: Test what happens if envs from template are None
        configured_envs = {**envs, **(envs_from_template or {})}
    else:
        raise HTTPException(
            status_code=422,
            detail=f"""
                The Config-Keys provided by the template
                do not match with the configs that the block
                {block_template.name} offers.
                """
        )

    configured_inputs: list[InputOutput] = _configure_io_items(
        block_template.inputs or [],
        unconfigured_entry.inputs or {},
        InputOutputType.INPUT
    )

    configured_outputs: list[InputOutput] = _configure_io_items(
        block_template.outputs or [],
        unconfigured_entry.outputs or {},
        InputOutputType.OUTPUT
    )

    return (configured_envs, configured_inputs, configured_outputs)


def create_compute_blocks_from_template(
    db: Session,
    workflow_template: WorkflowTemplate,
    project_id: UUID
) -> list[Block]:
    """
    Creates and configures all compute blocks as defined in the template.
    Make sure to pass a db session with transaction activated
    """
    required_blocks = _extract_block_urls_from_template(workflow_template)
    unconfigured_blocks = _bulk_query_blocks(required_blocks)

    try:
        for block_template in workflow_template.blocks:
            unconfigured_block: ComputeBlock = \
                unconfigured_blocks.get(
                    block_template.repo_url
                )
            unconfigured_entrypoint: SDKEntrypoint = \
                unconfigured_block.entrypoints.get(
                    block_template.entrypoint
                )

            if unconfigured_entrypoint is None:
                logging.error(f"""
                              Template definition of block
                              {block_template.name} is invalid,
                              given entrypoint {block_template.entrypoint}
                              does not exist on Compute Block!
                              """)
                raise HTTPException(
                    status_code=422,
                    detail="Template definition is invalid!"
                )

            configured_env, configured_entry_inputs, \
                configured_entry_outputs = _configure_block(
                    block_template,
                    unconfigured_entrypoint,
                )
            create_compute_block(
                db,
                unconfigured_block.name,
                unconfigured_block.description,
                unconfigured_block.author,
                unconfigured_block.docker_image,
                block_template.repo_url,
                block_template.name,
                1000,
                1000,
                entry_name=block_template.entrypoint,
                entry_description=unconfigured_block.description,
                envs=configured_env,
                inputs=configured_entry_inputs,
                outputs=configured_entry_outputs,
                project_id=project_id
            )
    except Exception as e:
        logging.exception(f"Error compute blocks from template: {e}")
        raise e


def create_compute_block(
        db: Session,
        name: str,
        description: str,
        author: str,
        docker_image: str,
        repo_url: str,
        custom_name: str,
        x_pos: float,
        y_pos: float,
        entry_name: str,
        entry_description: str,
        envs: ConfigType,
        inputs: list[InputOutput],
        outputs: list[InputOutput],
        project_id: str
) -> Block:
    """
    Creates a Compute Block.
    Make Sure to pass a transactional Session into this function (param: db)
    """
    logging.info(f"Creating compute block: {name}")

    try:
        # (1) Create Entrypoint
        entry = Entrypoint(
            name=entry_name,
            description=entry_description,
            envs=envs,
        )
        db.add(entry)
        db.flush()

        # (2) Create Input/Outputs
        input_outputs = inputs + outputs

        for o in input_outputs:
            o.entrypoint_uuid = entry.uuid

        if input_outputs:
            db.bulk_save_objects(input_outputs)
            db.flush()

        # (3) Create Block
        cb = Block(
            name=name,
            project_uuid=project_id,
            custom_name=custom_name,
            description=description,
            author=author,
            docker_image=docker_image,
            cbc_url=repo_url,
            x_pos=x_pos,
            y_pos=y_pos,
            selected_entrypoint_uuid=entry.uuid
        )
        db.add(cb)
        db.flush()

        db.refresh(entry)
        logging.info(f"Compute block created succesfully: {cb.uuid}")
        return cb
    except Exception as e:
        logging.error(f"Error creating compute block: {e}")
        raise e


def get_envs_for_entrypoint(e_id: UUID) -> ConfigType | None:
    db: Session = next(get_database())

    e = db.query(Entrypoint).filter_by(uuid=e_id).one_or_none()

    if not e:
        return HTTPException(status_code=404, detail="Entrypoint not found.")

    return e.envs


def get_ios_by_ids(
        ids: list[UUID]
) -> list[InputOutput]:
    db: Session = next(get_database())

    return db.query(InputOutput).filter(InputOutput.uuid.in_(ids)).all()


def get_io_for_entrypoint(
        e_id: UUID,
        io_type: InputOutputType | None
) -> list[InputOutput]:
    db: Session = next(get_database())

    return db.query(InputOutput).filter_by(
        entrypoint_uuid=e_id,
        type=io_type
    ).all()


def get_compute_blocks_by_project(project_id: UUID) -> list[Block]:
    db: Session = next(get_database())

    order_case = case(
        (InputOutput.data_type == DataType.FILE, 1),
        (InputOutput.data_type == DataType.PGTABLE, 2),
        (InputOutput.data_type == DataType.CUSTOM, 3),
        else_=4
    )

    blocks = (
        db.query(Block)
        .join(Block.selected_entrypoint)
        .outerjoin(Entrypoint.input_outputs)
        .filter(Block.project_uuid == project_id)
        .order_by(order_case, asc(InputOutput.name))
        .options(
            contains_eager(Block.selected_entrypoint)
            .contains_eager(Entrypoint.input_outputs)
        )
        .all()
    )

    return blocks


def get_block_dependencies_for_blocks(
    block_ids: list[UUID]
) -> list:
    db: Session = next(get_database())

    query = select(
        block_dependencies.c.upstream_block_uuid,
        block_dependencies.c.upstream_output_uuid,
        block_dependencies.c.downstream_block_uuid,
        block_dependencies.c.downstream_input_uuid
    ).where(
        block_dependencies.c.upstream_block_uuid.in_(block_ids) |
        block_dependencies.c.downstream_block_uuid.in_(block_ids)
    )

    # Fetch the dependencies
    return db.execute(query).fetchall()


def do_config_keys_match(
    config_type: Literal["envs", "io"],
    original_config: ConfigType,
    update_config: ConfigType,
) -> bool:
    """
    Check if the keys in the original config and update config are the same.
    If not, returns False.
    """
    original_keys = set(original_config.keys())
    update_keys = set(update_config.keys())

    # Check if all update keys are in the original config keys
    invalid_keys = update_keys - original_keys
    if invalid_keys:
        logging.debug(f"Invalid keys found for {
                      config_type}:")
        logging.debug(f"Original {config_type} keys: {original_keys}")
        logging.debug(f"Updated {config_type} keys: {update_keys}")
        logging.debug(f"Invalid keys: {invalid_keys}")
        return False
    return True


def _update_io(
    db: Session,
    io: InputOutput,
    new_config: ConfigType
) -> list[UUID]:
    """
    Returns a list of IO uuids that were automatically updated (downstreams).
    """
    logging.debug(f"Updating IO with id: {io.uuid}")

    if do_config_keys_match("io", io.config, new_config):
        io.config = {**io.config, **new_config}
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Config Keys of io with id {io.uuid} do not match."
        )

    # Only Update Outputs of type File & PgTable
    if (
        io.type != InputOutputType.OUTPUT and
        (io.data_type != DataType.FILE
         or io.data_type != DataType.PGTABLE)
    ):
        return []

    dep = db.execute(
        select(block_dependencies.c.downstream_input_uuid)
        .where(
            block_dependencies.c.upstream_output_uuid == io.uuid
        )
    ).fetchall()
    downstream_inputs = [row[0] for row in dep]
    if not downstream_inputs:
        return []

    downstream_ios = db.query(InputOutput).filter(
        InputOutput.uuid.in_(downstream_inputs)
    ).all()
    logging.debug(f"Updating connected input configs: {downstream_ios}.")

    # Apply the same config update to connected inputs
    # We are sure here that the downstream has the same type
    updated_downstream_ids = []
    for downstream_io in downstream_ios:
        update_dict = extract_default_keys_from_io(io)
        downstream_io.config = updated_configs_with_values(
            downstream_io, update_dict, downstream_io.data_type
        )
        updated_downstream_ids.append(downstream_io.uuid)
        logging.debug(f"Updated input config with id {
            downstream_io.uuid}")

    return updated_downstream_ids


def update_ios(
    update_dict: dict[UUID, ConfigType]
) -> list[InputOutput]:
    logging.debug("Updating input/outputs.")

    db: Session = next(get_database())

    with db.begin():
        ids = list(update_dict.keys())
        ios = db.query(InputOutput).filter(InputOutput.uuid.in_(ids)).all()

        if len(ios) == 0:
            raise HTTPException(
                status_code=400, detail="Provided Inputs do not exist.")

        for io in ios:
            updated_downstreams = _update_io(db, io, update_dict.get(io.uuid))
            ids.extend(updated_downstreams)

        logging.info("Input/Output updates committed successfully.")

    updated = db.query(InputOutput).filter(
        InputOutput.uuid.in_(set(ids))).all()
    return updated


def update_block(
    id: UUID,
    envs: ConfigType | None,
    custom_name: str | None,
    x_pos: float | None,
    y_pos: float | None
) -> Block:
    db: Session = next(get_database())

    block = db.query(Block).filter_by(uuid=id).one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found.")

    if custom_name:
        block.custom_name = custom_name

    if envs:
        if do_config_keys_match(
            "envs",
            block.selected_entrypoint.envs,
            envs
        ):
            block.selected_entrypoint.envs = {
                **block.selected_entrypoint.envs, **envs}
        else:
            raise HTTPException(
                status_code=422,
                detail="Env-Keys do not match."
            )

    if x_pos is not None:
        block.x_pos = x_pos

    if y_pos is not None:
        block.y_pos = y_pos

    db.commit()
    db.refresh(block)

    return block


def delete_block(
    id: UUID
):
    logging.debug(f"Deleting Compute Block with id: {id}")
    db: Session = next(get_database())

    block = db.query(Block).filter_by(uuid=id).one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found.")

    db.delete(block)
    db.commit()
    logging.info(f"Successfully deleted Compute Block with id {id}")


def create_stream_and_update_target_cfg(
    from_block_uuid: UUID,
    from_output_uuid: UUID,
    to_block_uuid: UUID,
    to_input_uuid: UUID,
) -> UUID:
    logging.debug(f"""
                  Create Edge from block {from_block_uuid} output
                  {from_output_uuid} to block {to_block_uuid} input
                  {to_input_uuid}
                  """)
    db: Session = next(get_database())

    with db.begin():
        dependency = {
            "upstream_block_uuid": from_block_uuid,
            "upstream_output_uuid": from_output_uuid,
            "downstream_block_uuid": to_block_uuid,
            "downstream_input_uuid": to_input_uuid,
        }

        db.execute(block_dependencies.insert().values(dependency))

        # Compare the cfgs, overwrite the cfgs
        target_io = db.query(InputOutput).filter_by(
            uuid=to_input_uuid).one_or_none()
        source_io = db.query(InputOutput).filter_by(
            uuid=from_output_uuid).one_or_none()

        if target_io.data_type != source_io.data_type:
            # Data types do not match, dont allow connection
            logging.error(f"Input datatype {
                target_io.data_type} does not match with \
                                     output type {target_io.data_type}")
            raise HTTPException(
                status_code=400,
                detail="Source & Target types do not match"
            )

        # Custom inputs are not overwritten
        if (
                (target_io.data_type != source_io.data_type) or
                (target_io.data_type is DataType.CUSTOM)
        ):
            logging.info("Edge from custom output to input created.")
            return target_io.uuid

        logging.debug(f"Updating Input {to_input_uuid} configs.")
        extracted_defaults = extract_default_keys_from_io(
            source_io
        )
        target_io.config = updated_configs_with_values(
            target_io, extracted_defaults, target_io.data_type)

        return target_io.entrypoint_uuid


def delete_edge(
    from_block_uuid: UUID,
    from_output_uuid: UUID,
    to_block_uuid: UUID,
    to_input_uuid: UUID,
):
    logging.debug(f"Deleting Edge from block {
        from_block_uuid} output {from_output_uuid} to \
                         {to_block_uuid} with input {to_input_uuid}.")
    db: Session = next(get_database())

    stmt = delete(block_dependencies).where(
        block_dependencies.c.upstream_block_uuid == from_block_uuid,
        block_dependencies.c.upstream_output_uuid == from_output_uuid,
        block_dependencies.c.downstream_block_uuid == to_block_uuid,
        block_dependencies.c.downstream_input_uuid == to_input_uuid,
    )

    db.execute(stmt)
    db.commit()
