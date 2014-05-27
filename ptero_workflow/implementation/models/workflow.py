from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import logging
import simplejson


__all__ = ['Workflow']


LOG = logging.getLogger(__file__)


class Workflow(Base):
    __tablename__ = 'workflow'

    id          = Column(Integer, primary_key=True)
    environment = Column(Text)

    root_operation_id = Column(Integer,
            ForeignKey('operation.id'), nullable=False)

    root_operation = relationship('Operation', backref='workflow',
            foreign_keys=[root_operation_id])

    input_holder_operation_id = Column(Integer,
            ForeignKey('operation.id'), nullable=False)

    input_holder_operation = relationship('InputHolderOperation',
            foreign_keys=[input_holder_operation_id])

    net_key = Column(Text, unique=True)

    @property
    def start_place_name(self):
        return self.root_operation.ready_place_name

    @property
    def links(self):
        results = []

        for name,op in self.operations.iteritems():
            results.extend(op.input_links)

        return results

    @property
    def operations(self):
        return self.root_operation.children

    @property
    def as_dict(self):
        ops = {name: op.as_dict for name,op in self.operations.iteritems()
                if name not in ['input connector', 'output connector']}
        links = [l.as_dict for l in self.links]
        data = {
            'operations': ops,
            'links': links,
            'inputs': self.root_operation.children['input connector'].get_outputs(),
            'outputs': self.root_operation.get_outputs(),
            'environment': simplejson.loads(self.environment),
        }
        if self.root_operation.status is not None:
            data['status'] = self.root_operation.status
        return data