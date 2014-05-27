from .base import Base
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import backref, relationship
import logging


__all__ = ['Link']


LOG = logging.getLogger(__file__)


class Link(Base):
    __tablename__ = 'link'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('operation.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('operation.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_by = Column(Boolean, nullable=False, default=False)

    source_operation = relationship('Operation',
            backref=backref('output_links'),
            foreign_keys=[source_id])

    destination_operation = relationship('Operation',
            backref=backref('input_links'),
            foreign_keys=[destination_id])

    @property
    def as_dict(self):
        data = {
            'source': self.source_operation.name,
            'destination': self.destination_operation.name,
            'source_property': self.source_property,
            'destination_property': self.destination_property,
        }

        if self.parallel_by:
            data['parallel_by'] = True

        return data