(function(){var b=Handlebars.template,a=Handlebars.templates=Handlebars.templates||{};a.tool_form=b(function(f,m,e,l,k){e=e||f.helpers;var i="",c,h,g="function",j=this.escapeExpression,n=this;function d(s,r){var p="",q,o;p+='\n        <div class="form-row">\n            <label for="';o=e.name;if(o){q=o.call(s,{hash:{}})}else{q=s.name;q=typeof q===g?q():q}p+=j(q)+'">';o=e.label;if(o){q=o.call(s,{hash:{}})}else{q=s.label;q=typeof q===g?q():q}p+=j(q)+':</label>\n            <div class="form-row-input">\n                ';o=e.html;if(o){q=o.call(s,{hash:{}})}else{q=s.html;q=typeof q===g?q():q}if(q||q===0){p+=q}p+='\n            </div>\n            <div class="toolParamHelp" style="clear: both;">\n                ';o=e.help;if(o){q=o.call(s,{hash:{}})}else{q=s.help;q=typeof q===g?q():q}p+=j(q)+'\n            </div>\n            <div style="clear: both;"></div>\n        </div>\n        ';return p}i+='<div class="toolFormTitle">';h=e.name;if(h){c=h.call(m,{hash:{}})}else{c=m.name;c=typeof c===g?c():c}i+=j(c)+" (version ";h=e.version;if(h){c=h.call(m,{hash:{}})}else{c=m.version;c=typeof c===g?c():c}i+=j(c)+')</div>\n    <div class="toolFormBody">\n        ';c=m.inputs;c=e.each.call(m,c,{hash:{},inverse:n.noop,fn:n.program(1,d,k)});if(c||c===0){i+=c}i+='\n    </div>\n    <div class="form-row form-actions">\n    <input type="submit" class="btn btn-primary" name="runtool_btn" value="Execute">\n</div>\n<div class="toolHelp">\n    <div class="toolHelpBody">';h=e.help;if(h){c=h.call(m,{hash:{}})}else{c=m.help;c=typeof c===g?c():c}i+=j(c)+"</div>\n</div>";return i})})();