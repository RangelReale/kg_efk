import unittest

from kubragen import KubraGen
from kubragen.jsonpatch import FilterJSONPatches_Apply, ObjectFilter, FilterJSONPatch
from kubragen.provider import Provider_Generic

from kg_efk import EFKBuilder, EFKOptions


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.kg = KubraGen(provider=Provider_Generic())

    def test_empty(self):
        efk_config = EFKBuilder(kubragen=self.kg, options=EFKOptions({
            'kubernetes': {
                'volumes': {
                    'elasticsearch-data': {
                        'emptyDir': {},
                    }
                }
            }
        }))
        self.assertEqual(efk_config.object_name('elasticsearch-service'), 'efk-elasticsearch')
        self.assertEqual(efk_config.object_name('fluentd-daemonset'), 'efk-fluentd')

    def test_basedata(self):
        efk_config = EFKBuilder(kubragen=self.kg, options=EFKOptions({
            'namespace': 'myns',
            'basename': 'myefk',
            'kubernetes': {
                'volumes': {
                    'elasticsearch-data': {
                        'emptyDir': {},
                    }
                }
            }
        }))

        self.assertEqual(efk_config.object_name('elasticsearch-service'), 'myefk-elasticsearch')
        self.assertEqual(efk_config.object_name('fluentd-daemonset'), 'myefk-fluentd')

        FilterJSONPatches_Apply(items=efk_config.build(efk_config.BUILD_SERVICE), jsonpatches=[
            FilterJSONPatch(filters=ObjectFilter(names=[efk_config.BUILDITEM_ELASTICSEARCH_SERVICE]), patches=[
                {'op': 'check', 'path': '/metadata/name', 'cmp': 'equals', 'value': 'myefk-elasticsearch'},
                {'op': 'check', 'path': '/metadata/namespace', 'cmp': 'equals', 'value': 'myns'},
            ]),
        ])
