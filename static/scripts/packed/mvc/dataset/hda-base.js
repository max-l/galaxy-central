define(["mvc/dataset/hda-model"],function(b){var a=Backbone.View.extend(LoggableMixin).extend({tagName:"div",className:"historyItemContainer",fxSpeed:"fast",initialize:function(c){if(c.logger){this.logger=this.model.logger=c.logger}this.log(this+".initialize:",c);this.defaultPrimaryActionButtonRenderers=[this._render_showParamsButton];this.expanded=c.expanded||false;this._setUpListeners()},_setUpListeners:function(){this.model.on("change",function(d,c){if(this.model.changedAttributes().state&&this.model.inReadyState()&&this.expanded&&!this.model.hasDetails()){this.model.fetch()}else{this.render()}},this)},render:function(){var d=this,g=this.model.get("id"),e=this.model.get("state"),c=$("<div/>").attr("id","historyItem-"+g),f=(this.$el.children().size()===0);this.$el.attr("id","historyItemContainer-"+g);this.$el.find("[title]").tooltip("destroy");this.urls=this.model.urls();c.addClass("historyItemWrapper").addClass("historyItem").addClass("historyItem-"+e);c.append(this._render_warnings());c.append(this._render_titleBar());this._setUpBehaviors(c);this.body=$(this._render_body());c.append(this.body);this.$el.fadeOut(this.fxSpeed,function(){d.$el.children().remove();d.$el.append(c).fadeIn(d.fxSpeed,function(){d.log(d+" rendered:",d.$el);var h="rendered";if(f){h+=":initial"}else{if(d.model.inReadyState()){h+=":ready"}}d.trigger(h)})});return this},_setUpBehaviors:function(c){c=c||this.$el;make_popup_menus(c);c.find("[title]").tooltip({placement:"bottom"})},_render_warnings:function(){return $(jQuery.trim(a.templates.messages(this.model.toJSON())))},_render_titleBar:function(){var c=$('<div class="historyItemTitleBar" style="overflow: hidden"></div>');c.append(this._render_titleButtons());c.append('<span class="state-icon"></span>');c.append(this._render_titleLink());return c},_render_titleButtons:function(){var c=$('<div class="historyItemButtons"></div>');c.append(this._render_displayButton());return c},_render_displayButton:function(){if((this.model.get("state")===b.HistoryDatasetAssociation.STATES.NOT_VIEWABLE)||(this.model.get("state")===b.HistoryDatasetAssociation.STATES.NEW)||(!this.model.get("accessible"))){this.displayButton=null;return null}var d={icon_class:"display",target:"galaxy_main"};if(this.model.get("purged")){d.enabled=false;d.title=_l("Cannot display datasets removed from disk")}else{if(this.model.get("state")===b.HistoryDatasetAssociation.STATES.UPLOAD){d.enabled=false;d.title=_l("This dataset must finish uploading before it can be viewed")}else{d.title=_l("View data");d.href=this.urls.display;var c=this;d.on_click=function(){Galaxy.frame_manager.frame_new({title:"Data Viewer: "+c.model.get("name"),type:"url",location:"center",content:c.urls.display})}}}this.displayButton=new IconButtonView({model:new IconButton(d)});return this.displayButton.render().$el},_render_titleLink:function(){return $(jQuery.trim(a.templates.titleLink(this.model.toJSON())))},_render_hdaSummary:function(){var c=_.extend(this.model.toJSON(),{urls:this.urls});return a.templates.hdaSummary(c)},_render_primaryActionButtons:function(e){var c=this,d=$("<div/>").attr("id","primary-actions-"+this.model.get("id"));_.each(e,function(f){d.append(f.call(c))});return d},_render_downloadButton:function(){if(this.model.get("purged")||!this.model.hasData()){return null}var c=a.templates.downloadLinks(_.extend(this.model.toJSON(),{urls:this.urls}));return $(c.trim())},_render_showParamsButton:function(){this.showParamsButton=new IconButtonView({model:new IconButton({title:_l("View details"),href:this.urls.show_params,target:"galaxy_main",icon_class:"information"})});return this.showParamsButton.render().$el},_render_displayAppArea:function(){return $("<div/>").addClass("display-apps")},_render_displayApps:function(e){e=e||this.$el;var f=e.find("div.display-apps"),c=this.model.get("display_types"),d=this.model.get("display_apps");if((!this.model.hasData())||(!e||!e.length)||(!f.length)){return}f.html(null);if(!_.isEmpty(c)){f.append(a.templates.displayApps({displayApps:c}))}if(!_.isEmpty(d)){f.append(a.templates.displayApps({displayApps:d}))}},_render_peek:function(){var c=this.model.get("peek");if(!c){return null}return $("<div/>").append($("<pre/>").attr("id","peek"+this.model.get("id")).addClass("peek").append(c))},_render_body:function(){var c=$("<div/>").attr("id","info-"+this.model.get("id")).addClass("historyItemBody").attr("style","display: none");if(this.expanded){this._render_body_html(c);c.show()}return c},_render_body_html:function(e){e.empty();var c=this.model.get("state");var f="_render_body_"+c,d=this[f];if(_.isFunction(d)){this[f](e)}else{e.append($('<div>Error: unknown dataset state "'+this.model.get("state")+'".</div>'))}e.append('<div style="clear: both"></div>');this._setUpBehaviors(e)},_render_body_new:function(d){var c=_l("This is a new dataset and not all of its data are available yet");d.append($("<div>"+_l(c)+"</div>"))},_render_body_noPermission:function(c){c.append($("<div>"+_l("You do not have permission to view this dataset")+"</div>"))},_render_body_upload:function(c){c.append($("<div>"+_l("Dataset is uploading")+"</div>"))},_render_body_queued:function(c){c.append($("<div>"+_l("Job is waiting to run")+"</div>"));c.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_paused:function(c){c.append($("<div>"+_l('Job is paused. Use the "Resume Paused Jobs" in the history menu to resume')+"</div>"));c.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_running:function(c){c.append("<div>"+_l("Job is currently running")+"</div>");c.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_error:function(c){if(!this.model.get("purged")){c.append($("<div>"+this.model.get("misc_blurb")+"</div>"))}c.append((_l("An error occurred with this dataset")+": <i>"+$.trim(this.model.get("misc_info"))+"</i>"));c.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers.concat([this._render_downloadButton])))},_render_body_discarded:function(c){c.append("<div>"+_l("The job creating this dataset was cancelled before completion")+".</div>");c.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_setting_metadata:function(c){c.append($("<div>"+_l("Metadata is being auto-detected")+".</div>"))},_render_body_empty:function(c){c.append($("<div>"+_l("No data")+": <i>"+this.model.get("misc_blurb")+"</i></div>"));c.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_failed_metadata:function(c){c.append($(a.templates.failedMetadata(_.extend(this.model.toJSON(),{urls:this.urls}))));this._render_body_ok(c)},_render_body_ok:function(c){c.append(this._render_hdaSummary());if(this.model.isDeletedOrPurged()){c.append(this._render_primaryActionButtons([this._render_downloadButton,this._render_showParamsButton]));return}c.append(this._render_primaryActionButtons([this._render_downloadButton,this._render_showParamsButton]));c.append('<div class="clear"/>');c.append(this._render_displayAppArea());this._render_displayApps(c);c.append(this._render_peek())},events:{"click .historyItemTitle":"toggleBodyVisibility"},toggleBodyVisibility:function(d,c){c=(c===undefined)?(!this.body.is(":visible")):(c);if(c){this.expandBody()}else{this.collapseBody()}},expandBody:function(){var c=this;function d(){c._render_body_html(c.body);c.body.slideDown(c.fxSpeed,function(){c.expanded=true;c.trigger("body-expanded",c.model.get("id"))})}if(this.model.inReadyState()&&!this.model.hasDetails()){this.model.fetch().done(function(e){d()})}else{d()}},collapseBody:function(){var c=this;this.body.slideUp(c.fxSpeed,function(){c.expanded=false;c.trigger("body-collapsed",c.model.get("id"))})},remove:function(d){var c=this;this.$el.fadeOut(c.fxSpeed,function(){c.$el.remove();c.off();if(d){d()}})},toString:function(){var c=(this.model)?(this.model+""):("(no model)");return"HDABaseView("+c+")"}});a.templates={warningMsg:Handlebars.templates["template-warningmessagesmall"],messages:Handlebars.templates["template-hda-warning-messages"],titleLink:Handlebars.templates["template-hda-titleLink"],hdaSummary:Handlebars.templates["template-hda-hdaSummary"],downloadLinks:Handlebars.templates["template-hda-downloadLinks"],failedMetadata:Handlebars.templates["template-hda-failedMetadata"],displayApps:Handlebars.templates["template-hda-displayApps"]};return{HDABaseView:a}});