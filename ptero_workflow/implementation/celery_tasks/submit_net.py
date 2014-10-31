from .. import models
from .. import tasks
from .. import translator
import celery
import os
import requests
import simplejson


__all__ = ['SubmitNet']


class SubmitNet(celery.Task):
    ignore_result = True

    def run(self, workflow_id):
        session = celery.current_app.Session()

        workflow = session.query(models.Workflow).get(workflow_id)

        petri_data = translator.build_petri_net(workflow)
        response_data = self._submit_net(petri_data)

        workflow.net_key = response_data['net_key']
        session.commit()

        self.http.delay('POST',
                response_data['entry_links'][workflow.start_place_name])

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_workflow.implementation.celery_tasks.http.HTTP']

    def _submit_net(self, petri_data):
        response = requests.post(self._petri_submit_url,
                data=simplejson.dumps(petri_data),
                headers={'Content-Type': 'application/json'})
        return response.json()

    @property
    def _petri_submit_url(self):
        return 'http://%s:%d/v1/nets' % (
            os.environ.get('PTERO_PETRI_HOST', 'localhost'),
            int(os.environ.get('PTERO_PETRI_PORT', 80)),
        )
