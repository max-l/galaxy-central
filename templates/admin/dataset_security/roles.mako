<%inherit file="/base.mako"/>

<% 
  from galaxy.web.controllers.admin import entities, unentities
  from xml.sax.saxutils import escape, unescape 
%>

## Render a row
<%def name="render_row( role )">
    <td><a href="${h.url_for( action='role', id=role.id, edit=True )}">${role.name}</a></td>
    <td>${role.type}</td>
    <td>${[ x.user.email for x in role.users ]} ${[ x.group.name for x in role.groups ]}</td>
    ##<td><a href="${h.url_for( controller='admin', action='group_members', group_id=group[0], group_name=group[1] )}">${group[3]}</a></td>
    <td>todo</td>
    ##<td><a href="${h.url_for( controller='admin', action='mark_group_deleted', group_id=group[0] )}">Mark group deleted</a></td>
</%def>

<%def name="title()">Roles</%def>

%if msg:
<div class="donemessage">${msg}</div>
%endif

<h2>Roles</h2>

<ul class="manage-table-actions">
    <li>
        <a class="action-button" href="${h.url_for( controller='admin', action='roles', create=True )}">
            Create a new role
        </a>
    </li>
    <li>
        <a class="action-button" href="${h.url_for( controller='admin', action='deleted_roles' )}">
            Manage deleted roles
        </a>
    </li>
</ul>

%if len( roles ) == 0:
    There are no Galaxy roles
%else:
    <table class="manage-table colored" border="0" cellspacing="0" cellpadding="0" width="100%">

      <% 
        render_quick_find = len( roles ) > 50
        ctr = 0
      %>
      %if render_quick_find:
        <%
          anchors = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
          anchor_loc = 0
          anchored = False
          curr_anchor = 'A'
        %>
        <tr style="background: #EEE">
          <td colspan="6" style="text-align: center; border-bottom: 1px solid #D8B365">
            Jump to letter:
            %for a in anchors:
                | <a href="#${a}">${a}</a>
            %endfor
          </td>
        </tr>
      %endif
      <tr class="header">
        <td>Name</td>
        <td>Type</td>
        <td>Users/Groups</td>
        <td>Datasets</td>
        ##<td>&nbsp;</td>
      </tr>
      %for role in roles:
        ##<% role_name = unescape( group[1], unentities ) %>
        %if render_quick_find and not role.name.upper().startswith( curr_anchor ):
          <% anchored = False %>
        %endif
        <tr>
          %if ctr % 2 == 1:
            <div class="odd_row">
          %endif
          %if render_quick_find and role.name.upper().startswith( curr_anchor ):
            %if not anchored:
              <tr>
                <td colspan="6" class=panel-body">
                  <a name="${curr_anchor}"></a>
                  <div style="float: right;"><a href="#TOP">quick find</a></div>
                  <% anchored = True %>
                </td>
              </tr>
            %endif
            ${render_row( role )}
          %elif render_quick_find:
            %for anchor in anchors[ anchor_loc: ]:
              %if role.name.upper().startswith( anchor ):
                %if not anchored:
                  <tr>
                    <td colspan="6" class="panel-body">
                      <a name="${anchor}"></a>
                      <div style="float: right;"><a href="#TOP">quick find</a></div>
                      <% 
                        curr_anchor = anchor
                        anchored = True 
                      %>
                    </td>
                  </tr>
                %endif
                ${render_row( role )}
                <% 
                  anchor_loc = anchors.index( anchor )
                  break 
                %>
              %endif
            %endfor
          %else:
            ${render_row( role )}
          %endif
          %if ctr % 2 == 1:
            </div>
          %endif
          <% ctr += 1 %>
        </tr>
      %endfor
    %endif
  </table>
</div>
