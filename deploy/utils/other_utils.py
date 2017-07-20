import collections
import logging
import os
import sys
import time
import subprocess

from deploy.utils.constants import BASE_DIR
from deploy.utils.servctl_utils import load_settings

logger = logging.getLogger()


def retrieve_settings(deployment_label):
    settings = collections.OrderedDict()

    settings['STARTED_VIA_SERVCTL'] = True
    settings['TIMESTAMP'] = time.strftime("%Y%m%d_%H%M%S")
    settings['HOME'] = os.path.expanduser("~")

    load_settings([
        os.path.join(BASE_DIR, "kubernetes/settings/shared-settings.yaml"),
        os.path.join(BASE_DIR, "kubernetes/settings/%(deployment_label)s-settings.yaml" % locals())
    ], settings)

    return settings


def check_kubernetes_context(deployment_label):
    # make sure the environment is configured to use a local kube-solo cluster, and not gcloud or something else
    try:
        cmd = 'kubectl config current-context'
        kubectl_current_context = subprocess.check_output(cmd, shell=True).strip()
    except subprocess.CalledProcessError as e:
        logger.error('Error while running "kubectl config current-context": %s', e)
        #i = raw_input("Continue? [Y/n] ")
        #if i != 'Y' and i != 'y':
        #    sys.exit('Exiting...')
        return

    if deployment_label == "local":
        if kubectl_current_context != 'kube-solo':
            logger.error(("'%(cmd)s' returned '%(kubectl_current_context)s'. For %(deployment_label)s deployment, this is "
                         "expected to equal 'kube-solo'. Please configure your shell environment "
                         "to point to a local kube-solo cluster by installing "
                         "kube-solo from https://github.com/TheNewNormal/kube-solo-osx, starting the kube-solo VM, "
                         "and then clicking on 'Preset OS Shell' in the kube-solo menu to launch a pre-configured shell.") % locals())
            sys.exit(-1)

    elif deployment_label.startswith("gcloud"):
        suffix = deployment_label.split("-")[-1]  # "dev" or "prod"
        if not kubectl_current_context.startswith('gke_') or not kubectl_current_context.endswith(suffix):
            logger.error(("'%(cmd)s' returned '%(kubectl_current_context)s' which doesn't match %(deployment_label)s. "
                         "To fix this, run:\n\n   "
                         "gcloud container clusters get-credentials <cluster-name>\n\n"
                         "Using one of these clusters: " + subprocess.check_output("gcloud container clusters list", shell=True) +
                         "\n\n") % locals())
            sys.exit(-1)
    else:
        raise ValueError("Unexpected value for deployment_label: %s" % deployment_label)


def lookup_json_path(resource_type="pod", labels={}, json_path=".items[0].metadata.name"):
    """Runs 'kubectl get <resource_type> | grep <component>' command to retrieve the full name of this resource.

    Args:
        component (string): keyword to use for looking up a kubernetes entity (eg. 'phenotips' or 'nginx')
        labels (dict):
        json_path (string):
    Returns:
        (string) resource value (eg. "postgres-410765475-1vtkn")
    """

    l_args = " ".join(['-l %s=%s' % (key, value) for key, value in labels.items()])
    output = subprocess.check_output("kubectl get %(resource_type)s %(l_args)s -o jsonpath={%(json_path)s}" % locals(), shell=True)
    output = output.strip('\n')

    return output
