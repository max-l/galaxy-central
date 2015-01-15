// dependencies
define(["utils/utils"],function(e){return Backbone.View.extend({options:{class_add:"upload-icon-button fa fa-square-o",class_remove:"upload-icon-button fa fa-check-square-o"},initialize:function(t){this.app=t;var n=this;this.setElement(this._template()),e.get({url:galaxy_config.root+"api/ftp_files",success:function(e){n._fill(e)},error:function(){n._fill()}})},events:{mousedown:function(e){e.preventDefault()}},_fill:function(t){var n=this;if(t&&t.length>0){this.$el.find("#upload-ftp-content").html($(this._templateTable()));var r=0;for(key in t)this.add(t[key]),r+=t[key].size;this.$el.find("#upload-ftp-number").html(t.length+" files"),this.$el.find("#upload-ftp-disk").html(e.bytesToString(r,!0));var s=this.$el.find("#selectAll");this._updateSelectAll(s),s.on("click",function(){var e=$(this).parents().find("tr.upload-ftp-row>td>div"),t=e.length;$this=$(this);var r=!$this.hasClass("fa-check-square-o");for(i=0;i<t;i++)r?e.eq(i).hasClass("fa-square-o")&&e.eq(i).trigger("addToUpBox"):e.eq(i).hasClass("fa-check-square-o")&&e.eq(i).trigger("addToUpBox");n._updateSelectAll(s)})}else this.$el.find("#upload-ftp-content").html($(this._templateInfo()));this.$el.find("#upload-ftp-wait").hide()},add:function(e){var t=this,n=$(this._templateRow(e)),r=n.find(".icon");$(this.el).find("tbody").append(n);var i="";this._find(e)?i=this.options.class_remove:i=this.options.class_add,r.addClass(i),n.on("addToUpBox",function(){var n=t._find(e);r.removeClass(),n?(t.app.collection.remove(n),r.addClass(t.options.class_add)):(t.app.uploadbox.add([{mode:"ftp",name:e.path,size:e.size,path:e.path}]),r.addClass(t.options.class_remove))}),n.on("click",function(){r.trigger("addToUpBox");var e=r.parents().find("#selectAll");t._updateSelectAll(e)})},_updateSelectAll:function(e){var t=e.parents().find("tr.upload-ftp-row>td>div"),n=e.parents().find("tr.upload-ftp-row>td>div.fa-check-square-o"),r=t.length,i=n.length;i>0&&i!==r?(e.removeClass("fa-square-o fa-check-square-o"),e.addClass("fa-minus-square-o")):i===r?(e.removeClass("fa-square-o fa-minus-square-o"),e.addClass("fa-check-square-o")):i===0&&(e.removeClass("fa-check-square-o fa-minus-square-o"),e.addClass("fa-square-o"))},_find:function(e){var t=this.app.collection.where({file_path:e.path}),n=null;for(var r in t){var i=t[r];i.get("status")=="init"&&i.get("file_mode")=="ftp"&&(n=i.get("id"))}return n},_templateRow:function(t){return'<tr class="upload-ftp-row" style="cursor: pointer;"><td><div class="icon"/></td><td style="width: 200px"><p style="width: inherit; word-wrap: break-word;">'+t.path+"</p></td>"+'<td style="white-space: nowrap;">'+e.bytesToString(t.size)+"</td>"+'<td style="white-space: nowrap;">'+t.ctime+"</td>"+"</tr>"},_templateTable:function(){return'<span style="whitespace: nowrap; float: left;">Available files: </span><span style="whitespace: nowrap; float: right;"><span class="upload-icon fa fa-file-text-o"/><span id="upload-ftp-number"/>&nbsp;&nbsp;<span class="upload-icon fa fa-hdd-o"/><span id="upload-ftp-disk"/></span><table class="grid" style="float: left;"><thead><tr><th><div id="selectAll" class="upload-icon-button fa fa-square-o" ></th><th>Name</th><th>Size</th><th>Created</th></tr></thead><tbody></tbody></table>'},_templateInfo:function(){return'<div class="upload-ftp-warning warningmessage">Your FTP directory does not contain any files.</div>'},_template:function(){return'<div class="upload-ftp"><div id="upload-ftp-wait" class="upload-ftp-wait fa fa-spinner fa-spin"/><div class="upload-ftp-help">This Galaxy server allows you to upload files via FTP. To upload some files, log in to the FTP server at <strong>'+this.app.options.ftp_upload_site+"</strong> using your Galaxy credentials (email address and password).</div>"+'<div id="upload-ftp-content"></div>'+"<div>"}})});