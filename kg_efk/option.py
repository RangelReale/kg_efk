from typing import Optional, Any, Mapping

from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.option import OptionDef, OptionDefFormat
from kubragen.options import Options


class EFKOptions(Options):
    """
    Options for the EFK builder.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - basename
          - object names prefix
          - str
          - ```efk```
        * - namespace
          - namespace
          - str
          - ```default```
        * - config |rarr| elasticsearch_replicas
          - number of elasticsearch replicas
          - int
          - ```3```
        * - config |rarr| probes
          - whether to enable liveness / rediness probes
          - bool
          - ```True```
        * - config |rarr| kkibana_service_port
          - Kibana service port
          - int
          - ```80```
        * - config |rarr| authorization |rarr| serviceaccount_create
          - whether to create a service account
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| serviceaccount_use
          - service account to use if not creating
          - str
          -
        * - config |rarr| authorization |rarr| roles_create
          - whether create roles
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| roles_bind
          - whether to bind roles to service account
          - bool
          - ```True```
        * - enable |rarr| kibana
          - whether to enable the kibana deployment
          - bool
          - ```True```
        * - container |rarr| elasticsearch
          - elasticsearch container image
          - str
          - ```docker.elastic.co/elasticsearch/elasticsearch:<version>```
        * - container |rarr| kibana
          - kibana container image
          - str
          - ```docker.elastic.co/kibana/kibana:<version>```
        * - container |rarr| fluentd
          - fluentd container image
          - str
          - ```fluent/fluentd-kubernetes-daemonset:<version>```
        * - kubernetes |rarr| volumes |rarr| elasticsearch-data
          - Elasticsearch Kubernetes data volume
          - Mapping, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          -
        * - kubernetes |rarr| resources |rarr| elasticsearch-statefulset
          - Elasticsearch Kubernetes StatefulSet resources
          - Mapping
          -
        * - kubernetes |rarr| resources |rarr| kibana-deployment
          - Kibana Kubernetes Deployment resources
          - Mapping
          -
        * - kubernetes |rarr| resources |rarr| fluentd-daemonset
          - Fluentd Kubernetes DaemonSet resources
          - Mapping
          -
    """
    def define_options(self) -> Optional[Any]:
        """
        Declare the options for the EFK builder.

        :return: The supported options
        """
        return {
            'basename': OptionDef(required=True, default_value='efk', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='default', allowed_types=[str]),
            'config': {
                'elasticsearch_replicas': OptionDef(required=True, default_value=3, allowed_types=[int]),
                'probes': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                'kibana_service_port': OptionDef(required=True, default_value=80, allowed_types=[int]),
                'authorization': {
                    'serviceaccount_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                    'roles_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'roles_bind': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                },
            },
            'enable': {
                'kibana': OptionDef(required=True, default_value=True, allowed_types=[bool]),
            },
            'container': {
                'elasticsearch': OptionDef(required=True, default_value='docker.elastic.co/elasticsearch/elasticsearch:7.9.3', allowed_types=[str]),
                'kibana': OptionDef(required=True, default_value='docker.elastic.co/kibana/kibana:7.9.3', allowed_types=[str]),
                'fluentd': OptionDef(required=True, default_value='fluent/fluentd-kubernetes-daemonset:v1.11.4-debian-elasticsearch7-1.0', allowed_types=[str]),
            },
            'kubernetes': {
                'volumes': {
                    'elasticsearch-data': OptionDef(required=True, format=OptionDefFormat.KDATA_VOLUME,
                                                    allowed_types=[Mapping, *KDataHelper_Volume.allowed_kdata()]),
                },
                'resources': {
                    'elasticsearch-statefulset': OptionDef(allowed_types=[Mapping]),
                    'kibana-deployment': OptionDef(allowed_types=[Mapping]),
                    'fluentd-daemonset': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
