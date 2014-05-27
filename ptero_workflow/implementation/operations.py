from . import exceptions
from . import models


__all__ = ['create_operation']


def _build_model_operation(operation_data, operation):
    _validate_model_operation_data(operation_data)

    for name, child_operation_data in operation_data['operations'].iteritems():
        create_operation(name=name, operation_data=child_operation_data,
                parent=operation)

    create_operation(name='input connector',
            operation_data={'type': 'input connector'}, parent=operation)
    create_operation(name='output connector',
            operation_data={'type': 'output connector'}, parent=operation)

    for link_data in operation_data['links']:
        source = operation.children[link_data['source']]
        destination = operation.children[link_data['destination']]
        models.Link(
            destination_operation=destination,
            destination_property=link_data['destination_property'],
            parallel_by=link_data.get('parallel_by', False),
            source_operation=source,
            source_property=link_data['source_property'],
        )


def _build_parallel_by_operation(operation_data, operation):
    operation.parallel_by = operation_data['parallel_by']


_OP_BUILDERS = {
    'model': _build_model_operation,
    'parallel-by-pass-through': _build_parallel_by_operation,
    'parallel-by-command': _build_parallel_by_operation,
}
def _build_operation(operation_data, operation):
    _operation_builder = _OP_BUILDERS.get(operation.type)
    if _operation_builder:
        _operation_builder(operation_data, operation=operation)


def _validate_model_operation_data(operation_data):
    if 'input connector' in operation_data['operations']:
        raise exceptions.InvalidWorkflow(
                "'input connector' is a reserved operation name")

    if 'output connector' in operation_data['operations']:
        raise exceptions.InvalidWorkflow(
                "'output connector' is a reserved operation name")

def _get_operation_type(operation_data):
    return operation_data['type'].lower()


def create_operation(name, operation_data, parent=None):
    op_type = _get_operation_type(operation_data)

    operation = models.Operation.from_dict(name=name, type=op_type)
    if parent is not None:
        parent.children[name] = operation

    _build_operation(operation_data, operation=operation)

    return operation

def create_input_holder(root, inputs):
    operation = models.InputHolderOperation(name='input_holder')
    operation.set_outputs(inputs)
    for i in inputs.iterkeys():
        models.Link(source_operation=operation, destination_operation=root,
                source_property=i, destination_property=i)
    return operation