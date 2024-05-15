from mysql_conf import *
from random import randint

def getComponents():
	query = (component.select(component.id,component.enabler_id,enabler.name,component.name).join(enabler)).dicts()
	dict = []
	for q in query:
		dict.append(q)
	return dict

def getResources(comp,curr,hist):
	dataCPU = []
	dataRAM = []
	query = data.select().where((data.component_id==comp['id']) & (data.timestamp >= hist) & (data.timestamp < curr))
	for q in query:
		dataCPU.append([q.timestamp,q.cpu+randint(0,1)])
		dataRAM.append([q.timestamp,q.ram+randint(0,1)])
	return dataCPU,dataRAM

def setMetrics(values):
	for val in values:
		try:
			f = data.get(
        	(data.enabler_id == val['enabler_id']) &
        	(data.component_id == val['component_id']) &
			(data.timestamp == val['timestamp']))
		except data.DoesNotExist:
			data.create(**val)
			continue
		up = data.update(**val).where(
			data.enabler_id==val['enabler_id'],
			data.component_id==val['component_id'],
			data.timestamp==val['timestamp'],
			data.real == val['real']
		)
		up.execute()