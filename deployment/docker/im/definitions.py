from mysql_conf import *
import json
import requests
from datetime import datetime,timedelta
from kubernetes import client,config
from pint import UnitRegistry

ureg = UnitRegistry()

# Memory units
ureg.define('kmemunits = 1 = [kmemunits]')
ureg.define('Ki = 1024 * kmemunits')
ureg.define('Mi = Ki^2')
ureg.define('Gi = Ki^3')
ureg.define('Ti = Ki^4')
ureg.define('Pi = Ki^5')
ureg.define('Ei = Ki^6')

# cpu units
ureg.define('kcpuunits = 1 = [kcpuunits]')
ureg.define('n = 1/1000000000 * kcpuunits')
ureg.define('u = 1/1000000 * kcpuunits')
ureg.define('m = 1/1000 * kcpuunits')
ureg.define('k = 1000 * kcpuunits')
ureg.define('M = k^2')
ureg.define('G = k^3')
ureg.define('T = k^4')
ureg.define('P = k^5')
ureg.define('E = k^6')

Q_ = ureg.Quantity

def core_v1():
    config.load_incluster_config()
    return client.CoreV1Api()

def getEnablers():
    pods = core_v1().list_namespaced_pod(namespace='default')
    enablers = []
    for item in pods.items:
        if 'enabler' in item.metadata.labels:
            enabler = item.metadata.labels['enabler']
            if not enabler in enablers:
                enablers.append(enabler)
    return enablers

def getComponents(enabler):
    pods = core_v1().list_namespaced_pod(namespace='default')
    components = []
    for item in pods.items:
        if 'enabler' in item.metadata.labels and enabler == item.metadata.labels['enabler']:
            if 'app.kubernetes.io/component' in item.metadata.labels and not item.metadata.labels['app.kubernetes.io/component'] in components:
                component = item.metadata.labels['app.kubernetes.io/component']
                components.append(component)
    return components

def getEnabler(e):
    try:
      enablerObject = enabler.get(enabler.name == e)
      return enablerObject
    except enabler.DoesNotExist:
      return None

def getComponent(e,c):
    try:
      componentObject = component.get((component.enabler_id == e) & (component.name == c))
      return componentObject
    except component.DoesNotExist:
      return None

def getDeployments():
	config.load_incluster_config()
	v1 = client.AppsV1Api()
	list_deploy = v1.list_namespaced_deployment(namespace='default')
	list = []
	for deploy in list_deploy.items:
		if not 'enabler' in deploy.spec.template.metadata.labels:
			continue
		cpu = 0
		ram = 0
		for container in deploy.spec.template.spec.containers:
			if container.resources.requests:
				cpu += int(Q_(container.resources.requests['cpu']).to('m').magnitude)
				ram += int(Q_(container.resources.requests['memory']).to('Mi').magnitude)
		dict = {
			'deployment_name': deploy.metadata.name,
			'enabler_name': deploy.spec.template.metadata.labels['enabler'],
			'component_name': deploy.spec.template.metadata.labels['app.kubernetes.io/component'],
			'cpu': cpu,
			'ram': ram
		}
		list.append(dict)
	return list

def getDeployment(en,comp,deployments):
	for deploy in deployments:
		if (deploy['enabler_name'] == en.name and deploy['component_name'] == comp.name):
			return deploy
	return None

def getReplicas(deploy,comp):
	curr = datetime.now().replace(second=0, microsecond=0)
	fut = hist = curr + timedelta(minutes=15)
	query = data.select().where((data.component_id == comp.id) & (data.timestamp > curr) & (data.timestamp <= fut))
	if query: 
		cpu,ram = query[0].cpu,query[0].ram
	else: 
		cpu,ram = 0,0
	requests_cpu = int(deploy['cpu'])
	requests_ram = int(deploy['ram'])
	avg = 0.75
	if requests_cpu == 0 and requests_ram == 0:
		return 1,1
	else:
		min_replicas_cpu = int(cpu/(requests_cpu+1)/avg)+1
		min_replicas_ram = int(ram/(requests_ram+1)/avg)+1
		min_replicas = min(10,max(min_replicas_cpu,min_replicas_ram))
		max_replicas = min_replicas+3
		return min_replicas,max_replicas

def body_horizontalpodautoscaler(enabler,component,min_replicas,max_replicas):
	# Configurate HPA template

	# Configurate target
    target = client.V2beta2MetricTarget(
		type = 'Utilization',
		average_utilization = 75
	)

	# Configurate metric source
    resourceCPU = client.V2beta2ResourceMetricSource(
		name = 'cpu',
		target = target
	)

    resourceRAM = client.V2beta2ResourceMetricSource(
		name = 'memory',
		target = target
	)

	# Configurate metrics
    my_metrics = []

    metricsCPU = client.V2beta2MetricSpec(
		type = 'Resource',
		resource = resourceCPU
	)
    my_metrics.append(metricsCPU)

    metricsRAM = client.V2beta2MetricSpec(
		type = 'Resource',
		resource = resourceRAM
	)
    my_metrics.append(metricsRAM)

	# Configurate scale_target_ref
    scale_target_ref = client.V2beta2CrossVersionObjectReference(
		api_version = 'apps/v1',
		kind = 'Deployment', 
		name = enabler+'-'+component
	)

    # Create the specification of horizontal pod autoscaler
    spec = client.V2beta2HorizontalPodAutoscalerSpec(
        scale_target_ref = scale_target_ref,
		min_replicas = min_replicas,
		max_replicas = max_replicas,
		metrics = my_metrics
    )

	# Instantiate the horizontal pod autoscaler object
    body = client.V2beta2HorizontalPodAutoscaler(
		api_version = 'autoscaling/v2beta2',
		kind = 'HorizontalPodAutoscaler',
		metadata = client.V1ObjectMeta(
			name=enabler+'-'+component+'-hpa',
			labels = {
    			'enabler': enabler,
				'app.kubernetes.io/component': component
			}),
		spec = spec
	)
    return body

def list_horizontalpodautoscaler():
	config.load_incluster_config()
	v2 = client.AutoscalingV2beta2Api()
	query = v2.list_namespaced_horizontal_pod_autoscaler(namespace='default')
	list = []
	for q in query.items:
		list.append(q.spec.scale_target_ref.name)
	return list

def create_or_replace_horizontalpodautoscaler(enabler,component,min_replicas,max_replicas,list):
	if min_replicas == 1 and max_replicas == 1:
		return 0
	config.load_incluster_config()
	v2 = client.AutoscalingV2beta2Api()
	body = body_horizontalpodautoscaler(enabler,component,min_replicas,max_replicas)
	name = enabler+'-'+component
	if not name in list:
		ret = v2.create_namespaced_horizontal_pod_autoscaler(namespace='default', body=body, pretty=True)
	else:
		ret = v2.patch_namespaced_horizontal_pod_autoscaler(name=name+'-hpa',namespace='default', body=body, pretty=True)
	return ret

def delete_horizontalpodautoscaler(enabler,component,list):
	name = enabler+'-'+component
	if not name in list: return 0
	config.load_incluster_config()
	v2 = client.AutoscalingV2beta2Api()
	ret = v2.delete_namespaced_horizontal_pod_autoscaler(name=name+'-hpa',namespace='default',pretty=True)
	return ret
