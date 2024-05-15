#!/usr/bin/python3

from datetime import datetime, timedelta
from io import BufferedRandom
from definitions import *

def inference():

    deployments = getDeployments()
    enablers = getEnablers()
    list = list_horizontalpodautoscaler()
    for en in enablers:
        enabler = getEnabler(en)
        if not enabler: continue
        components = getComponents(en)
        for comp in components:
            component = getComponent(enabler.id,comp)
            if not component: continue
            if enabler.infer and component.infer:
                deploy = getDeployment(enabler,component,deployments)
                if not deploy: continue
                min_replicas,max_replicas = getReplicas(deploy,component)
                create_or_replace_horizontalpodautoscaler(enabler.name,component.name,min_replicas,max_replicas,list)
            else:
                delete_horizontalpodautoscaler(enabler.name,component.name,list)
        return 'Inference complete sucessfully'