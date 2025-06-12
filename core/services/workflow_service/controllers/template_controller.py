from fastapi import HTTPException
from uuid import UUID, uuid4
import networkx as nx
import logging

from sqlalchemy.orm import Session
from services.workflow_service.schemas.compute_block import (
    ConfigType,
)
from services.workflow_service.schemas.workflow import (
    WorkflowTemplate,
    Block as BlockTemplate,
    Input as InputTemplate,
    Output as OutputTemplate,
)
from scystream.sdk.config.models import (
    ComputeBlock,
    Entrypoint as SDKEntrypoint,
    InputOutputModel
)
from services.workflow_service.models.block import (
    Block
)
from services.workflow_service.models.input_output import (
    InputOutput, InputOutputType, DataType
)
from services.workflow_service.controllers.compute_block_controller import (
    updated_configs_with_values, do_config_keys_match, create_compute_block,
    create_stream_and_update_target_cfg
)
from utils.config.defaults import (
    get_file_cfg_defaults_dict,
    get_pg_cfg_defaults_dict,
)


def extract_block_urls_from_template(template: WorkflowTemplate) -> list[str]:
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


def build_workflow_graph(template: WorkflowTemplate):
    """
    Parses the Workflow Template into a Networkx DAG and
    assigns positions for the workbench.
    """

    G = nx.DiGraph()

    for block in template.blocks:
        G.add_node(block.name, block=block)

    for block in template.blocks:
        for inp in block.inputs or []:
            if inp.depends_on:
                from_block = inp.depends_on.block
                to_block = block.name
                G.add_edge(
                    from_block,
                    to_block,
                    input_identifier=inp.identifier,
                    output_identifier=inp.depends_on.output
                )
    if not nx.is_directed_acyclic_graph(G):
        raise HTTPException(
            status_code=422, detail="Template defines a cyclic dependency.")

    # Assigning Positions
    level_map = {}
    y_offsets = {}

    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        level = 0 if not preds else 1 + max(level_map[p] for p in preds)
        level_map[node] = level

        y_index = y_offsets.get(level, 0)
        y_offsets[level] = y_index + 1

        x_pos = level * 500
        y_pos = y_index * 400

        G.nodes[node]["position"] = (x_pos, y_pos)
        G.nodes[node]["level"] = level

    return G


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
        uuid=uuid4(),
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
                    status_code=421,
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
        configured_envs = {**envs, **(envs_from_template or {})}
    else:
        raise HTTPException(
            status_code=421,
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


def configure_and_create_blocks(
    G: nx.DiGraph,
    db: Session,
    unconfigured_blocks: dict[str, ComputeBlock],
    project_id: UUID
) -> tuple[
    dict[str, Block],
    dict[str, dict[str, UUID]],
    dict[str, dict[str, UUID]]
]:
    """
    Configures and creates blocks defined in the template graph.

    Parameters:
        :G: nx.Digraph -> A DAG that contains information
            from the parsed template
        :db: Session -> Transactional DB session
        :unconfigured_blocks: -> Mapping repo_url to the block
            definitions from the cbc.yaml

    Returns:
        :dict[str, Block]: Mapping of block names from templates
            to their database model instance
        :dict[str, [str, UUID]]: Mapping of block names from
            templates to their outputs database uuids
        :dict[str, [str, UUID]]: Mapping of block names from
            templates to their inputs database uuids
    """
    block_name_to_model = {}
    block_outputs_by_name = {}
    block_inputs_by_name = {}

    for block_name in nx.topological_sort(G):
        block_template = G.nodes[block_name]["block"]
        # 1. Validate wether Template Definition of Compute Block is correct
        compute_block = unconfigured_blocks.get(
            block_template.repo_url
        )
        if compute_block is None:
            raise HTTPException(
                status_code=422,
                detail=f"Block repo '{block_template.repo_url}' not found."
            )

        entrypoint = compute_block.entrypoints.get(block_template.entrypoint)
        if entrypoint is None:
            raise HTTPException(
                status_code=422,
                detail=f"Entrypoint '{block_template.entrypoint}' not found in\
                        block '{block_template.name}'."
            )

        # 2. Configure the Block
        configured_envs, inputs, outputs = _configure_block(
            block_template, entrypoint
        )

        # 3. Create the Block
        x_pos, y_pos = G.nodes[block_name]["position"]
        created_block = create_compute_block(
            db,
            compute_block.name,
            compute_block.description,
            compute_block.author,
            compute_block.docker_image,
            block_template.repo_url,
            block_template.name,
            x_pos,
            y_pos,
            entry_name=block_template.entrypoint,
            entry_description=compute_block.description,
            envs=configured_envs,
            inputs=inputs,
            outputs=outputs,
            project_id=project_id
        )

        # 4. Create the maps that "connect" template to database representation
        # We use them to create the edges in the database
        block_name_to_model[block_template.name] = created_block
        block_outputs_by_name[block_template.name] = {
            o.name: o.uuid for o in outputs
        }
        block_inputs_by_name[block_template.name] = {
            i.name: i.uuid for i in inputs
        }

    return block_name_to_model, block_outputs_by_name, block_inputs_by_name


def create_edges_from_template(
    G: nx.DiGraph,
    db: Session,
    block_name_to_model: dict[str, Block],
    block_outputs_by_name: dict[str, dict[str, UUID]],
    block_inputs_by_name: dict[str, dict[str, UUID]],
) -> dict[tuple[UUID, UUID], tuple[UUID, UUID]]:
    """
    This method create the edges using the template graph..
    """
    for from_block, to_block, edge_data in G.edges(data=True):
        input_identifier = edge_data["input_identifier"]
        output_identifier = edge_data["output_identifier"]

        downstream_block = block_name_to_model[to_block]
        upstream_block = block_name_to_model[from_block]

        input_uuid = block_inputs_by_name[to_block].get(input_identifier)
        output_uuid = block_outputs_by_name[from_block].get(output_identifier)

        if input_uuid is None or output_uuid is None:
            raise HTTPException(
                status_code=422,
                detail=f"""
                    Dependency resolution failed for edge:
                    "{from_block} -> {to_block}
                    "({output_identifier}-> {input_identifier})
                """
            )

        create_stream_and_update_target_cfg(
            db,
            upstream_block.uuid,
            output_uuid,
            downstream_block.uuid,
            input_uuid
        )
