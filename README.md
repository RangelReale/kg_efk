# KubraGen Builder: EFK (Elasticsearch, Fluentd, Kibana)

[![PyPI version](https://img.shields.io/pypi/v/kg_efk.svg)](https://pypi.python.org/pypi/kg_efk/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/kg_efk.svg)](https://pypi.python.org/pypi/kg_efk/)

kg_efk is a builder for [KubraGen](https://github.com/RangelReale/kubragen) that deploys 
a [EFK](https://www.efk.com/) stack in Kubernetes. (Elasticsearch, Fluentd, Kibana)

[KubraGen](https://github.com/RangelReale/kubragen) is a Kubernetes YAML generator library that makes it possible to generate
configurations using the full power of the Python programming language.

* Website: https://github.com/RangelReale/kg_efk
* Repository: https://github.com/RangelReale/kg_efk.git
* Documentation: https://kg_efk.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/kg_efk

## Example

```python
from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_efk import EFKBuilder, EFKOptions

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: efk
#
efk_config = EFKBuilder(kubragen=kg, options=EFKOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'myefk',
    'kubernetes': {
        'volumes': {
            'elasticsearch-data': {
                'persistentVolumeClaim': {
                    'claimName': 'efk-storage-claim'
                }
            }
        },
    }
}))

efk_config.ensure_build_names(efk_config.BUILD_ACCESSCONTROL, efk_config.BUILD_SERVICE)

#
# OUTPUTFILE: efk-config.yaml
#
file = OutputFile_Kubernetes('efk-config.yaml')
out.append(file)

file.append(efk_config.build(efk_config.BUILD_ACCESSCONTROL))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# OUTPUTFILE: efk.yaml
#
file = OutputFile_Kubernetes('efk.yaml')
out.append(file)

file.append(efk_config.build(efk_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-efk-config.yaml ********
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myefk
  namespace: app-monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: myefk-fluentd
rules:
- apiGroups: ['']
  resources: [pods, namespaces]
  verbs: [get, list, watch]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: myefk-fluentd
roleRef:
  kind: ClusterRole
  name: myefk-fluentd
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: myefk
  namespace: app-monitoring

****** END FILE: 002-efk-config.yaml ********
****** BEGIN FILE: 003-efk.yaml ********
kind: Service
apiVersion: v1
metadata:
  name: myefkelasticsearch-service
  namespace: app-monitoring
  labels:
    app: myefkelasticsearch-pod-label-app
spec:
  selector:
    app: myefkelasticsearch-pod-label-app
  clusterIP: None
  ports:
  - port: 9200
    name: rest
  - port: 9300
    name: inter-node
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: myefk-elasticsearch
  namespace: app-monitoring
spec:
  serviceName: myefk-elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: myefk-elasticsearch
  template:
    metadata:
      labels:
        app: myefk-elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.2.0
<...more...>
****** END FILE: 003-efk.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-efk-config.yaml
kubectl apply -f 003-efk.yaml

****** END FILE: create_gke.sh ********
```

## Credits

based on

[How To Set Up an Elasticsearch, Fluentd and Kibana (EFK) Logging Stack on Kubernetes](https://www.digitalocean.com/community/tutorials/how-to-set-up-an-elasticsearch-fluentd-and-kibana-efk-logging-stack-on-kubernetes)

## Author

Rangel Reale (rangelreale@gmail.com)
