from kubernetes import client, config
from peewee import *
from mysql_conf import *
import json
import requests
from datetime import datetime, timedelta
import json
import yaml

api_port = os.environ['API_PORT']
tm = os.environ['TM_HOST']
tm_port = os.environ['TM_PORT']
im = os.environ['IM_HOST']
im_port = os.environ['IM_PORT']

def version():
    headers = ['enabler','version']
    data = [os.environ['ENABLER_NAME'],os.environ['ENABLER_VERSION']]
    return dict(zip(headers,data))

def health():
    health_status = True
    if (requests.get('http://{}:{}/health'.format(tm,tm_port)).status_code != 200 or
        requests.get('http://{}:{}/health'.format(im,im_port)).status_code != 200 ):
        health_status = False
    return health_status

def apiexport():
    f = open('openapi.yaml')
    data = yaml.load(f, Loader=yaml.Loader)
    return data

def createTables():
    enabler.create_table()
    component.create_table()
    data.create_table()

def core_v1():
    config.load_incluster_config()
    return client.CoreV1Api()

def apps_v1():
    config.load_incluster_config()
    return client.AppsV1Api()

def getMetrics():
    config.load_incluster_config()
    cust = client.CustomObjectsApi()
    dict = cust.list_namespaced_custom_object(
        'metrics.k8s.io', 'v1beta1', 'default', 'pods')
    return dict

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

def getDeployments(enabler):
    deploy = apps_v1().list_namespaced_deployment(namespace='default')
    deployments = []
    for item in deploy.items:
        if 'enabler' in item.metadata.labels and enabler == item.metadata.labels['enabler']:
            if 'app.kubernetes.io/component' in item.metadata.labels:
                deployments.append(item.metadata.name)
    return deployments

def enablers():
    enablers = getEnablers()
    data = {"enablers" : []}
    for en in enablers:
        enabler = getInferEnabler(en)
        if enabler is None: continue
        components = getComponents(en)
        compList = []
        for comp in components:
            component = getInferComponent(enabler.id,comp)
            if component is None: continue
            compData = {
                "name": comp,
                "managed": component.infer
            }
            compList.append(compData)
        enablerData = {
            "name": en,
            "managed": enabler.infer,
            "components": compList
        }
        data["enablers"].append(enablerData)
    return data

def enablerspost(jsonData):
    data = json.loads(json.dumps(jsonData))
    keys = dict(data).keys()
    if not 'enablers' in keys: return 'Invalid JSON'
    for en in data['enablers']:
        keys = dict(en).keys()
        if not ('name' or 'managed' or 'components') in keys: return 'Invalid JSON'
        if type(en['managed']) is not bool: return 'managed enabler must be true or false'
        try:
            enablerData = enabler.get(enabler.name == en['name'])
        except enabler.DoesNotExist:
            continue
        if (not en['managed'] and not enablerData.infer): continue
        elif (not en['managed'] and enablerData.infer): enablerVal = {'infer': False}
        else: enablerVal = {'infer': True}
        for comp in en['components']:
            keys = dict(comp).keys()
            if not ('name' or 'managed') in keys: return 'Invalid JSON'
            if type(comp['managed']) is not bool: return 'managed components must be true or false'
            try:
                componentData = component.get((component.enabler_id == enablerData.id) & (component.name == comp['name']))
            except component.DoesNotExist:
                continue
            if not en['managed']: componentVal = {'infer': False}
            else: componentVal = {'infer': comp['managed']}
            up = component.update(**componentVal).where(component.enabler_id==enablerData.id,component.name==componentData.name)
            up.execute()
        up = enabler.update(**enablerVal).where(enabler.id==enablerData.id)
        up.execute()
    return 'Enablers managed updates sucessfully'

def getInferEnabler(e):
    try:
      enablerObject = enabler.get(enabler.name == e)
      return enablerObject
    except enabler.DoesNotExist:
      return None

def getInferComponent(e,c):
    try:
      componentObject = component.get((component.enabler_id == e) & (component.name == c))
      return componentObject
    except component.DoesNotExist:
      return None

def addEnablers():
    enablers = getEnablers()
    data = {"enablers" : []}
    for en in enablers:
        components = getComponents(en)
        compList = []
        for comp in components:
            compData = {
                "name": comp,
                "managed": component.infer
            }
            compList.append(compData)
        enablerData = {
            "name": en,
            "managed": enabler.infer,
            "components": compList
        }
        data["enablers"].append(enablerData)
    for d in data['enablers']:
        keys = dict(d).keys()
        if 'name' in keys:
            enabler.get_or_create(name=d['name'])
            id = enabler.select(enabler.id).where(
                enabler.name == d['name']).get()
            if 'components' in keys:
                for comp in d['components']:
                    component.get_or_create(
                        enabler_id=id, name=comp['name'])
    return "enablers added or updated sucesfully"

def train():
    url = 'http://{}:{}/train'.format(tm,tm_port)
    data = requests.get(url).text
    return data

def trainvalues():
    url = 'http://{}:{}/train-values'.format(tm,tm_port)
    data = json.loads(json.dumps(requests.get(url).json()))
    return data

def trainvaluespost(json):
    url = 'http://{}:{}/train-values'.format(tm,tm_port)
    data = requests.post(url, json=json).text
    return data

def deleteData():
    curr = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    datadb = curr - timedelta(days=14)
    return 0

def inference():
    data = requests.get('http://{}:{}/inference'.format(im,im_port)).text
    return data