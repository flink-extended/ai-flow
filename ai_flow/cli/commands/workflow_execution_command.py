


@init_config
def workflow_list_executions(args):
    """Lists all workflow executions of the workflow by workflow name."""
    workflow_executions = list_workflow_executions(args.workflow_name)
    AIFlowConsole().print_as(
        data=sorted(workflow_executions, key=lambda w: w.workflow_execution_id),
        output=args.output,
        mapper=lambda x: {
            'workflow_execution_id': x.workflow_execution_id,
            'workflow_name': x.workflow_info.workflow_name,
            'status': x.status,
            'properties': x.properties,
            'start_date': parse_date(x.start_date),
            'end_date': parse_date(x.end_date),
            'context': x.context
        },
    )


@init_config
def workflow_show_execution(args):
    """Shows the workflow execution by workflow execution id."""
    workflow_execution = get_workflow_execution(args.workflow_execution_id)
    AIFlowConsole().print_as(
        data=[workflow_execution],
        output=args.output,
        mapper=lambda x: {
            'workflow_execution_id': x.workflow_execution_id,
            'workflow_name': x.workflow_info.workflow_name,
            'status': x.status,
            'properties': x.properties,
            'start_date': parse_date(x.start_date),
            'end_date': parse_date(x.end_date),
            'context': x.context
        },
    )


@init_config
def workflow_start_execution(args):
    """Starts a new workflow execution by workflow name."""
    workflow_execution = start_new_workflow_execution(args.workflow_name, args.context)
    print("Workflow: {}, started: {}.".format(args.workflow_name, workflow_execution is not None))

