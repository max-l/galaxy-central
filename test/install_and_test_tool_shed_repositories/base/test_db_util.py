import logging
import galaxy.model as model
from galaxy.model.orm import and_
from galaxy.model.mapping import context as sa_session

log = logging.getLogger(__name__)

def delete_obj( obj ):
    sa_session.delete( obj )
    sa_session.flush()

def delete_user_roles( user ):
    for ura in user.roles:
        sa_session.delete( ura )
    sa_session.flush()

def flush( obj ):
    sa_session.add( obj )
    sa_session.flush()

def get_repository( repository_id ):
    return sa_session.query( model.ToolShedRepository ) \
                     .filter( model.ToolShedRepository.table.c.id == repository_id ) \
                     .first()

def get_installed_repository_by_name_owner_changeset_revision( name, owner, changeset_revision ):
    return sa_session.query( model.ToolShedRepository ) \
                     .filter( and_( model.ToolShedRepository.table.c.name == name,
                                    model.ToolShedRepository.table.c.owner == owner,
                                    model.ToolShedRepository.table.c.installed_changeset_revision == changeset_revision ) ) \
                     .one()

def get_missing_tool_dependencies( repository ):
    return sa_session.query( model.ToolDependency ) \
                     .filter( and_( model.ToolDependency.table.c.tool_shed_repository_id == repository_id,
                                    model.ToolDependency.table.c.status != model.ToolDependency.installation_status.INSTALLED ) ) \
                     .all()

def get_private_role( user ):
    for role in user.all_roles():
        if role.name == user.email and role.description == 'Private Role for %s' % user.email:
            return role
    raise AssertionError( "Private role not found for user '%s'" % user.email )

def get_tool_dependencies_for_installed_repository( repository_id, status=None, exclude_status=None ):
    if status is not None:
        return sa_session.query( model.ToolDependency ) \
                         .filter( and_( model.ToolDependency.table.c.tool_shed_repository_id == repository_id,
                                        model.ToolDependency.table.c.status == status ) ) \
                         .all()
    elif exclude_status is not None:
        return sa_session.query( model.ToolDependency ) \
                         .filter( and_( model.ToolDependency.table.c.tool_shed_repository_id == repository_id,
                                        model.ToolDependency.table.c.status != exclude_status ) ) \
                         .all()
    else:
        return sa_session.query( model.ToolDependency ) \
                         .filter( model.ToolDependency.table.c.tool_shed_repository_id == repository_id ) \
                         .all()

def mark_obj_deleted( obj ):
    obj.deleted = True
    sa_session.add( obj )
    sa_session.flush()

def refresh( obj ):
    sa_session.refresh( obj )

def get_private_role( user ):
    for role in user.all_roles():
        if role.name == user.email and role.description == 'Private Role for %s' % user.email:
            return role
    raise AssertionError( "Private role not found for user '%s'" % user.email )

def get_user( email ):
    return sa_session.query( model.User ) \
                     .filter( model.User.table.c.email==email ) \
                     .first()
