<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

%if message:
    ${render_msg( message, status )}
%endif

<div class="toolForm">
    <form name="user_api_keys" id="user_api_keys" action="${h.url_for( controller='user', action='api_keys' )}" method="post" >
        <div class="toolFormTitle">Web API Key</div>
        <div class="toolFormBody">
            <div class="form-row">
                <label>Current API key:</label>
                %if user.api_keys:
                    ${user.api_keys[0].key}
                %else:
                    none set
                %endif
            </div>
            <div class="form-row">
                <input type="submit" name="new_api_key_button" value="Generate a new key now"/>
                %if user.api_keys:
                    (invalidates old key)
                %endif
                <div class="toolParamHelp" style="clear: both;">
                    An API key will allow you to access Galaxy via its web
                    API (documentation forthcoming).  Please note that
                    <strong>this key acts as an alternate means to access
                    your account, and should be treated with the same care
                    as your login password</strong>.
                </div>
            </div>
        </div>
    </form>
</div>
