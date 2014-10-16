from .task_base import Task
from sqlalchemy import Column, ForeignKey, Integer


__all__ = ['InputConnector']


class InputConnector(Task):
    __tablename__ = 'input_connector'

    id = Column(Integer, ForeignKey('task.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    def get_source_task_and_name(self, output_param_name):
        task, name = self.parent.get_input_task_and_name(output_param_name)
        return task.get_source_task_and_name(name)

    def attach_subclass_transitions(self, transitions, start_place):
        return start_place, None
