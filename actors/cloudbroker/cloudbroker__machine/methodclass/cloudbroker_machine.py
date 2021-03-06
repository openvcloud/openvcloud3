from js9 import j
from cloudbroker.actorlib.baseactor import BaseActor
from JumpScale9Portal.portal.auth import auth
from JumpScale9Portal.portal.async import async
from JumpScale9Portal.portal import exceptions
import ujson


class cloudbroker_machine(BaseActor):

    def __init__(self):
        super(cloudbroker_machine, self).__init__()
        self.acl = j.clients.agentcontroller.get()

    def _checkMachine(self, machineId):
        vmachines = self.models.vmachine.search({'id': machineId})[1:]
        if not vmachines:
            raise exceptions.NotFound("Machine with id %s does not exists" % machineId)

        return vmachines[0]

    @auth(['level1', 'level2', 'level3'])
    def create(self, cloudspaceId, name, description, sizeId, imageId, disksize, datadisks, **kwargs):
        return self.cb.actors.cloudapi.machines.create(cloudspaceId=cloudspaceId, name=name,
                                                       description=description, sizeId=sizeId,
                                                       imageId=imageId, disksize=disksize, datadisks=datadisks)

    @auth(['level1', 'level2', 'level3'])
    def createOnStack(self, cloudspaceId, name, description, memory, vcpus,
                      imageId, disksize, stackId, datadisks, publicsshkeys, **kwargs):
        """
        Create a machine on a specific stackid
        param:cloudspaceId id of space in which we want to create a machine
        param:name name of machine
        param:description optional description
        :param memory: amount of memory to assign to the vmachine in MiB
        :param vcpus: amount of vcpus to assign to the vmachine
        param:imageId id of the specific image
        param:disksize size of base volume
        param:stackid id of the stack
        param:datadisks list of disk sizes
        param:publicsshkeys list of publicsshkeys which will be granted access to the vm
        result bool
        """
        publicsshkeys = publicsshkeys or []
        pubkeys = []
        for key in publicsshkeys:
            for line in key.splitlines():
                line = line.strip()
                if line:
                    pubkeys.append(line)
        return j.apps.cloudapi.machines._create(cloudspaceId, name, description, memory, vcpus,
                                                imageId, disksize, datadisks, stackId, pubkeys)

    def _validateMachineRequest(self, machineId):
        vmachine = self.models.VMachine.get(machineId)
        if not vmachine:
            raise exceptions.NotFound('Machine ID %s was not found' % machineId)

        if vmachine.status == 'DESTROYED' or not vmachine.status:
            raise exceptions.BadRequest('Machine %s is invalid' % machineId)

        return vmachine

    @auth(['level1', 'level2', 'level3'])
    def destroy(self, machineId, reason, **kwargs):
        self.cb.actors.cloudapi.machines.delete(machineId=machineId)
        return True

    @auth(['level1', 'level2', 'level3'])
    def destroyMachines(self, machineIds, reason, **kwargs):
        ctx = kwargs['ctx']
        ctx.events.runAsync(self._destroyMachines,
                            args=(machineIds, reason, ctx),
                            kwargs={},
                            title='Destroying Machines',
                            success='Machines destroyed successfully',
                            error='Failed to destroy machines')

    def _destroyMachines(self, machineIds, reason, ctx):
        for idx, machineId in enumerate(machineIds):
            ctx.events.sendMessage("Destroying Machine", 'Destroying Machine %s/%s' %
                                   (idx + 1, len(machineIds)))
            try:  # BULK ACTION
                self.destroy(machineId, reason)
            except exceptions.BadRequest:
                pass

    @auth(['level1', 'level2', 'level3'])
    def start(self, machineId, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.start(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def startMachines(self, machineIds, reason, **kwargs):
        ctx = kwargs['ctx']
        ctx.events.runAsync(self._startMachines,
                            args=(machineIds, reason, ctx),
                            kwargs={},
                            title='Starting machines',
                            success='Machines started successfully',
                            error='Failed to start machines')

    def _startMachines(self, machineIds, reason, ctx):
        for idx, machineId in enumerate(machineIds):
            ctx.events.sendMessage("Starting", 'Starting Machine %s/%s' %
                                   (idx + 1, len(machineIds)))
            try:  # BULK ACTION
                self.start(machineId, reason)
            except exceptions.BadRequest:
                pass

    @auth(['level1', 'level2', 'level3'])
    def stop(self, machineId, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.stop(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def stopMachines(self, machineIds, reason, **kwargs):
        ctx = kwargs['ctx']
        ctx.events.runAsync(self._stopMachines,
                            args=(machineIds, reason, ctx),
                            kwargs={},
                            title='Stopping machines',
                            success='Machines stopped successfully',
                            error='Failed to stop machines')

    def _stopMachines(self, machineIds, reason, ctx):
        runningMachineIds = []
        for machineId in machineIds:
            try:  # BULK ACTION
                vmachine = self._validateMachineRequest(machineId)
                if vmachine.status in ['RUNNING', 'PAUSED']:
                    runningMachineIds.append(machineId)
            except exceptions.BadRequest:
                pass

        for idx, machineId in enumerate(runningMachineIds):
            ctx.events.sendMessage("Stopping Machine", 'Stopping Machine %s/%s' %
                                   (idx + 1, len(runningMachineIds)))
            self.cb.actors.cloudapi.machines.stop(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def pause(self, machineId, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.pause(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def resume(self, machineId, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.resume(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def reboot(self, machineId, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.reboot(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def get(self, machineId, **kwargs):
        return self._checkMachine(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def rebootMachines(self, machineIds, reason, **kwargs):
        ctx = kwargs['ctx']
        ctx.events.runAsync(self._rebootMachines,
                            args=(machineIds, reason, ctx),
                            kwargs={},
                            title='Rebooting machines',
                            success='Machines rebooted successfully',
                            error='Failed to reboot machines')

    def _rebootMachines(self, machineIds, reason, ctx):
        for idx, machineId in enumerate(machineIds):
            ctx.events.sendMessage("Rebooting Machine", 'Rebooting Machine %s/%s' %
                                   (idx + 1, len(machineIds)))
            try:   # BULK ACTION
                self.reboot(machineId, reason)
            except exceptions.BadRequest:
                pass

    @auth(['level1', 'level2', 'level3'])
    def snapshot(self, machineId, snapshotName, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.snapshot(machineId=machineId, name=snapshotName)

    @auth(['level1', 'level2', 'level3'])
    def rollbackSnapshot(self, machineId, epoch, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.rollbackSnapshot(machineId=machineId, epoch=epoch)

    @auth(['level1', 'level2', 'level3'])
    def deleteSnapshot(self, machineId, epoch, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.deleteSnapshot(machineId=machineId, epoch=epoch)

    @auth(['level1', 'level2', 'level3'])
    def clone(self, machineId, cloneName, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.clone(machineId=machineId, name=cloneName)

    @auth(['level1', 'level2', 'level3'])
    @async('Moving Virtual Machine', 'Finished Moving Virtual Machine', 'Failed to move Virtual Machine')
    def moveToDifferentComputeNode(self, machineId, reason, targetStackId=None, force=False, **kwargs):
        vmachine = self._validateMachineRequest(machineId)
        cloudspace = vmachine.cloudspace
        source_stack = vmachine.stack

        if not targetStackId:
            targetStackId = self.cb.getBestStack(cloudspace.location, vmachine.image).id
        
        targetStack = self.models.Stack.get(targetStackId)
        if targetStack.location.id != source_stack.location.id:
            raise exceptions.BadRequest('Target stack %s is not on the same location as source' % targetStack.client.uri)

        self.cb.machine.move(vmachine, targetStack, force=force)
        vmachine.stack = targetStack
        vmachine.status = self.cb.machine.status(vmachine)
        vmachine.save()

    @auth(['level1', 'level2', 'level3'])
    def export(self, machineId, name, backuptype, storage, host, aws_access_key, aws_secret_key, bucketname, **kwargs):
        machineId = int(machineId)
        machine = self._validateMachineRequest(machineId)
        stack = self.models.stack.get(machine.stackId)
        storageparameters = {}
        if storage == 'S3':
            if not aws_access_key or not aws_secret_key or not host:
                raise exceptions.BadRequest('S3 parameters are not provided')
            storageparameters['aws_access_key'] = aws_access_key
            storageparameters['aws_secret_key'] = aws_secret_key
            storageparameters['host'] = host
            storageparameters['is_secure'] = True

        storageparameters['storage_type'] = storage
        storageparameters['backup_type'] = backuptype
        storageparameters['bucket'] = bucketname
        storageparameters['mdbucketname'] = bucketname

        storagepath = '/mnt/vmstor/vm-%s' % machineId
        nid = int(stack.referenceId)
        gid = stack.gid
        args = {'path': storagepath, 'name': name, 'machineId': machineId,
                'storageparameters': storageparameters, 'nid': nid, 'backup_type': backuptype}
        guid = self.acl.executeJumpscript(
            'cloudscalers', 'cloudbroker_export', j.application.whoAmI.nid, gid=gid, args=args, wait=False)['guid']
        return guid

    @auth(['level1', 'level2', 'level3'])
    def restore(self, vmexportId, nid, destinationpath, aws_access_key, aws_secret_key, **kwargs):
        vmexportId = int(vmexportId)
        nid = int(nid)
        vmexport = self.models.vmexport.get(vmexportId)
        if not vmexport:
            raise exceptions.NotFound('Export definition with id %s not found' % vmexportId)
        storageparameters = {}

        if vmexport.storagetype == 'S3':
            if not aws_access_key or not aws_secret_key:
                raise exceptions.BadRequest('S3 parameters are not provided')
            storageparameters['aws_access_key'] = aws_access_key
            storageparameters['aws_secret_key'] = aws_secret_key
            storageparameters['host'] = vmexport.server
            storageparameters['is_secure'] = True

        storageparameters['storage_type'] = vmexport.storagetype
        storageparameters['bucket'] = vmexport.bucket
        storageparameters['mdbucketname'] = vmexport.bucket

        metadata = ujson.loads(vmexport.files)

        args = {'path': destinationpath, 'metadata': metadata, 'storageparameters': storageparameters, 'nid': nid}

        id = self.acl.executeJumpscript(
            'cloudscalers', 'cloudbroker_import', j.application.whoAmI.nid, args=args, wait=False)['result']
        return id

    @auth(['level1', 'level2', 'level3'])
    def listExports(self, status, machineId, **kwargs):
        machineId = int(machineId)
        query = {'status': status, 'machineId': machineId}
        exports = self.models.vmexport.search(query)[1:]
        exportresult = []
        for exp in exports:
            exportresult.append({'status': exp['status'], 'type': exp['type'], 'storagetype': exp['storagetype'], 'machineId': exp[
                                'machineId'], 'id': exp['id'], 'name': exp['name'], 'timestamp': exp['timestamp']})
        return exportresult

    @auth(['level1', 'level2', 'level3'])
    def tag(self, machineId, tagName, **kwargs):
        """
        Adds a tag to a machine, useful for indexing and following a (set of) machines
        param:machineId id of the machine to tag
        param:tagName tag
        """
        vmachine = self._validateMachineRequest(machineId)
        tags = j.core.tags.getObject(vmachine.tags)
        if tags.labelExists(tagName):
            raise exceptions.Conflict('Tag %s is already assigned to this vMachine' % tagName)

        tags.labelSet(tagName)
        vmachine.tags = tags.tagstring
        self.models.vmachine.set(vmachine)
        return True

    @auth(['level1', 'level2', 'level3'])
    def untag(self, machineId, tagName, **kwargs):
        """
        Removes a specific tag from a machine
        param:machineId id of the machine to untag
        param:tagName tag
        """
        vmachine = self._validateMachineRequest(machineId)
        tags = j.core.tags.getObject(vmachine.tags)
        if not tags.labelExists(tagName):
            raise exceptions.NotFound('vMachine does not have tag %s' % tagName)

        tags.labelDelete(tagName)
        vmachine.tags = tags.tagstring
        self.models.vmachine.set(vmachine)
        return True

    @auth(['level1', 'level2', 'level3'])
    def list(self, tag=None, computeNode=None, accountName=None, cloudspaceId=None, **kwargs):
        """
        List the undestroyed machines based on specific criteria
        At least one of the criteria needs to be passed
        param:tag a specific tag
        param:computenode name of a specific computenode
        param:accountname specific account
        param:cloudspaceId specific cloudspace
        """
        if not tag and not computeNode and not accountName and not cloudspaceId:
            raise exceptions.BadRequest('At least one parameter must be passed')
        query = dict()
        if tag:
            query['tags'] = tag
        if computeNode:
            stacks = self.models.stack.search({'referenceId': computeNode})[1:]
            if stacks:
                stack_id = stacks[0]['id']
                query['stackId'] = stack_id
            else:
                return list()
        if accountName:
            accounts = self.models.account.search({'name': accountName})[1:]
            if accounts:
                account_id = accounts[0]['id']
                cloudspaces = self.models.cloudspace.search({'accountId': account_id})[1:]
                if cloudspaces:
                    cloudspaces_ids = [cs['id'] for cs in cloudspaces]
                    query['cloudspaceId'] = {'$in': cloudspaces_ids}
                else:
                    return list()
            else:
                return list()
        if cloudspaceId:
            query['cloudspaceId'] = cloudspaceId

        query['status'] = {'$ne': 'destroyed'}
        return self.models.vmachine.search(query)[1:]

    @auth(['level1', 'level2', 'level3'])
    def stopForAbusiveResourceUsage(self, accountId, machineId, reason, **kwargs):
        '''If a machine is abusing the system and violating the usage policies it can be stopped using this procedure.
        A ticket will be created for follow up and visibility, the machine stopped, the image put on slower storage and the ticket is automatically closed if all went well.
        Use with caution!
        @param:accountId str,,Account ID, extra validation for preventing a wrong machineId
        @param:machineId str,,Id of the machine
        @param:reason str,,Reason
        '''
        machineId = int(machineId)
        vmachine = self._validateMachineRequest(machineId)

        stack = self.models.stack.get(vmachine.stackId)
        args = {'machineId': vmachine.id, 'nodeId': vmachine.referenceId}
        self.acl.executeJumpscript(
            'cloudscalers', 'vm_stop_for_abusive_usage', gid=stack.gid, nid=stack.referenceId, args=args, wait=False)

    @auth(['level1', 'level2', 'level3'])
    def getConsoleInfo(self, token, **kwargs):
        return self.cb.machine.getConsoleInfo(token)

    @auth(['level1', 'level2', 'level3'])
    def backupAndDestroy(self, accountId, machineId, reason, **kwargs):
        """
        * Create a ticketjob
        * Call the backup method
        * Destroy the machine
        * Close the ticket
        """
        vmachine = self._validateMachineRequest(machineId)
        args = {'accountId': accountId, 'machineId': machineId, 'reason': reason,
                'vmachineName': vmachine.name, 'cloudspaceId': vmachine.cloudspaceId}
        self.acl.executeJumpscript(
            'cloudscalers', 'vm_backup_destroy', gid=j.application.whoAmI.gid, nid=j.application.whoAmI.nid, args=args, wait=False)

    @auth(['level1', 'level2', 'level3'])
    def listSnapshots(self, machineId, **kwargs):
        self._validateMachineRequest(machineId)
        return self.cb.actors.cloudapi.machines.listSnapshots(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def getHistory(self, machineId, **kwargs):
        self._validateMachineRequest(machineId)
        return self.cb.actors.cloudapi.machines.getHistory(machineId=machineId, size=10)

    @auth(['level1', 'level2', 'level3'])
    def listPortForwards(self, machineId, **kwargs):
        vmachine = self._validateMachineRequest(machineId)
        cloudspace = self.models.cloudspace.get(vmachine.cloudspaceId)
        return cloudspace.forwardRules

    @auth(['level1', 'level2', 'level3'])
    def createPortForward(self, machineId, localPort, destPort, proto, **kwargs):
        vmachine = self._validateMachineRequest(machineId)
        j.apps.cloudapi.portforwarding.create(cloudspaceId=vmachine.cloudspace.id,
                                              publicIp=vmachine.cloudspace.externalnetworkip,
                                              publicPort=destPort, machineId=vmachine.id,
                                              localPort=localPort, protocol=proto)

    @auth(['level1', 'level2', 'level3'])
    def deletePortForward(self, machineId, publicIp, publicPort, proto, **kwargs):
        vmachine = self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.portforwarding.deleteByPort(cloudspaceId=vmachine.cloudspace.id,
                                                            publicIp=publicIp,
                                                            publicPort=publicPort, proto=proto)

    @auth(['level1', 'level2', 'level3'])
    def addDisk(self, machineId, diskName, description, size=10, iops=2000, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.addDisk(machineId=machineId, diskName=diskName,
                                                 description=description, size=size, iops=iops, type='D')

    @auth(['level1', 'level2', 'level3'])
    def deleteDisk(self, machineId, diskId, **kwargs):
        self._validateMachineRequest(machineId)
        return self.cb.actors.cloudapi.disks.delete(diskId=diskId, detach=True)

    @auth(['level1', 'level2', 'level3'])
    def convertToTemplate(self, machineId, templateName, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.convertToTemplate(machineId=machineId, templatename=templateName)

    @auth(['level1', 'level2', 'level3'])
    def updateMachine(self, machineId, description, name, reason, **kwargs):
        self._validateMachineRequest(machineId)
        self.cb.actors.cloudapi.machines.update(machineId=machineId, description=description, name=name)

    @auth(['level1', 'level2', 'level3'])
    def attachExternalNetwork(self, machineId, **kwargs):
        # FIXME: requires name parameter.
        return self.cb.actors.cloudapi.machines.attachExternalNetwork(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def detachExternalNetwork(self, machineId, **kwargs):
        return self.cb.actors.cloudapi.machines.detachExternalNetwork(machineId=machineId)

    @auth(['level1', 'level2', 'level3'])
    def addUser(self, machineId, username, accesstype, **kwargs):
        """
        Give a user access rights.
        Access rights can be 'R' or 'W'
        param:machineId id of the machine
        param:username id of the user to give access or emailaddress to invite an external user
        param:accesstype 'R' for read only access, 'W' for Write access
        result bool
        """
        return self.cb.actors.cloudapi.machines.addUser(machineId=machineId, userId=username, accesstype=accesstype)

    @auth(['level1', 'level2', 'level3'])
    def deleteUser(self, machineId, username, **kwargs):
        """
        Delete a user from the account
        """
        return self.cb.actors.cloudapi.machines.deleteUser(machineId=machineId, userId=username)

    @auth(['level1', 'level2', 'level3'])
    def resize(self, machineId, memory, vcpus, **kwargs):
        return self.cb.actors.cloudapi.machines.resize(machineId=machineId, memory=memory, vcpus=vcpus)
