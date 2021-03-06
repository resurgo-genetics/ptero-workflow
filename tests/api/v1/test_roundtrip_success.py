from ..base import BaseAPITest
from tests.util import shell_command_url
import abc
import difflib
import json
import sys
import base64
import uuid


class RoundTripSuccess(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(RoundTripSuccess, self).setUp()
        self.response = self.post(self.post_url, self.post_data)

    def tearDown(self):
        url = self.response.headers.get('Location')
        delete_response = self.delete(url)
        self.assertEqual(200, delete_response.status_code)
        super(RoundTripSuccess, self).tearDown()

    def test_roundtrip(self):
        self.should_return_201()
        self.should_set_location_header()
        self.get_should_return_post_data()

    def should_return_201(self):
        self.assertEqual(201, self.response.status_code)

    def should_set_location_header(self):
        self.assertIsNotNone(self.response.headers.get('Location'))

    def get_should_return_post_data(self):
        get_response = self.get(self.response.DATA['reports']['workflow-submission-data'])
        del(get_response.DATA['status'])
        if self.post_data.get('name') is None:
            del(get_response.DATA['name'])
        self.assertTrue(self.compareDictAsJSON(expected=self.post_data,
            actual=get_response.DATA))

    def _to_json(self, data):
        return json.dumps( data, indent=4, sort_keys=True, default=str )

    def compareDictAsJSON(self, expected, actual):
        is_ok = 1
        expected_json = self._to_json(expected).splitlines(1)
        actual_json = self._to_json(actual).splitlines(1)
        from pprint import pprint
        pprint(actual_json)
        for line in difflib.unified_diff(expected_json, actual_json,
                fromfile='Expected', tofile='Actual'):
            is_ok = 0
            sys.stdout.write(line)
        return is_ok

    def webhook_url(self, name):
        # this url should always respond with a status-code that does not
        # get retried.
        return self.post_url + '?webhook_name=%s' % name


class WorkflowWithConvergeOperation(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'Converge': {
                        'methods': [
                            {
                                'name': 'converger',
                                'service': 'workflow-converge',
                                'parameters': {
                                    'input_names': ['b', 'a'],
                                    'output_name': 'c',
                                    }
                                }
                            ]
                        },
                    },
                'links': [
                    {
                        'source': 'Converge',
                        'destination': 'output connector',
                        'dataFlow': {
                            'c': 'result',
                            },
                        }, {
                            'source': 'input connector',
                            'destination': 'Converge',
                            'dataFlow': {
                                'in_a': 'a',
                                'in_b': 'b',
                                },
                            },
                        ],
                'inputs': {
                    'in_a': 'kittens',
                    'in_b': 'puppies',
                    },
                }


class WorkflowWithBlockOperation(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'Block': {
                        'methods': [
                            {
                                'name': 'blocker',
                                'service': 'workflow-block',
                                'parameters': {
                                    }
                                }
                            ]
                        },
                    },
                'links': [
                    {
                        'source': 'Block',
                        'destination': 'output connector',
                        'dataFlow': {
                            'result': 'result',
                            },
                        }, {
                            'source': 'input connector',
                            'destination': 'Block',
                            'dataFlow': {
                                'in_a': 'in_a',
                                },
                            },
                        ],
                'inputs': {
                    'in_a': 'kittens',
                    },
                }


class SingleNodeWorkflow(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
            'tasks': {
                'A': {
                    'methods': [
                        {
                            'name': 'execute',
                            'service': 'job',
                            'serviceUrl': shell_command_url(),
                            'parameters': {
                                'commandLine': ['cat'],
                                'user': 'testuser',
                                'workingDirectory': '/test/working/directory'
                            }
                        }
                    ]
                },
            },
            'links': [
                {
                    'source': 'A',
                    'destination': 'output connector',
                    'dataFlow': {
                        'result': 'out_a',
                    },
                }, {
                    'source': 'input connector',
                    'destination': 'A',
                    'dataFlow': {
                        'in_a': 'param',
                    },
                },
            ],
            'inputs': {
                'in_a': 'kittens',
            },
        }


def _generate_uuid():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]

unique_name = _generate_uuid()


class MinimalNamedWorkflow(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    },
                'links': [
                    {
                        'source': 'input connector',
                        'destination': 'output connector',
                        'dataFlow': {
                            'in_a': 'out_a',
                            },
                        },
                    ],
                'inputs': {
                    'in_a': 'kittens',
                    },
                'name': unique_name,
                }


class NestedWorkflowWithWebhooks(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
        'webhooks': {
            'running': self.webhook_url('outer_dag'),
            'errored': [self.webhook_url('outer_dag'), self.webhook_url('outer_dag_2')]
        },
        'tasks': {
            'Inner': {
                'webhooks': {
                    'running': self.webhook_url('outer_task'),
                    'errored': [self.webhook_url('outer_task'), self.webhook_url('outer_task_2')]
                },
                'methods': [{
                    'name': 'some_workflow',
                    'webhooks': {
                        'running': self.webhook_url('inner_dag'),
                        'errored': [self.webhook_url('inner_dag'), self.webhook_url('inner_dag_2')]
                    },
                    'parameters': {
                        'tasks': {
                            'A': {
                                'webhooks': {
                                    'running': self.webhook_url('inner_task'),
                                    'errored': [self.webhook_url('inner_task'), self.webhook_url('inner_task_2')]
                                },
                                'methods': [
                                    {
                                        'name': 'execute',
                                        'service': 'job',
                                        'serviceUrl': shell_command_url(),
                                        'parameters': {
                                            'commandLine': ['cat'],
                                            'user': 'testuser',
                                            'workingDirectory': '/test/working/directory',
                                            'webhooks': {
                                                'running': self.webhook_url('shell_command'),
                                                'errored': [self.webhook_url('shell_command'), self.webhook_url('shell_command_2')]
                                            },
                                        }
                                    }
                                ]
                            },
                        },
                        'links': [
                            {
                                'source': 'A',
                                'destination': 'output connector',
                                'dataFlow': {
                                    'result': 'inner_output',
                                },
                            }, {
                                'source': 'input connector',
                                'destination': 'A',
                                'dataFlow': {
                                    'inner_input': 'param',
                                },
                            },
                        ],
                    },
                    'service': 'workflow',
                }]
            },
        },

        'links': [
            {
                'source': 'Inner',
                'destination': 'output connector',
                'dataFlow': {
                    'inner_output': 'outer_output',
                },
            }, {
                'source': 'input connector',
                'destination': 'Inner',
                'dataFlow': {
                    'outer_input': 'inner_input',
                },
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
    }


class NestedWorkflow(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'Inner': {
                        'methods': [{
                            'name': 'some_workflow',
                            'parameters': {
                                'tasks': {
                                    'A': {
                                        'methods': [
                                            {
                                                'name': 'execute',
                                                'service': 'job',
                                                'serviceUrl': shell_command_url(),
                                                'parameters': {
                                                    'commandLine': ['cat'],
                                                    'user': 'testuser',
                                                    'workingDirectory': '/test/working/directory'
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                'links': [
                                    {
                                        'source': 'A',
                                        'destination': 'output connector',
                                        'dataFlow': {
                                            'result': 'inner_output',
                                            },
                                        }, {
                                            'source': 'input connector',
                                            'destination': 'A',
                                            'dataFlow': {
                                                'inner_input': 'param',
                                                },
                                            },
                                        ],
                                },
                            'service': 'workflow',
                            }]
                        },
                    },

                'links': [
                    {
                        'source': 'Inner',
                        'destination': 'output connector',
                        'dataFlow': {
                            'inner_output': 'outer_output',
                            },
                        }, {
                            'source': 'input connector',
                            'destination': 'Inner',
                            'dataFlow': {
                                'outer_input': 'inner_input',
                                },
                            },
                        ],
                'inputs': {
                        'outer_input': 'kittens',
                        },
                }


class ParallelByTaskWorkflow(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'A': {
                        'methods': [
                            {
                                'name': 'execute',
                                'service': 'job',
                                'serviceUrl': shell_command_url(),
                                'parameters': {
                                    'commandLine': ['cat'],
                                    'user': 'testuser',
                                    'workingDirectory': '/test/working/directory'
                                    }
                                }
                            ]
                        },
                    },
                'links': [
                    {
                        'source': 'A',
                        'destination': 'output connector',
                        'dataFlow': {
                            'result': 'out_a',
                            },
                        }, {
                            'source': 'input connector',
                            'destination': 'A',
                            'dataFlow': {
                                'in_a': 'param',
                                },
                            },
                        ],
                'inputs': {
                    'in_a': 'kittens',
                    },
                }


class NestedParallelByTaskWorkflow(RoundTripSuccess, BaseAPITest):
    @property
    def post_data(self):
        return {
                'tasks': {
                    'Inner': {
                        'methods': [{
                            'name': 'some_workflow',
                            'parameters': {
                                'tasks': {
                                    'A': {
                                        'methods': [
                                            {
                                                'name': 'execute',
                                                'service': 'job',
                                                'serviceUrl': shell_command_url(),
                                                'parameters': {
                                                    'commandLine': ['cat'],
                                                    'user': 'testuser',
                                                    'workingDirectory': '/test/working/directory'
                                                    }
                                                }
                                            ]
                                        },
                                    },
                                'links': [
                                    {
                                        'source': 'A',
                                        'destination': 'output connector',
                                        'dataFlow': {
                                            'result': 'inner_output',
                                            },
                                        }, {
                                            'source': 'input connector',
                                            'destination': 'A',
                                            'dataFlow': {
                                                'inner_input': 'param',
                                                },
                                            },
                                        ],
                                },
                            'service': 'workflow',
                            }],
                        },
                    },

                'links': [
                    {
                        'source': 'Inner',
                        'destination': 'output connector',
                        'dataFlow': {
                            'inner_output': 'outer_output',
                            },
                        }, {
                            'source': 'input connector',
                            'destination': 'Inner',
                            'dataFlow': {
                                'outer_input': 'inner_input',
                                },
                            },
                        ],
                'inputs': {
                        'outer_input': 'kittens',
                        },
                }
