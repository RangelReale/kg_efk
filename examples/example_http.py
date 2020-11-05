from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print, OutputDriver_Directory
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
# SETUP: efk
#
efk_config = EFKBuilder(kubragen=kg, options=EFKOptions({
    'basename': 'efk',
    'namespace': 'default',
    'kubernetes': {
        'volumes': {
            'elasticsearch-data': {
                'emptyDir': {},
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
# OUTPUTFILE: http-echo.yaml
#
file = OutputFile_Kubernetes('http-echo.yaml')
out.append(file)

file.append([{
    'apiVersion': 'apps/v1',
    'kind': 'Deployment',
    'metadata': {
        'name': 'echo-deployment',
        'labels': {
            'app': 'echo'
        }
    },
    'spec': {
        'replicas': 1,
        'selector': {
            'matchLabels': {
                'app': 'echo'
            }
        },
        'template': {
            'metadata': {
                'labels': {
                    'app': 'echo'
                }
            },
            'spec': {
                'containers': [{
                    'name': 'echo',
                    'image': 'mendhak/http-https-echo',
                    'ports': [{
                        'containerPort': 80
                    },
                    {
                        'containerPort': 443
                    }]
                }]
            }
        }
    }
},
{
    'apiVersion': 'v1',
    'kind': 'Service',
    'metadata': {
        'name': 'echo-service'
    },
    'spec': {
        'selector': {
            'app': 'echo'
        },
        'ports': [{
            'name': 'http',
            'port': 80,
            'targetPort': 80,
            'protocol': 'TCP'
        }]
    }
}])

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory(r'M:\prog\tests\temp'))
