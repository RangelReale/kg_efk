from typing import Optional, Sequence

from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.consts import PROVIDER_K3D, PROVIDER_K3S
from kubragen.data import ValueData
from kubragen.exception import InvalidParamError, InvalidNameError
from kubragen.helper import QuotedStr
from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.object import ObjectItem, Object
from kubragen.types import TBuild, TBuildItem

from .option import EFKOptions


class EFKBuilder(Builder):
    """
    EFK builder.

    Based on `How To Set Up an Elasticsearch, Fluentd and Kibana (EFK) Logging Stack on Kubernetes <https://www.digitalocean.com/community/tutorials/how-to-set-up-an-elasticsearch-fluentd-and-kibana-efk-logging-stack-on-kubernetes>`_.

    .. list-table::
        :header-rows: 1

        * - build
          - description
        * - BUILD_ACCESSCONTROL
          - creates service account, roles, and roles bindings
        * - BUILD_SERVICE
          - creates StatefulSet and Services

    .. list-table::
        :header-rows: 1

        * - build item
          - description
        * - BUILDITEM_SERVICE_ACCOUNT
          - ServiceAccount
        * - BUILDITEM_ELASTICSEARCH_SERVICE
          - Elasticsearch Service
        * - BUILDITEM_ELASTICSEARCH_STATEFULSET
          - Elasticsearch StatefulSet
        * - BUILDITEM_KIBANA_DEPLOYMENT
          - Kibana Deployment
        * - BUILDITEM_KIBANA_SERVICE
          - Kibana Service
        * - BUILDITEM_FLUENTD_CLUSTER_ROLE
          - Fluentd Cluster Role
        * - BUILDITEM_FLUENTD_CLUSTER_ROLE_BINDING
          - Fluentd Cluster Role Binding
        * - BUILDITEM_FLUENTD_DAEMONSET
          - Fluentd Daemonset

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - service-account
          - ServiceAccount
          - ```<basename>```
        * - elasticsearch-service
          - Elasticsearch Service
          - ```<basename>-elasticsearch```
        * - elasticsearch-statefulset
          - Elasticsearch StatefulSet
          - ```<basename>-elasticsearch```
        * - elasticsearch-pod-label-all
          - Elasticsearch label *app* to be used by selection
          - ```<basename>-elasticsearch```
        * - kibana-service
          - Kibana Service
          - ```<basename>-kibana```
        * - kibana-deployment
          - Kibana Deployment
          - ```<basename>-kibana```
        * - kibana-pod-label-all
          - Kibana label *app* to be used by selection
          - ```<basename>-kibana```
        * - fluentd-cluster-role
          - Fluentd ClusterRole
          - ```<basename>-fluentd```
        * - fluentd-cluster-role-binding
          - Fluentd ClusterRoleBinding
          - ```<basename>-fluentd```
        * - fluentd-deployment
          - Fluentd Deployment
          - ```<basename>-fluentd```
        * - fluentd-pod-label-all
          - Fluentd label *app* to be used by selection
          - ```<basename>-fluentd```
    """
    options: EFKOptions
    configfile: Optional[str]
    _namespace: str

    SOURCE_NAME = 'kg_efk'

    BUILD_ACCESSCONTROL: TBuild = 'accesscontrol'
    BUILD_SERVICE: TBuild = 'service'

    BUILDITEM_SERVICE_ACCOUNT: TBuildItem = 'service-account'
    BUILDITEM_ELASTICSEARCH_SERVICE: TBuildItem = 'elasticsearch-service'
    BUILDITEM_ELASTICSEARCH_STATEFULSET: TBuildItem = 'elasticsearch-statefulset'
    BUILDITEM_KIBANA_DEPLOYMENT: TBuildItem = 'kibana-deployment'
    BUILDITEM_KIBANA_SERVICE: TBuildItem = 'kibana-service'
    BUILDITEM_FLUENTD_CLUSTER_ROLE: TBuildItem = 'fluentd-cluster-role'
    BUILDITEM_FLUENTD_CLUSTER_ROLE_BINDING: TBuildItem = 'fluentd-cluster-role-binding'
    BUILDITEM_FLUENTD_DAEMONSET: TBuildItem = 'fluentd-daemonset'

    def __init__(self, kubragen: KubraGen, options: Optional[EFKOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = EFKOptions()
        self.options = options
        self.configfile = None

        self._namespace = self.option_get('namespace')

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            serviceaccount_name = self.basename()
        else:
            serviceaccount_name = self.option_get('config.authorization.serviceaccount_use')
            if serviceaccount_name == '':
                serviceaccount_name = None

        if self.option_get('config.authorization.roles_bind') is not False:
            if serviceaccount_name is None:
                raise InvalidParamError('To bind roles a service account is required')

        self.object_names_update({
            'service-account': serviceaccount_name,
            'elasticsearch-service': self.basename('-elasticsearch'),
            'elasticsearch-statefulset': self.basename('-elasticsearch'),
            'elasticsearch-pod-label-app': self.basename('-elasticsearch'),
            'fluentd-cluster-role': self.basename('-fluentd'),
            'fluentd-cluster-role-binding': self.basename('-fluentd'),
            'fluentd-daemonset': self.basename('-fluentd'),
            'fluentd-pod-label-app': self.basename('-fluentd'),
        })
        if self.option_get('enable.kibana'):
            self.object_names_update({
                'kibana-service': self.basename('-kibana'),
                'kibana-deployment': self.basename('-kibana'),
                'kibana-pod-label-app': self.basename('-kibana'),
            })

    def option_get(self, name: str):
        return self.kubragen.option_root_get(self.options, name)

    def basename(self, suffix: str = ''):
        return '{}{}'.format(self.option_get('basename'), suffix)

    def namespace(self):
        return self._namespace

    def build_names(self) -> Sequence[TBuild]:
        return [self.BUILD_ACCESSCONTROL, self.BUILD_SERVICE]

    def build_names_required(self) -> Sequence[TBuild]:
        ret = [self.BUILD_SERVICE]
        if self.option_get('config.authorization.serviceaccount_create') is not False or \
                self.option_get('config.authorization.roles_create') is not False:
            ret.append(self.BUILD_ACCESSCONTROL)
        return ret

    def builditem_names(self) -> Sequence[TBuildItem]:
        return [
            self.BUILDITEM_SERVICE_ACCOUNT,
            self.BUILDITEM_ELASTICSEARCH_SERVICE,
            self.BUILDITEM_ELASTICSEARCH_STATEFULSET,
            self.BUILDITEM_KIBANA_DEPLOYMENT,
            self.BUILDITEM_KIBANA_SERVICE,
            self.BUILDITEM_FLUENTD_CLUSTER_ROLE,
            self.BUILDITEM_FLUENTD_CLUSTER_ROLE_BINDING,
            self.BUILDITEM_FLUENTD_DAEMONSET,
        ]

    def internal_build(self, buildname: TBuild) -> Sequence[ObjectItem]:
        if buildname == self.BUILD_ACCESSCONTROL:
            return self.internal_build_accesscontrol()
        elif buildname == self.BUILD_SERVICE:
            return self.internal_build_service()
        else:
            raise InvalidNameError('Invalid build name: "{}"'.format(buildname))

    def internal_build_accesscontrol(self) -> Sequence[ObjectItem]:
        ret = []

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'v1',
                    'kind': 'ServiceAccount',
                    'metadata': {
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }
                }, name=self.BUILDITEM_SERVICE_ACCOUNT, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        if self.option_get('config.authorization.roles_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'kind': 'ClusterRole',
                    'metadata': {
                        'name': self.object_name('fluentd-cluster-role'),
                    },
                    'rules': [{
                        'apiGroups': [''],
                        'resources': ['pods', 'namespaces'],
                        'verbs': ['get', 'list', 'watch']
                    }]
                }, name=self.BUILDITEM_FLUENTD_CLUSTER_ROLE, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        if self.option_get('config.authorization.roles_bind') is not False:
            ret.extend([
                Object({
                    'kind': 'ClusterRoleBinding',
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'metadata': {
                        'name': self.object_name('fluentd-cluster-role-binding'),
                    },
                    'roleRef': {
                        'kind': 'ClusterRole',
                        'name': self.object_name('fluentd-cluster-role'),
                        'apiGroup': 'rbac.authorization.k8s.io'
                    },
                    'subjects': [{
                        'kind': 'ServiceAccount',
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }]
                }, name=self.BUILDITEM_FLUENTD_CLUSTER_ROLE_BINDING, source=self.SOURCE_NAME, instance=self.basename())
            ])

        return ret

    def internal_build_service(self) -> Sequence[ObjectItem]:
        ret = []

        ret.extend([
            Object({
                'kind': 'Service',
                'apiVersion': 'v1',
                'metadata': {
                    'name': self.object_name('elasticsearch-service'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('elasticsearch-pod-label-app'),
                    }
                },
                'spec': {
                    'selector': {
                        'app': self.object_name('elasticsearch-pod-label-app'),
                    },
                    'clusterIP': 'None',
                    'ports': [{
                        'port': 9200,
                        'name': 'rest'
                    }, {
                        'port': 9300,
                        'name': 'inter-node'
                    }],
                }
            }, name=self.BUILDITEM_ELASTICSEARCH_SERVICE, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'apps/v1',
                'kind': 'StatefulSet',
                'metadata': {
                    'name': self.object_name('elasticsearch-statefulset'),
                    'namespace': self.namespace(),
                },
                'spec': {
                    'serviceName': self.object_name('elasticsearch-service'),
                    'replicas': self.option_get('config.elasticsearch_replicas'),
                    'selector': {
                        'matchLabels': {
                            'app': self.object_name('elasticsearch-pod-label-app'),
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': self.object_name('elasticsearch-pod-label-app'),
                            }
                        },
                        'spec': {
                            'volumes': [
                                KDataHelper_Volume.info(base_value={
                                    'name': 'data',
                                }, value=self.option_get('kubernetes.volumes.elasticsearch-data')),
                            ],
                            'containers': [{
                                'name': 'elasticsearch',
                                'image': self.option_get('container.elasticsearch'),
                                'ports': [{
                                    'containerPort': 9200,
                                    'name': 'rest',
                                    'protocol': 'TCP'
                                },
                                {
                                    'containerPort': 9300,
                                    'name': 'inter-node',
                                    'protocol': 'TCP'
                                }],
                                'volumeMounts': [{
                                    'name': 'data',
                                    'mountPath': '/usr/share/elasticsearch/data'
                                }],
                                'env': [{
                                    'name': 'cluster.name',
                                    'value': self.object_name('elasticsearch-statefulset'),
                                },
                                # {
                                #     'name': 'node.name',
                                #     'valueFrom': {
                                #         'fieldRef': {
                                #             'fieldPath': 'metadata.name'
                                #         }
                                #     },
                                # },
                                {
                                    'name': 'NODE_NAME',
                                    'valueFrom': {
                                        'fieldRef': {
                                            'fieldPath': 'metadata.name'
                                        }
                                    },
                                },
                                {
                                    'name': 'node.name',
                                    'value': QuotedStr('$(NODE_NAME).{}'.format(self.object_name('elasticsearch-service'))),
                                },
                                {
                                    'name': 'discovery.seed_hosts',
                                    'value': ','.join(['{}-{}.{}'.format(
                                        self.object_name('elasticsearch-statefulset'), rpl, self.object_name('elasticsearch-service'))
                                        for rpl in range(self.option_get('config.elasticsearch_replicas'))
                                    ]),
                                },
                                {
                                    'name': 'cluster.initial_master_nodes',
                                    'value': ','.join(['{}-{}.{}'.format(
                                        self.object_name('elasticsearch-statefulset'), rpl, self.object_name('elasticsearch-service'))
                                        for rpl in range(self.option_get('config.elasticsearch_replicas'))
                                    ]),
                                },
                                {
                                    'name': 'ES_JAVA_OPTS',
                                    'value': '-Xms512m '
                                             '-Xmx512m'
                                }],
                                'resources': ValueData(value=self.option_get('kubernetes.resources.elasticsearch-statefulset'),
                                                       disabled_if_none=True),
                            }],
                            'initContainers': [{
                                'name': 'fix-permissions',
                                'image': 'busybox',
                                'command': [
                                    'sh',
                                    '-c',
                                    'chown -R '
                                    '1000:1000 '
                                    '/usr/share/elasticsearch/data'
                                ],
                                'securityContext': {
                                    'privileged': True
                                },
                                'volumeMounts': [{
                                    'name': 'data',
                                    'mountPath': '/usr/share/elasticsearch/data'
                                }],
                            },
                            {
                                'name': 'increase-vm-max-map',
                                'image': 'busybox',
                                'command': [
                                    'sysctl',
                                    '-w',
                                    'vm.max_map_count=262144'
                                ],
                                'securityContext': {
                                    'privileged': True
                                },
                            },
                            {
                                'name': 'increase-fd-ulimit',
                                'image': 'busybox',
                                'command': [
                                    'sh',
                                    '-c',
                                    'ulimit -n '
                                    '65536'
                                ],
                                'securityContext': {
                                    'privileged': True
                                },
                            }]
                        }
                    },
                }
            }, name=self.BUILDITEM_ELASTICSEARCH_STATEFULSET, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'apps/v1',
                'kind': 'DaemonSet',
                'metadata': {
                    'name': self.object_name('fluentd-daemonset'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('fluentd-pod-label-app'),
                    }
                },
                'spec': {
                    'selector': {
                        'matchLabels': {
                            'app': self.object_name('fluentd-pod-label-app'),
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': self.object_name('fluentd-pod-label-app'),
                            }
                        },
                        'spec': {
                            'serviceAccount': self.object_name('service-account'),
                            'serviceAccountName': self.object_name('service-account'),
                            'tolerations': [{
                                'key': 'node-role.kubernetes.io/master',
                                'effect': 'NoSchedule'
                            }],
                            'containers': [{
                                'name': 'fluentd',
                                'image': self.option_get('container.fluentd'),
                                'env': [{
                                    'name': 'FLUENT_ELASTICSEARCH_HOST',
                                    'value': '{}.{}.svc.cluster.local'.format(self.object_name('elasticsearch-service'), self.namespace()),
                                },
                                {
                                    'name': 'FLUENT_ELASTICSEARCH_PORT',
                                    'value': '9200'
                                },
                                {
                                    'name': 'FLUENT_ELASTICSEARCH_SCHEME',
                                    'value': 'http'
                                },
                                {
                                    'name': 'FLUENTD_SYSTEMD_CONF',
                                    'value': 'disable'
                                },
                                ValueData(value={
                                    'name': 'FLUENT_CONTAINER_TAIL_PARSER_TYPE',
                                    'value': '/^(?<time>.+) (?<stream>stdout|stderr) [^ ]* (?<log>.*)$/',
                                }, enabled=self.kubragen.provider.provider == PROVIDER_K3D or self.kubragen.provider.provider == PROVIDER_K3S)],
                                'volumeMounts': [{
                                    'name': 'varlog',
                                    'mountPath': '/var/log'
                                },
                                {
                                    'name': 'varlibdockercontainers',
                                    'mountPath': '/var/lib/docker/containers',
                                    'readOnly': True
                                }],
                                'resources': ValueData(value=self.option_get('kubernetes.resources.fluentd-daemonset'),
                                                       disabled_if_none=True),

                            }],
                            'terminationGracePeriodSeconds': 30,
                            'volumes': [{
                                'name': 'varlog',
                                'hostPath': {
                                    'path': '/var/log'
                                }
                            },
                            {
                                'name': 'varlibdockercontainers',
                                'hostPath': {
                                    'path': '/var/lib/docker/containers'
                                }
                            }]
                        }
                    }
                }
            }, name=self.BUILDITEM_FLUENTD_DAEMONSET, source=self.SOURCE_NAME, instance=self.basename()),
        ])

        if self.option_get('enable.kibana'):
            ret.extend([
                Object({
                    'apiVersion': 'v1',
                    'kind': 'Service',
                    'metadata': {
                        'name': self.object_name('kibana-service'),
                        'namespace': self.namespace(),
                        'labels': {
                            'app': self.object_name('kibana-pod-label-app'),
                        },
                    },
                    'spec': {
                        'ports': [{
                            'port': 5601
                        }],
                        'selector': {
                            'app': self.object_name('kibana-pod-label-app'),
                        }
                    }
                }, name=self.BUILDITEM_KIBANA_SERVICE, source=self.SOURCE_NAME, instance=self.basename()),
                Object({
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'metadata': {
                        'name': self.object_name('kibana-deployment'),
                        'namespace': self.namespace(),
                        'labels': {
                            'app': self.object_name('kibana-pod-label-app'),
                        }
                    },
                    'spec': {
                        # 'replicas': 1,
                        'selector': {
                            'matchLabels': {
                                'app': self.object_name('kibana-pod-label-app'),
                            }
                        },
                        'template': {
                            'metadata': {
                                'labels': {
                                    'app': self.object_name('kibana-pod-label-app'),
                                }
                            },
                            'spec': {
                                'containers': [{
                                    'name': 'kibana',
                                    'image': self.option_get('container.kibana'),
                                    'env': [{
                                        'name': 'ELASTICSEARCH_HOSTS',
                                        'value': 'http://{}:9200'.format(self.object_name('elasticsearch-service')),
                                    }],
                                    'ports': [{
                                        'containerPort': 5601
                                    }],
                                    'livenessProbe': ValueData(value={
                                        'httpGet': {
                                            'path': '/api/status',
                                            'port': 5601,
                                        },
                                        'initialDelaySeconds': 30,
                                        'timeoutSeconds': 20,
                                    }, enabled=self.option_get('config.probes')),
                                    'readinessProbe': ValueData(value={
                                        'httpGet': {
                                            'path': '/api/status',
                                            'port': 5601,
                                        },
                                        'initialDelaySeconds': 30,
                                        'timeoutSeconds': 20,
                                    }, enabled=self.option_get('config.probes')),
                                    'resources': ValueData(
                                        value=self.option_get('kubernetes.resources.kibana-deployment'),
                                        disabled_if_none=True),
                                }]
                            }
                        }
                    }
                }, name=self.BUILDITEM_KIBANA_DEPLOYMENT, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        return ret
