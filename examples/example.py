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
