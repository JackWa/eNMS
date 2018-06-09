from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from time import sleep


from eNMS import db
from eNMS.base.helpers import get_obj
from eNMS.base.models import CustomBase
from eNMS.base.properties import cls_to_properties


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    source_id = Column(Integer, ForeignKey('InnerTask.id'))
    source = relationship(
        'InnerTask',
        primaryjoin='InnerTask.id == WorkflowEdge.source_id',
        backref='destinations'
    )
    destination_id = Column(Integer, ForeignKey('InnerTask.id'))
    destination = relationship(
        'InnerTask',
        primaryjoin='InnerTask.id == WorkflowEdge.destination_id'
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship('Workflow', back_populates='edges')

    def __init__(self, type, source, destination):
        self.type = type
        self.source = source
        self.destination = destination
        self.name = '{} -> {}'.format(self.source.name, self.destination.name)

    @property
    def serialized(self):
        properties = {
            'name': self.name,
            'type': self.type,
            'source': self.source.serialized,
            'destination': self.destination.serialized
        }
        return properties

class Workflow(CustomBase):

    __tablename__ = 'Workflow'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    vendor = Column(String)
    operating_system = Column(String)
    tasks = relationship('ScheduledWorkflowTask', back_populates='workflow')
    inner_tasks = relationship('InnerTask', back_populates='workflow')
    edges = relationship('WorkflowEdge', back_populates='workflow')
    # start_task_id = Column(Integer, ForeignKey('InnerTask.id'))

    properties = (
        'name',
        'description',
        'type'
    )

    def __init__(self, **kwargs):
        for property in self.properties:
            setattr(self, property, kwargs[property])

    @property
    def serialized(self):
        properties = {p: str(getattr(self, p)) for p in cls_to_properties['Workflow']}
        for prop in ('tasks', 'inner_tasks', 'edges'):
            properties[prop] = [obj.serialized for obj in getattr(self, prop)]
        return properties

    def run(self):
        layer, visited = {self.start_task}, set()
        while layer:
            new_layer = set()
            for task in layer:
                visited.add(task)
                task_results = {}
                success = task.job([task, node, task_results])
                edge_type = 'success' if success else 'failure'
                results[task.name] = task_results
                for neighbor in task.task_neighbors(self, edge_type):
                    if neighbor not in visited:
                        new_layer.add(neighbor)
                sleep(task.waiting_time)
            layer = new_layer


def workflow_factory(**kwargs):
    workflow = get_obj(Workflow, name=kwargs['name'])
    if workflow:
        for property, value in kwargs.items():
            if property in workflow.__dict__:
                setattr(workflow, property, value)
    else:
        workflow = Workflow(**kwargs)
    db.session.add(workflow)
    db.session.commit()
    return workflow
