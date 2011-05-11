# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.db import models

import generic, hosts, fault, config, hashlib, re, uuid, os

from lib import qm, fileutil, hostserver, ifaceutil

class KVMDevice(generic.Device):
	def upcast(self):
		return self

	def init(self):
		self.setTemplate("")

	def setVmid(self, value):
		self.attributes["vmid"] = value

	def getVmid(self):
		return self.attributes.get("vmid")

	def setVncPort(self, value):
		self.attributes["vnc_port"] = value

	def getVncPort(self):
		return self.attributes.get("vnc_port")

	def setTemplate(self, value):
		self.attributes["template"] = value

	def getTemplate(self):
		return self.attributes["template"]

	def getState(self):
		if config.remote_dry_run:
			return self.state
		if not self.getVmid() or not self.host:
			return generic.State.CREATED
		return qm.getState(self.host, self.getVmid()) 

	def downloadSupported(self):
		return self.state == generic.State.PREPARED

	def downloadImageUri(self):
		assert self.downloadSupported(), "Download not supported"
		filename = "%s_%s.qcow2" % (self.topology.name, self.name)
		file = hostserver.randomFilename(self.host)
		qm.copyImage(self.host, self.getVmid(), file)
		return hostserver.downloadGrant(self.host, file, filename)

	def uploadSupported(self):
		return self.state == generic.State.PREPARED

	def useUploadedImageRun(self, path):
		assert self.uploadSupported(), "Upload not supported"
		qm.useImage(self.host, self.getVmid(), path, move=True)
		self.setTemplate("***custom***")

	def _startVnc(self):
		if not self.getVncPort():
			self.setVncPort(self.host.nextFreePort())
		qm.startVnc(self.host, self.getVmid(), self.getVncPort(), self.vncPassword())

	def _startIface(self, iface):
		bridge = self.bridgeName(iface)
		ifaceutil.bridgeCreate(self.host, bridge)
		ifaceutil.bridgeConnect(self.host, bridge, self._interfaceDevice(iface))
		ifaceutil.ifup(self.host, bridge)

	def _startVm(self):
		qm.start(self.host, self.getVmid())

	def getStartTasks(self):
		from lib import tasks
		taskset = generic.Device.getStartTasks(self)
		taskset.addTask(tasks.Task("start-vm", self._startVm))
		for iface in self.interfaceSetAll():
			taskset.addTask(tasks.Task("start-interface-%s" % iface, self._startIface, args=(iface,), depends="start-vm"))
		taskset.addTask(tasks.Task("start-vnc", self._startVnc, depends="start-vm"))
		return taskset

	def _stopVnc(self):
		qm.stopVnc(self.host, self.getVmid(), self.getVncPort())
		del self.attributes["vnc_port"]
	
	def _stopVm(self):
		qm.stop(self.host, self.getVmid())
	
	def getStopTasks(self):
		from lib import tasks
		taskset = generic.Device.getStopTasks(self)
		taskset.addTask(tasks.Task("stop-vm", self._stopVm))
		taskset.addTask(tasks.Task("stop-vnc", self._stopVnc))
		return taskset

	def _assignTemplate(self):
		self.setTemplate(hosts.getTemplateName(self.type, self.getTemplate()))
		assert self.getTemplate() and self.getTemplate() != "None", "Template not found"

	def _assignHost(self):
		if not self.host:
			self.host = self.hostOptions().best()
			assert self.host, "No matching host found"
			self.save()

	def _assignVmid(self):
		assert self.host
		if not self.getVmid():
			self.setVmid(self.host.nextFreeVmId())

	def _useTemplate(self):
		qm.useTemplate(self.host, self.getVmid(), self.getTemplate())

	def _configureVm(self):
		qm.setName(self.host, self.getVmid(), "%s_%s" % (self.topology.name, self.name))

	def _createIface(self, iface):
		qm.addInterface(self.host, self.getVmid(), iface.name)
	
	def _createVm(self):
		qm.create(self.host, self.getVmid())

	def getPrepareTasks(self):
		from lib import tasks
		taskset = generic.Device.getPrepareTasks(self)
		taskset.addTask(tasks.Task("assign-template", self._assignTemplate))
		taskset.addTask(tasks.Task("assign-host", self._assignHost))		
		taskset.addTask(tasks.Task("assign-vmid", self._assignVmid, depends="assign-host"))
		taskset.addTask(tasks.Task("create-vm", self._createVm, depends="assign-vmid"))
		taskset.addTask(tasks.Task("use-template", self._useTemplate, depends="create-vm"))
		taskset.addTask(tasks.Task("configure-vm", self._configureVm, depends="create-vm"))
		for iface in self.interfaceSetAll():
			taskset.addTask(tasks.Task("create-interface-%s" % iface.name, self._createIface, args=(iface,), depends="create-vm"))
		return taskset

	def _unassignHost(self):
		self.host = None
		self.save()
		
	def _unassignVmid(self):
		del self.attributes["vmid"]

	def _destroyVm(self):
		qm.destroy(self.host, self.getVmid())

	def getDestroyTasks(self):
		from lib import tasks
		taskset = generic.Device.getDestroyTasks(self)
		if self.host:
			taskset.addTask(tasks.Task("destroy-vm", self._destroyVm))
			taskset.addTask(tasks.Task("unassign-host", self._unassignHost, depends="destroy-vm"))
			taskset.addTask(tasks.Task("unassign-vmid", self._unassignVmid, depends="destroy-vm"))
		return taskset

	def configure(self, properties):
		if "template" in properties:
			assert self.state == generic.State.CREATED, "Cannot change template of prepared device: %s" % self.name
		generic.Device.configure(self, properties)
		if "template" in properties:
			self._assignTemplate()
		self.save()
			
	def interfacesAdd(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		assert self.state != generic.State.STARTED, "Changes of running KVMs are not supported"
		assert re.match("eth(\d+)", name), "Invalid interface name: %s" % name
		iface = generic.Interface()
		iface.init()
		try:
			if self.interfaceSetGet(name):
				raise fault.new(fault.DUPLICATE_INTERFACE_NAME, "Duplicate interface name: %s" % name)
		except generic.Interface.DoesNotExist: #pylint: disable-msg=W0702
			pass
		iface.name = name
		iface.device = self
		if self.state == generic.State.PREPARED:
			qm.addInterface(self.host, self.getVmid(), iface.name)
		iface.save()
		generic.Device.interfaceSetAdd(self, iface)

	def interfacesConfigure(self, name, properties):
		pass
	
	def interfacesRename(self, name, properties): #@UnusedVariable, pylint: disable-msg=W0613
		#FIXME: implement by delete-add
		assert False, "KVM does not support renaming interfaces: %s" % name
	
	def interfacesDelete(self, name): #@UnusedVariable, pylint: disable-msg=W0613
		assert self.state != generic.State.STARTED, "Changes of running KVMs are not supported"
		iface = self.interfaceSetGet(name)
		if self.state == generic.State.PREPARED:
			qm.deleteInterface(self.host, self.getVmid(), iface.name)
		iface.delete()
		
	def vncPassword(self):
		if not self.getVmid():
			return "---"
		m = hashlib.md5()
		m.update(config.password_salt)
		m.update(str(self.name))
		m.update(str(self.getVmid()))
		m.update(str(self.getVncPort()))
		m.update(str(self.topology.owner))
		return m.hexdigest()

	def getResourceUsage(self):
		disk = 0
		memory = 0
		ports = 1 if self.state == generic.State.STARTED else 0		
		if self.host and self.getVmid():
			disk = qm.getDiskUsage(self.host, self.getVmid())
			memory = qm.getMemoryUsage(self.host, self.getVmid())
		return {"disk": disk, "memory": memory, "ports": ports}		
	
	def _interfaceDevice(self, iface):
		return qm.interfaceDevice(self.host, self.getVmid(), iface.name)

	def migrateRun(self, host=None):
		#FIXME: both vmids must be reserved the whole time
		if self.state == generic.State.CREATED:
			self._unassignHost()
			self._unassignVmid()
			return
		#save src data
		src_host = self.host
		src_vmid = self.getVmid()
		#assign new host and vmid
		self._unassignHost()
		self._unassignVmid()
		if host:
			self.host = host
		else:
			self._assignHost()
		self._assignVmid()
		dst_host = self.host
		dst_vmid = self.getVmid()
		#reassign host and vmid
		self.host = src_host
		self.setVmid(src_vmid)
		#destroy all connectors and save their state
		constates={}
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector
				if con.name in constates:
					continue
				constates[con.name] = con.state
				if con.state == generic.State.STARTED:
					con.stop(True)
				if con.state == generic.State.PREPARED:
					con.destroy(True)
		#actually migrate the vm
		if self.state == generic.State.STARTED:
			self._stopVnc()
		qm.migrate(src_host, src_vmid, dst_host, dst_vmid)
		if self.state == generic.State.STARTED:
			self._startVnc()
		#switch host and vmid
		self.host = dst_host
		self.setVmid(dst_vmid)
		#redeploy all connectors
		for iface in self.interfaceSetAll():
			if iface.isConnected():
				con = iface.connection.connector
				if not con.name in constates:
					continue
				state = constates[con.name]
				del constates[con.name]
				if state == generic.State.PREPARED or state == generic.State.STARTED:
					con.prepare(True)
				if state == generic.State.STARTED:
					con.start(True)

	def toDict(self, auth):
		res = generic.Device.toDict(self, auth)
		if not auth:
			del res["attrs"]["vnc_port"]
		else:
			res["attrs"]["vncPassword"] = self.vncPassword()
		return res

