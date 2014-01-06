"""
API operations on the contents of a library.
"""
import logging

from galaxy import web
from galaxy.model import ExtendedMetadata, ExtendedMetadataIndex
from galaxy.web.base.controller import BaseAPIController, UsesLibraryMixin, UsesLibraryMixinItems
from galaxy.web.base.controller import UsesHistoryDatasetAssociationMixin
from galaxy.web.base.controller import HTTPBadRequest, url_for
from galaxy import util

log = logging.getLogger( __name__ )

class LibraryContentsController( BaseAPIController, UsesLibraryMixin, UsesLibraryMixinItems,
                                 UsesHistoryDatasetAssociationMixin ):

    @web.expose_api
    # TODO: Add parameter to only get top level of datasets/subfolders.
    def index( self, trans, library_id, **kwd ):
        """
        index( self, trans, library_id, **kwd )
        * GET /api/libraries/{library_id}/contents:
            return a list of library files and folders

        :type   library_id: str
        :param  library_id: encoded id string of the library that contains this item

        :rtype:     list
        :returns:   list of dictionaries of the form:

            * id:   the encoded id of the library item
            * name: the 'libary path'
                or relationship of the library item to the root
            * type: 'file' or 'folder'
            * url:  the url to get detailed information on the library item
        """
        rval = []
        current_user_roles = trans.get_current_user_roles()
        def traverse( folder ):
            admin = trans.user_is_admin()
            rval = []
            for subfolder in folder.active_folders:
                if not admin:
                    can_access, folder_ids = trans.app.security_agent.check_folder_contents( trans.user, current_user_roles, subfolder )
                if (admin or can_access) and not subfolder.deleted:
                    subfolder.api_path = folder.api_path + '/' + subfolder.name
                    subfolder.api_type = 'folder'
                    rval.append( subfolder )
                    rval.extend( traverse( subfolder ) )
            for ld in folder.datasets:
                if not admin:
                    can_access = trans.app.security_agent.can_access_dataset(
                        current_user_roles, ld.library_dataset_dataset_association.dataset )
                if (admin or can_access) and not ld.deleted:
                    #log.debug( "type(folder): %s" % type( folder ) )
                    #log.debug( "type(api_path): %s; folder.api_path: %s" % ( type(folder.api_path), folder.api_path ) )
                    #log.debug( "attributes of folder: %s" % str(dir(folder)) )
                    ld.api_path = folder.api_path + '/' + ld.name
                    ld.api_type = 'file'
                    rval.append( ld )
            return rval
        try:
            decoded_library_id = trans.security.decode_id( library_id )
        except TypeError:
            trans.response.status = 400
            return "Malformed library id ( %s ) specified, unable to decode." % str( library_id )
        try:
            library = trans.sa_session.query( trans.app.model.Library ).get( decoded_library_id )
        except:
            library = None
        if not library or not ( trans.user_is_admin() or trans.app.security_agent.can_access_library( current_user_roles, library ) ):
            trans.response.status = 400
            return "Invalid library id ( %s ) specified." % str( library_id )
        #log.debug( "Root folder type: %s" % type( library.root_folder ) )
        encoded_id = 'F' + trans.security.encode_id( library.root_folder.id )
        rval.append( dict( id = encoded_id,
                           type = 'folder',
                           name = '/',
                           url = url_for( 'library_content', library_id=library_id, id=encoded_id ) ) )
        #log.debug( "Root folder attributes: %s" % str(dir(library.root_folder)) )
        library.root_folder.api_path = ''
        for content in traverse( library.root_folder ):
            encoded_id = trans.security.encode_id( content.id )
            if content.api_type == 'folder':
                encoded_id = 'F' + encoded_id
            rval.append( dict( id = encoded_id,
                               type = content.api_type,
                               name = content.api_path,
                               url = url_for( 'library_content', library_id=library_id, id=encoded_id, ) ) )
        return rval

    @web.expose_api
    def show( self, trans, id, library_id, **kwd ):
        """
        show( self, trans, id, library_id, **kwd )
        * GET /api/libraries/{library_id}/contents/{id}
            return information about library file or folder

        :type   id:         str
        :param  id:         the encoded id of the library item to return
        :type   library_id: str
        :param  library_id: encoded id string of the library that contains this item

        :rtype:     dict
        :returns:   detailed library item information
        .. seealso::
            :func:`galaxy.model.LibraryDataset.to_dict` and
            :attr:`galaxy.model.LibraryFolder.dict_element_visible_keys`
        """
        class_name, content_id = self.__decode_library_content_id( trans, id )
        if class_name == 'LibraryFolder':
            content = self.get_library_folder( trans, content_id, check_ownership=False, check_accessible=True )
        else:
            content = self.get_library_dataset( trans, content_id, check_ownership=False, check_accessible=True )
        return self.encode_all_ids( trans, content.to_dict( view='element' ) )

    @web.expose_api
    def create( self, trans, library_id, payload, **kwd ):
        """
        create( self, trans, library_id, payload, **kwd )
        * POST /api/libraries/{library_id}/contents:
            create a new library file or folder

        To copy an HDA into a library send ``create_type`` of 'file' and
        the HDA's encoded id in ``from_hda_id`` (and optionally ``ldda_message``).

        :type   library_id: str
        :param  library_id: encoded id string of the library that contains this item
        :type   payload:    dict
        :param  payload:    dictionary structure containing:

            * folder_id:    the parent folder of the new item
            * create_type:  the type of item to create ('file' or 'folder')
            * from_hda_id:  (optional) the id of an accessible HDA to copy into the
                library
            * ldda_message: (optional) the new message attribute of the LDDA created
            * extended_metadata: (optional) dub-dictionary containing any extended
                metadata to associate with the item

        :rtype:     dict
        :returns:   a dictionary containing the id, name,
            and 'show' url of the new item
        """
        create_type = None
        if 'create_type' not in payload:
            trans.response.status = 400
            return "Missing required 'create_type' parameter."
        else:
            create_type = payload.pop( 'create_type' )
        if create_type not in ( 'file', 'folder' ):
            trans.response.status = 400
            return "Invalid value for 'create_type' parameter ( %s ) specified." % create_type

        if 'folder_id' not in payload:
            trans.response.status = 400
            return "Missing requred 'folder_id' parameter."
        else:
            folder_id = payload.pop( 'folder_id' )
            class_name, folder_id = self.__decode_library_content_id( trans, folder_id )
        try:
            # security is checked in the downstream controller
            parent = self.get_library_folder( trans, folder_id, check_ownership=False, check_accessible=False )
        except Exception, e:
            return str( e )
        # The rest of the security happens in the library_common controller.
        real_folder_id = trans.security.encode_id( parent.id )

        roles = payload.get("roles", None)
        if roles:
            roles = util.listify(roles)

            def to_id_as_str(role):
                role = role.replace("__at__", "@")
                if "@" in role:
                    role = str( trans.sa_session.query( trans.app.model.Role ).filter( trans.app.model.Role.table.c.name == role ).first().id )
                else:
                    role = str( trans.security.decode_id( role ) )
                return role

            payload["roles"] = map( to_id_as_str, roles )

        # are we copying an HDA to the library folder?
        #   we'll need the id and any message to attach, then branch to that private function
        from_hda_id, ldda_message = ( payload.pop( 'from_hda_id', None ), payload.pop( 'ldda_message', '' ) )
        if create_type == 'file' and from_hda_id:
            return self._copy_hda_to_library_folder( trans, from_hda_id, library_id, real_folder_id, ldda_message )

        #check for extended metadata, store it and pop it out of the param
        #otherwise sanitize_param will have a fit
        ex_meta_payload = None
        if 'extended_metadata' in payload:
            ex_meta_payload = payload.pop('extended_metadata')

        # Now create the desired content object, either file or folder.
        if create_type == 'file':
            status, output = trans.webapp.controllers['library_common'].upload_library_dataset( trans, 'api', library_id, real_folder_id, **payload )
        elif create_type == 'folder':
            status, output = trans.webapp.controllers['library_common'].create_folder( trans, 'api', real_folder_id, library_id, **payload )
        if status != 200:
            trans.response.status = status
            return output
        else:
            rval = []
            for k, v in output.items():
                if ex_meta_payload is not None:
                    """
                    If there is extended metadata, store it, attach it to the dataset, and index it
                    """
                    ex_meta = ExtendedMetadata(ex_meta_payload)
                    trans.sa_session.add( ex_meta )
                    v.extended_metadata = ex_meta
                    trans.sa_session.add(v)
                    trans.sa_session.flush()
                    for path, value in self._scan_json_block(ex_meta_payload):
                        meta_i = ExtendedMetadataIndex(ex_meta, path, value)
                        trans.sa_session.add(meta_i)
                    trans.sa_session.flush()
                if type( v ) == trans.app.model.LibraryDatasetDatasetAssociation:
                    v = v.library_dataset
                encoded_id = trans.security.encode_id( v.id )
                if create_type == 'folder':
                    encoded_id = 'F' + encoded_id
                rval.append( dict( id = encoded_id,
                                   name = v.name,
                                   url = url_for( 'library_content', library_id=library_id, id=encoded_id ) ) )
            return rval

    def _scan_json_block(self, meta, prefix=""):
        """
        Scan a json style data structure, and emit all fields and their values.
        Example paths

        Data
        { "data" : [ 1, 2, 3 ] }

        Path:
        /data == [1,2,3]

        /data/[0] == 1

        """
        if isinstance(meta, dict):
            for a in meta:
                for path, value in self._scan_json_block(meta[a], prefix + "/" + a):
                    yield path, value
        elif isinstance(meta, list):
            for i, a in enumerate(meta):
                for path, value in self._scan_json_block(a, prefix + "[%d]" % (i)):
                    yield path, value
        else:
            #BUG: Everything is cast to string, which can lead to false positives
            #for cross type comparisions, ie "True" == True
            yield prefix, ("%s" % (meta)).encode("utf8", errors='replace')

    def _copy_hda_to_library_folder( self, trans, from_hda_id, library_id, folder_id, ldda_message='' ):
        """
        Copies hda ``from_hda_id`` to library folder ``library_folder_id`` optionally
        adding ``ldda_message`` to the new ldda's ``message``.

        ``library_contents.create`` will branch to this if called with 'from_hda_id'
        in it's payload.
        """
        log.debug( '_copy_hda_to_library_folder: %s' %( str(( from_hda_id, library_id, folder_id, ldda_message )) ) )
        #PRECONDITION: folder_id has already been altered to remove the folder prefix ('F')
        #TODO: allow name and other, editable ldda attrs?
        if ldda_message:
            ldda_message = util.sanitize_html.sanitize_html( ldda_message, 'utf-8' )

        rval = {}
        try:
            # check permissions on (all three?) resources: hda, library, folder
            #TODO: do we really need the library??
            hda = self.get_dataset( trans, from_hda_id, check_ownership=True, check_accessible=True, check_state=True )
            library = self.get_library( trans, library_id, check_accessible=True )
            folder = self.get_library_folder( trans, folder_id, check_accessible=True )

            if not self.can_current_user_add_to_library_item( trans, folder ):
                trans.response.status = 403
                return { 'error' : 'user has no permission to add to library folder (%s)' %( folder_id ) }

            ldda = self.copy_hda_to_library_folder( trans, hda, folder, ldda_message=ldda_message )
            ldda_dict = ldda.to_dict()
            rval = trans.security.encode_dict_ids( ldda_dict )

        except Exception, exc:
            #TODO: grrr...
            if 'not accessible to the current user' in str( exc ):
                trans.response.status = 403
                return { 'error' : str( exc ) }
            else:
                log.exception( exc )
                trans.response.status = 500
                return { 'error' : str( exc ) }

        return rval

    @web.expose_api
    def update( self, trans, id, library_id, payload, **kwd ):
        """
        update( self, trans, id, library_id, payload, **kwd )
        * PUT /api/libraries/{library_id}/contents/{id}
            create a ImplicitlyConvertedDatasetAssociation
        .. seealso:: :class:`galaxy.model.ImplicitlyConvertedDatasetAssociation`

        :type   id:         str
        :param  id:         the encoded id of the library item to return
        :type   library_id: str
        :param  library_id: encoded id string of the library that contains this item
        :type   payload:    dict
        :param  payload:    dictionary structure containing::
            'converted_dataset_id':

        :rtype:     None
        :returns:   None
        """
        if 'converted_dataset_id' in payload:
            converted_id = payload.pop( 'converted_dataset_id' )
            content = self.get_library_dataset( trans, id, check_ownership=False, check_accessible=False )
            content_conv = self.get_library_dataset( trans, converted_id, check_ownership=False, check_accessible=False )
            assoc = trans.app.model.ImplicitlyConvertedDatasetAssociation( parent = content.library_dataset_dataset_association,
                dataset = content_conv.library_dataset_dataset_association,
                file_type = content_conv.library_dataset_dataset_association.extension,
                metadata_safe = True )
            trans.sa_session.add( assoc )
            trans.sa_session.flush()

    def __decode_library_content_id( self, trans, content_id ):
        if ( len( content_id ) % 16 == 0 ):
            return 'LibraryDataset', content_id
        elif ( content_id.startswith( 'F' ) ):
            return 'LibraryFolder', content_id[1:]
        else:
            raise HTTPBadRequest( 'Malformed library content id ( %s ) specified, unable to decode.' % str( content_id ) )
