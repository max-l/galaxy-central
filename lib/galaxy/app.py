import sys, os, atexit

from galaxy import config, jobs, util, tools, web
import galaxy.model
import galaxy.model.mapping
import galaxy.datatypes.registry
import galaxy.security

class UniverseApplication( object ):
    """Encapsulates the state of a Universe application"""
    def __init__( self, **kwargs ):
        print >> sys.stderr, "python path is: " + ", ".join( sys.path )
        # Read config file and check for errors
        self.config = config.Configuration( **kwargs )
        self.config.check()
        config.configure_logging( self.config )
        # Set up datatypes registry
        self.datatypes_registry = galaxy.datatypes.registry.Registry( self.config.root, self.config.datatypes_config )
        galaxy.model.set_datatypes_registry( self.datatypes_registry )
        # Determine the database url
        if self.config.database_connection:
            db_url = self.config.database_connection
        else:
            db_url = "sqlite://%s?isolation_level=IMMEDIATE" % self.config.database
        # Setup the database engine and ORM
        self.model = galaxy.model.mapping.init( self.config.file_path,
                                                db_url,
                                                self.config.database_engine_options,
                                                create_tables = True )
        # Initialize the tools
        self.toolbox = tools.ToolBox( self.config.tool_config, self.config.tool_path, self )
        #Load datatype converters
        self.datatypes_registry.load_datatype_converters( self.toolbox )
        #Load security policy
        self.security_agent = self.model.security_agent
        # Start the job queue
        job_dispatcher = jobs.DefaultJobDispatcher( self )
        self.job_queue = jobs.JobQueue( self, job_dispatcher )
        self.job_stop_queue = jobs.JobStopQueue( self, job_dispatcher )
        self.heartbeat = None
        # Start the heartbeat process if configured and available
        if self.config.use_heartbeat:
            from galaxy.util import heartbeat
            if heartbeat.Heartbeat:
                self.heartbeat = heartbeat.Heartbeat()
                self.heartbeat.start()
    def shutdown( self ):
        self.job_stop_queue.shutdown()
        self.job_queue.shutdown()
        if self.heartbeat:
            self.heartbeat.shutdown()
