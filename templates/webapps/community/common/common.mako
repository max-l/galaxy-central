<%def name="common_misc_javascripts()">
    <script type="text/javascript">
        function checkAllFields( name )
        {
            var chkAll = document.getElementById( 'checkAll' );
            var checks = document.getElementsByTagName( 'input' );
            var boxLength = checks.length;
            var allChecked = false;
            var totalChecked = 0;
            if ( chkAll.checked == true )
            {
                for ( i=0; i < boxLength; i++ )
                {
                    if ( checks[i].name.indexOf( name ) != -1 )
                    {
                       checks[i].checked = true;
                    }
                }
            }
            else
            {
                for ( i=0; i < boxLength; i++ )
                {
                    if ( checks[i].name.indexOf( name ) != -1 )
                    {
                       checks[i].checked = false
                    }
                }
            }
        }
    </script>
</%def>

<%def name="escape_html_add_breaks( value )">
    <%
        from galaxy import eggs
        eggs.require('markupsafe')
        import markupsafe
        value = str( markupsafe.escape( value ) ).replace( '\n', '<br/>' )
    %>
    ${value}
</%def>

<%def name="render_star_rating( name, rating, disabled=False )">
    <%
        if disabled:
            disabled_str = ' disabled="disabled"'
        else:
            disabled_str = ''
        html = ''
        for index in range( 1, 6 ):
            html += '<input name="%s" type="radio" class="star" value="%s" %s' % ( str( name ), str( index ), disabled_str )
            if rating > ( index - 0.5 ) and rating < ( index + 0.5 ):
                html += ' checked="checked"'
            html += '/>'
    %>
    ${html}
</%def>

<%def name="render_readme( readme_text )">
    <style type="text/css">
        #readme_table{ table-layout:fixed;
                       width:100%;
                       overflow-wrap:normal;
                       overflow:hidden;
                       border:0px; 
                       word-break:keep-all;
                       word-wrap:break-word;
                       line-break:strict; }
    </style>
    <div class="toolForm">
        <div class="toolFormTitle">Repository README file (may contain important installation or license information)</div>
        <div class="toolFormBody">
            <div class="form-row">
                <table id="readme_table">
                    <tr><td>${ escape_html_add_breaks( readme_text ) }</td></tr>
                </table>
            </div>
        </div>
    </div>
</%def>

<%def name="render_long_description( description_text )">
    <style type="text/css">
        #description_table{ table-layout:fixed;
                            width:100%;
                            overflow-wrap:normal;
                            overflow:hidden;
                            border:0px; 
                            word-break:keep-all;
                            word-wrap:break-word;
                            line-break:strict; }
    </style>
    <div class="form-row">
        <label>Detailed description:</label>
        <table id="description_table">
            <tr><td>${ escape_html_add_breaks( description_text ) }</td></tr>
        </table>
        <div style="clear: both"></div>
    </div>
</%def>
