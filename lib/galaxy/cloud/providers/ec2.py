import subprocess, threading, os, errno, time, datetime
from Queue import Queue, Empty
from datetime import datetime

from galaxy import model # Database interaction class
from galaxy.model import mapping
from galaxy.datatypes.data import nice_size
from galaxy.util.bunch import Bunch
from Queue import Queue
from sqlalchemy import or_

import galaxy.eggs
galaxy.eggs.require("boto")
from boto.ec2.connection import EC2Connection
import boto.exception

import logging
log = logging.getLogger( __name__ )

uci_states = Bunch(
    NEW_UCI = "newUCI",
    NEW = "new",
    DELETING_UCI = "deletingUCI",
    DELETING = "deleting",
    SUBMITTED_UCI = "submittedUCI",
    SUBMITTED = "submitted",
    SHUTTING_DOWN_UCI = "shutting-downUCI",
    SHUTTING_DOWN = "shutting-down",
    AVAILABLE = "available",
    RUNNING = "running",
    PENDING = "pending",
    ERROR = "error",
    DELETED = "deleted"
)

instance_states = Bunch(
    TERMINATED = "terminated",
    RUNNING = "running",
    PENDING = "pending",
    SHUTTING_DOWN = "shutting-down"
)

store_states = Bunch(
    IN_USE = "in-use",
    CREATING = "creating"
)

class EC2CloudProvider( object ):
    """
    Amazon EC2-based cloud provider implementation for managing instances. 
    """
    STOP_SIGNAL = object()
    def __init__( self, app ):
        self.type = "ec2" # cloud provider type (e.g., ec2, eucalyptus, opennebula)
        self.zone = "us-east-1a"
        self.key_pair = "galaxy-keypair"
        self.queue = Queue()
        
        #TODO: Use multiple threads to process requests?
        self.threads = []
        nworkers = 5
        log.info( "Starting EC2 cloud controller workers" )
        for i in range( nworkers  ):
            worker = threading.Thread( target=self.run_next )
            worker.start()
            self.threads.append( worker )
        log.debug( "%d EC2 cloud workers ready", nworkers )
        
    def run_next( self ):
        """Run the next job, waiting until one is available if necessary"""
        cnt = 0
        while 1:
            
            uci_wrapper = self.queue.get()
#            uci = uci_wrapper.get_uci()
            log.debug( '[%d] uci type: %s' % ( cnt, uci_wrapper.get_name() ) )
            uci_state = uci_wrapper.get_state()
            if uci_state is self.STOP_SIGNAL:
                return
            try:
                if uci_state==uci_states.NEW: # "new":
                    self.createUCI( uci_wrapper )
                elif uci_state==uci_states.DELETING: #"deleting":
                    self.deleteUCI( uci_wrapper )
                elif uci_state==uci_states.SUBMITTED: #"submitted":
                    self.startUCI( uci_wrapper )
                elif uci_state==uci_states.SHUTTING_DOWN: #"shutting-down":
                    self.stopUCI( uci_wrapper )
            except:
                log.exception( "Uncaught exception executing request." )
            cnt += 1
            
    def get_connection( self, uci_wrapper ):
        """
        Establishes EC2 cloud connection using user's credentials associated with given UCI
        """
        log.debug( '##### Establishing EC2 cloud connection' )
        conn = EC2Connection( uci_wrapper.get_access_key(), uci_wrapper.get_secret_key() )
        return conn
        
    def set_keypair( self, uci_wrapper, conn ):
        """
        Generate keypair using user's default credentials
        """
        log.debug( "Getting user's keypair" )
        instances = uci_wrapper.get_instances_indexes()
        try:
            kp = conn.get_key_pair( self.key_pair )
            for inst in instances:
#                log.debug("inst: '%s'" % inst )
                uci_wrapper.set_key_pair( inst, kp.name )
            return kp.name
        except boto.exception.EC2ResponseError, e: # No keypair under this name exists so create it
            if e.code == 'InvalidKeyPair.NotFound': 
                log.info( "No keypair found, creating keypair '%s'" % self.key_pair )
                kp = conn.create_key_pair( self.key_pair )
                for inst in instances:
                    uci_wrapper.set_key_pair( inst, kp.name, kp.material )
            else:
                log.error( "EC2 response error: '%s'" % e )
                uci_wrapper.set_error( "EC2 response error while creating key pair: " + e )
                
        return kp.name
    
    def get_mi_id( self, type ):
        """
        Get appropriate machine image (mi) based on instance size.
        TODO: Dummy method - need to implement logic
            For valid sizes, see http://aws.amazon.com/ec2/instance-types/
        """
        return model.CloudImage.filter( model.CloudImage.table.c.id==2 ).first().image_id 
    
#    def get_instances( self, uci ):
#        """
#        Get objects of instances that are pending or running and are connected to uci object
#        """
#        instances = trans.sa_session.query( model.CloudInstance ) \
#            .filter_by( user=user, uci_id=uci.id ) \
#            .filter( or_(model.CloudInstance.table.c.state=="running", model.CloudInstance.table.c.state=="pending" ) ) \
#            .first()
#            #.all() #TODO: return all but need to edit calling method(s) to handle list
#        
#        instances = uci.instance
#            
#        return instances

        
    def shutdown( self ):
        """Attempts to gracefully shut down the monitor thread"""
        log.info( "sending stop signal to worker threads in EC2 cloud manager" )
        for i in range( len( self.threads ) ):
            self.queue.put( self.STOP_SIGNAL )
        log.info( "EC2 cloud manager stopped" )
    
    def put( self, uci_wrapper ):
        # Get rid of UCI from state description
        state = uci_wrapper.get_state()
        uci_wrapper.change_state( state.split('U')[0] ) # remove 'UCI' from end of state description (i.e., mark as accepted and ready for processing)
        self.queue.put( uci_wrapper )
        
    def createUCI( self, uci_wrapper ):
        """ 
        Creates User Configured Instance (UCI). Essentially, creates storage volume on cloud provider
        and registers relevant information in Galaxy database.
        """
        conn = self.get_connection( uci_wrapper )
        # Temporary code - need to ensure user selects zone at UCI creation time!
        if uci_wrapper.get_uci_availability_zone()=='':
            log.info( "Availability zone for UCI (i.e., storage volume) was not selected, using default zone: %s" % self.zone )
            uci_wrapper.set_store_availability_zone( self.zone )
        
        #TODO: check if volume associated with UCI already exists (if server crashed for example) and don't recreate it
        log.info( "Creating volume in zone '%s'..." % uci_wrapper.get_uci_availability_zone() )
        # Because only 1 storage volume may be created at UCI config time, index of this storage volume in local Galaxy DB w.r.t
        # current UCI is 0, so reference it in following methods
        vol = conn.create_volume( uci_wrapper.get_store_size( 0 ), uci_wrapper.get_uci_availability_zone(), snapshot=None )
        uci_wrapper.set_store_volume_id( 0, vol.id )
        
        # Wait for a while to ensure volume was created
#        vol_status = vol.status
#        for i in range( 30 ):
#            if vol_status is not "available":
#                log.debug( 'Updating volume status; current status: %s' % vol_status )
#                vol_status = vol.status
#                time.sleep(3)
#            if i is 29:
#                log.debug( "Error while creating volume '%s'; stuck in state '%s'; deleting volume." % ( vol.id, vol_status ) )
#                conn.delete_volume( vol.id )
#                uci_wrapper.change_state( uci_state='error' )
#                return
        vl = conn.get_all_volumes( [vol.id] )
        if len( vl ) > 0:
            uci_wrapper.change_state( uci_state=vl[0].status )
            uci_wrapper.set_store_status( vol.id, vl[0].status )
        else:
            uci_wrapper.change_state( uci_state=uci_states.ERROR )
            uci_wrapper.set_store_status( vol.id, uci_states.ERROR )
            uci_wrapper.set_error( "Volume '%s' not found by cloud provider after being created" % vol.id )

    def deleteUCI( self, uci_wrapper ):
        """ 
        Deletes UCI. NOTE that this implies deletion of any and all data associated
        with this UCI from the cloud. All data will be deleted.
        """
        conn = self.get_connection( uci_wrapper )
        vl = [] # volume list
        count = 0 # counter for checking if all volumes assoc. w/ UCI were deleted
        
        # Get all volumes assoc. w/ UCI, delete them from cloud as well as in local DB
        vl = uci_wrapper.get_all_stores()
        deletedList = []
        failedList = []
        for v in vl:
            log.debug( "Deleting volume with id='%s'" % v.volume_id )
            if conn.delete_volume( v.volume_id ):
                deletedList.append( v.volume_id )
                v.delete()
                v.flush()
                count += 1
            else:
                failedList.append( v.volume_id )
            
        # Delete UCI if all of associated 
        log.debug( "count=%s, len(vl)=%s" % (count, len( vl ) ) )
        if count == len( vl ):
            uci_wrapper.delete()
        else:
            log.error( "Deleting following volume(s) failed: %s. However, these volumes were successfully deleted: %s. \
                        MANUAL intervention and processing needed." % ( failedList, deletedList ) )
            uci_wrapper.change_state( uci_state=uci_state.ERROR )
            uci_wrapper.set_error( "Deleting following volume(s) failed: "+failedList+". However, these volumes were successfully deleted: "+deletedList+". \
                        MANUAL intervention and processing needed." )
            
    def addStorageToUCI( self, name ):
        """ Adds more storage to specified UCI 
        TODO"""
    
    def dummyStartUCI( self, uci_wrapper ):
        
        uci = uci_wrapper.get_uci()
        log.debug( "Would be starting instance '%s'" % uci.name )
        uci_wrapper.change_state( uci_state.PENDING )
#        log.debug( "Sleeping a bit... (%s)" % uci.name )
#        time.sleep(20)
#        log.debug( "Woke up! (%s)" % uci.name )
        
    def startUCI( self, uci_wrapper ):
        """
        Starts instance(s) of given UCI on the cloud.  
        """ 
        conn = self.get_connection( uci_wrapper )
#        
        self.set_keypair( uci_wrapper, conn )
        i_indexes = uci_wrapper.get_instances_indexes() # Get indexes of i_indexes associated with this UCI whose state is 'None'
        log.debug( "Starting instances with IDs: '%s' associated with UCI '%s' " % ( uci_wrapper.get_name(), i_indexes ) )
        
        for i_index in i_indexes:
            mi_id = self.get_mi_id( uci_wrapper.get_type( i_index ) )
#            log.debug( "mi_id: %s, uci_wrapper.get_key_pair_name( i_index ): %s" % ( mi_id, uci_wrapper.get_key_pair_name( i_index ) ) )
            uci_wrapper.set_mi( i_index, mi_id )
            
            # Check if galaxy security group exists (and create it if it does not)
#            log.debug( '***** Setting up security group' )
            security_group = 'galaxyWeb'
            sgs = conn.get_all_security_groups() # security groups
            gsgt = False # galaxy security group test
            for sg in sgs:
                if sg.name == security_group:
                    gsgt = True
            # If security group does not exist, create it 
            if not gsgt:
                gSecurityGroup = conn.create_security_group(security_group, 'Security group for Galaxy.')
                gSecurityGroup.authorize( 'tcp', 80, 80, '0.0.0.0/0' ) # Open HTTP port
                gSecurityGroup.authorize( 'tcp', 22, 22, '0.0.0.0/0' ) # Open SSH port
            # Start an instance            
            log.debug( "***** Starting instance for UCI '%s'" % uci_wrapper.get_name() )
            #TODO: Once multiple volumes can be attached to a single instance, update 'userdata' composition            
            userdata = uci_wrapper.get_store_volume_id()+"|"+uci_wrapper.get_access_key()+"|"+uci_wrapper.get_secret_key() 
            log.debug( 'Using following command: conn.run_instances( image_id=%s, key_name=%s, security_groups=[%s], user_data=[OMITTED], instance_type=%s, placement=%s )' 
                       % ( mi_id, uci_wrapper.get_key_pair_name( i_index ), [security_group], uci_wrapper.get_type( i_index ), uci_wrapper.get_uci_availability_zone() ) )
            reservation = conn.run_instances( image_id=mi_id, 
                                              key_name=uci_wrapper.get_key_pair_name( i_index ), 
                                              security_groups=[security_group], 
                                              user_data=userdata,
                                              instance_type=uci_wrapper.get_type( i_index ),  
                                              placement=uci_wrapper.get_uci_availability_zone() )
            # Record newly available instance data into local Galaxy database
            l_time = datetime.utcnow()
            uci_wrapper.set_launch_time( l_time, i_index=i_index ) # format_time( reservation.i_indexes[0].launch_time ) )
            if not uci_wrapper.uci_launch_time_set():
                uci_wrapper.set_uci_launch_time( l_time )
            uci_wrapper.set_reservation_id( i_index, str( reservation ).split(":")[1] )
            # TODO: if more than a single instance will be started through single reservation, change this reference to element [0]
            i_id = str( reservation.instances[0]).split(":")[1] 
            uci_wrapper.set_instance_id( i_index, i_id )
            s = reservation.instances[0].state 
            uci_wrapper.change_state( s, i_id, s )
            log.debug( "Instance of UCI '%s' started, current state: '%s'" % ( uci_wrapper.get_name(), uci_wrapper.get_state() ) )
        
        
        
#        # Wait until instance gets running and then update the DB
#        while s!="running":
#            log.debug( "Waiting on instance '%s' to start up (reservation ID: %s); current state: %s" % ( uci.instance[0].instance_id, uci.instance[0].reservation_id, s ) )
#            time.sleep( 15 )
#            s = reservation.i_indexes[0].update()
#        
#        # Update instance data in local DB
#        uci.instance[0].state = s
#        uci.instance[0].public_dns = reservation.i_indexes[0].dns_name
#        uci.instance[0].private_dns = reservation.i_indexes[0].private_dns_name
#        uci.instance[0].flush()
#        # Update storage data in local DB w/ volume state info. NOTE that this only captures current volume state 
#        #    and does not connect or wait on connection between instance and volume to be established
#        vl = model.CloudStore.filter( model.CloudStore.c.uci_id == uci.id ).all()
#        vols = []
#        for v in vl:
#            vols.append( v.volume_id )
#        try:
#            volumes = conn.get_all_volumes( vols )
#            for i, v in enumerate( volumes ):
#                uci.store[i].i_id = v.instance_id
#                uci.store[i].status = v.status
#                uci.store[i].device = v.device
#                uci.store[i].flush()
#        except BotoServerError:
#            log.debug( "Error getting volume(s) attached to instance. Volume status was not updated." )
#        
#        uci.state = s
#        uci.flush()
        
        
    def stopUCI( self, uci_wrapper):
        """ 
        Stops all of cloud instances associated with given UCI. 
        """
        conn = self.get_connection( uci_wrapper )
        
        # Get all instances associated with given UCI
        il = uci_wrapper.get_instances_ids() # instance list
#        log.debug( 'List of instances being terminated: %s' % il )
        rl = conn.get_all_instances( il ) # Reservation list associated with given instances
        
#        tState = conn.terminate_instances( il )
#        # TODO: Need to update instance stop time (for all individual instances)
#        stop_time = datetime.utcnow()
#        uci_wrapper.set_stop_time( stop_time )
                
        # Initiate shutdown of all instances under given UCI
        cnt = 0
        stopped = []
        notStopped = []
        for r in rl:
            for inst in r.instances:
                log.debug( "Sending stop signal to instance '%s' associated with reservation '%s'." % ( inst, r ) )
                inst.stop()
                uci_wrapper.set_stop_time( datetime.utcnow(), i_id=inst.id )
                uci_wrapper.change_state( instance_id=inst.id, i_state=inst.update() )
                stopped.append( inst )
                
#        uci_wrapper.change_state( uci_state='available' )
        uci_wrapper.reset_uci_launch_time()
                        
#        # Wait for all instances to actually terminate and update local DB
#        terminated=0
#        while terminated!=len( rl ):
#            for i, r in enumerate( rl ):
#                log.debug( "r state: %s" % r.instances[0].state )
#                state = r.instances[0].update()
#                if state=='terminated':
#                    uci.instance[i].state = state
#                    uci.instance[i].flush()
#                    terminated += 1
#                time.sleep ( 5 )
#        
#        # Reset UCI state      
#        uci.state = 'available'
#        uci.launch_time = None
#        uci.flush()
#        
        log.debug( "Termination was initiated for all instances of UCI '%s'." % uci_wrapper.get_name() )


#        dbInstances = get_instances( trans, uci ) #TODO: handle list!
#        
#        # Get actual cloud instance object
#        cloudInstance = get_cloud_instance( conn, dbInstances.instance_id )
#        
#        # TODO: Detach persistent storage volume(s) from instance and update volume data in local database
#        stores = get_stores( trans, uci )
#        for i, store in enumerate( stores ):
#            log.debug( "Detaching volume '%s' to instance '%s'." % ( store.volume_id, dbInstances.instance_id ) )
#            mntDevice = store.device
#            volStat = None
##            Detaching volume does not work with Eucalyptus Public Cloud, so comment it out
##            try:
##                volStat = conn.detach_volume( store.volume_id, dbInstances.instance_id, mntDevice )
##            except:
##                log.debug ( 'Error detaching volume; still going to try and stop instance %s.' % dbInstances.instance_id )
#            store.attach_time = None
#            store.device = None
#            store.i_id = None
#            store.status = volStat
#            log.debug ( '***** volume status: %s' % volStat )
#   
#        
#        # Stop the instance and update status in local database
#        cloudInstance.stop()
#        dbInstances.stop_time = datetime.utcnow()
#        while cloudInstance.state != 'terminated':
#            log.debug( "Stopping instance %s state; current state: %s" % ( str( cloudInstance ).split(":")[1], cloudInstance.state ) )
#            time.sleep(3)
#            cloudInstance.update()
#        dbInstances.state = cloudInstance.state
#        
#        # Reset relevant UCI fields
#        uci.state = 'available'
#        uci.launch_time = None
#          
#        # Persist
#        session = trans.sa_session
##        session.save_or_update( stores )
#        session.save_or_update( dbInstances ) # TODO: Is this going to work w/ multiple instances stored in dbInstances variable?
#        session.save_or_update( uci )
#        session.flush()
#        trans.log_event( "User stopped cloud instance '%s'" % uci.name )
#        trans.set_message( "Galaxy instance '%s' stopped." % uci.name )

    def update( self ):
        """ 
        Runs a global status update on all instances that are in 'running', 'pending', "creating", or 'shutting-down' state.
        Also, runs update on all storage volumes that are in "in-use", "creating", or 'None' state.
        Reason behind this method is to sync state of local DB and real-world resources
        """
        log.debug( "Running general status update for EC2 UCIs..." )
        instances = model.CloudInstance.filter( or_( model.CloudInstance.c.state==instance_states.RUNNING, 
                                                     model.CloudInstance.c.state==instance_states.PENDING,  
                                                     model.CloudInstance.c.state==instance_states.SHUTTING_DOWN ) ).all()
        for inst in instances:
            if self.type == inst.uci.credentials.provider.type:
                log.debug( "[%s] Running general status update on instance '%s'" % ( inst.uci.credentials.provider.type, inst.instance_id ) )
                self.updateInstance( inst )
            
        stores = model.CloudStore.filter( or_( model.CloudStore.c.status==store_states.IN_USE, 
                                               model.CloudStore.c.status==store_states.CREATING,
                                               model.CloudStore.c.status==None ) ).all()
        for store in stores:
            if self.type == store.uci.credentials.provider.type:
                log.debug( "[%s] Running general status update on store '%s'" % ( store.uci.credentials.provider.type, store.volume_id ) )
                self.updateStore( store )
        
    def updateInstance( self, inst ):
        
        # Get credentials associated wit this instance
        uci_id = inst.uci_id
        uci = model.UCI.get( uci_id )
        uci.refresh()
        a_key = uci.credentials.access_key
        s_key = uci.credentials.secret_key
        # Get connection
        conn = EC2Connection( aws_access_key_id=a_key, aws_secret_access_key=s_key )
        # Get reservations handle for given instance
        rl= conn.get_all_instances( [inst.instance_id] )
        # Because EPC deletes references to reservations after a short while after instances have terminated, getting an empty list as a response to a query
        # typically means the instance has successfully shut down but the check was not performed in short enough amount of time. As a result, below code simply
        # marks given instance as having terminated. Note that an instance might have also crashed and this code will not catch the difference...
        if len( rl ) == 0:
            log.info( "Instance ID '%s' was not found by the cloud provider. Instance might have crashed or otherwise been terminated." % inst.instance_id )
            inst.state = instance_states.TERMINATED
            uci.state = uci_states.AVAILABLE
            uci.launch_time = None
            inst.flush()
            uci.flush()
        # Update instance status in local DB with info from cloud provider
        for r in rl:
            for i, cInst in enumerate( r.instances ):
                s = cInst.update()
                log.debug( "Checking state of cloud instance '%s' associated with UCI '%s' and reservation '%s'. State='%s'" % ( cInst, uci.name, r, s ) )
                if  s != inst.state:
                    inst.state = s
                    inst.flush()
                    if s == instance_states.TERMINATED: # After instance has shut down, ensure UCI is marked as 'available'
                        uci.state = uci_states.AVAILABLE
                        uci.flush()
                if s != uci.state and s != instance_states.TERMINATED: 
                    # Making sure state of UCI is updated. Once multiple instances become associated with single UCI, this will need to be changed.
                    uci.state = s                    
                    uci.flush() 
                if cInst.public_dns_name != inst.public_dns:
                    inst.public_dns = cInst.public_dns_name
                    inst.flush()
                if cInst.private_dns_name != inst.private_dns:
                    inst.private_dns = cInst.private_dns_name
                    inst.flush()

    def updateStore( self, store ):
        # Get credentials associated wit this store
        uci_id = store.uci_id
        uci = model.UCI.get( uci_id )
        uci.refresh()
        a_key = uci.credentials.access_key
        s_key = uci.credentials.secret_key
        # Get connection
        conn = EC2Connection( aws_access_key_id=a_key, aws_secret_access_key=s_key )
        # Get reservations handle for given store 
        vl = conn.get_all_volumes( [store.volume_id] )
#        log.debug( "Store '%s' vl: '%s'" % ( store.volume_id, vl ) )
        # Update store status in local DB with info from cloud provider
        if store.status != vl[0].status:
            # In case something failed during creation of UCI but actual storage volume was created and yet 
            #  UCI state remained as 'new', try to remedy this by updating UCI state here 
            if ( store.status == None ) and ( store.volume_id != None ):
                uci.state = vl[0].status
                uci.flush()
                
            store.status = vl[0].status
            store.flush()
        if store.i_id != vl[0].instance_id:
            store.i_id = vl[0].instance_id
            store.flush()
        if store.attach_time != vl[0].attach_time:
            store.attach_time = vl[0].attach_time
            store.flush()
        if store.device != vl[0].device:
            store.device = vl[0].device
            store.flush()
    
#    def updateUCI( self, uci ):
#        """ 
#        Runs a global status update on all storage volumes and all instances that are
#        associated with specified UCI
#        """
#        conn = self.get_connection( uci )
#        
#        # Update status of storage volumes
#        vl = model.CloudStore.filter( model.CloudInstance.c.uci_id == uci.id ).all()
#        vols = []
#        for v in vl:
#            vols.append( v.volume_id )
#        try:
#            volumes = conn.get_all_volumes( vols )
#            for i, v in enumerate( volumes ):
#                uci.store[i].i_id = v.instance_id
#                uci.store[i].status = v.status
#                uci.store[i].device = v.device
#                uci.store[i].flush()
#        except:
#            log.debug( "Error updating status of volume(s) associated with UCI '%s'. Status was not updated." % uci.name )
#            pass
#        
#        # Update status of instances
#        il = model.CloudInstance.filter_by( uci_id=uci.id ).filter( model.CloudInstance.c.state != 'terminated' ).all()
#        instanceList = []
#        for i in il:
#            instanceList.append( i.instance_id )
#        log.debug( 'instanceList: %s' % instanceList )
#        try:
#            reservations = conn.get_all_instances( instanceList )
#            for i, r in enumerate( reservations ):
#                uci.instance[i].state = r.instances[0].update()
#                log.debug('updating instance %s; status: %s' % ( uci.instance[i].instance_id, uci.instance[i].state ) )
#                uci.state = uci.instance[i].state
#                uci.instance[i].public_dns = r.instances[0].dns_name
#                uci.instance[i].private_dns = r.instances[0].private_dns_name
#                uci.instance[i].flush()
#                uci.flush()
#        except:
#            log.debug( "Error updating status of instances associated with UCI '%s'. Instance status was not updated." % uci.name )
#            pass
        
    # --------- Helper methods ------------
    
    def format_time( time ):
        dict = {'T':' ', 'Z':''}
        for i, j in dict.iteritems():
            time = time.replace(i, j)
        return time
        