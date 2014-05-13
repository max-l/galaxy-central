<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%def name="title()">Data Manager</%def>

%if message:
    ${render_msg( message, status )}
%endif

<h2>Data Manager</h2>

%if view_only:
    <p>Not implemented</p>
%elif not data_managers.data_managers:
    ${render_msg( "You do not currently have any Data Managers installed.", "warning" ) }
%else:
    <p>Choose your data managing option from below.</p>
    <ul>
        <li><strong>Run Data Manager Tools</strong>
            <div style="margin-left:1em">
            <ul>
            %for data_manager_id, data_manager in data_managers.data_managers.iteritems():
                <li>
                    <a href="${ h.url_for( controller='tool_runner', action='index', tool_id=data_manager.tool.id ) }"><strong>${ data_manager.name | h }</strong></a> - ${ data_manager.description | h }
                </li>
                <p/>
            %endfor
            </ul>
            </div>
        </li>
        <p/>
        <li><strong>View Data Manager Jobs</strong>
            <div style="margin-left:1em">
            <ul>
                %for data_manager_id, data_manager in data_managers.data_managers.iteritems():
                    <li>
                        <a href="${h.url_for( controller='data_manager', action='manage_data_manager', id=data_manager_id)}" target="galaxy_main"><strong>${ data_manager.name | h }</strong></a> - ${ data_manager.description | h }</a>
                    </li>
                    <p/>
                %endfor
            </ul>
            </div>
        </li>
        <p/>
        <p/>
        <li><strong>View Tool Data Table Entries</strong>
            <div style="margin-left:1em">
            <ul>
                %for table_name, managers in data_managers.managed_data_tables.iteritems():
                    <li>
                        <a href="${h.url_for( controller='data_manager', action='manage_data_table', table_name=table_name)}" target="galaxy_main"><strong>${ table_name | h }</strong></a>
                    </li>
                    <p/>
                %endfor
                %for table_name in tool_data_tables.get_tables():
                    %if table_name not in data_managers.managed_data_tables:
                        <li>
                            <a href="${h.url_for( controller='data_manager', action='manage_data_table', table_name=table_name)}" target="galaxy_main">${ table_name | h }</a>
                        </li>
                        <p/>
                    %endif
                %endfor
            </ul>
            </div>
        </li>
        <p/>
    </ul>
    <p/>
    <br/>
%endif

${render_msg( 'To find out more information about Data Managers, please visit the <a href="https://wiki.galaxyproject.org/Admin/Tools/DataManagers" target="_blank">wiki.</a>', "info" ) }
