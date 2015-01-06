define(["galaxy.masthead"],function(b){var a=Backbone.Model.extend({options:null,masthead:null,initialize:function(c){this.options=c.config;this.masthead=c.masthead;this.create()},create:function(){var e=new b.GalaxyMastheadTab({id:"analysis",title:"Analyze Data",content:"",title_attribute:"Analysis home view"});this.masthead.append(e);var g={id:"workflow",title:"Workflow",content:"workflow",title_attribute:"Chain tools into workflows"};if(!this.options.user.valid){g.disabled=true}var d=new b.GalaxyMastheadTab(g);this.masthead.append(d);var i=new b.GalaxyMastheadTab({id:"shared",title:"Shared Data",content:"library/index",title_attribute:"Access published resources"});i.add({title:"Data Libraries",content:"library/index"});i.add({title:"Data Libraries Beta",content:"library/list",divider:true});i.add({title:"Published Histories",content:"history/list_published"});i.add({title:"Published Workflows",content:"workflow/list_published"});i.add({title:"Published Visualizations",content:"visualization/list_published"});i.add({title:"Published Pages",content:"page/list_published"});this.masthead.append(i);if(this.options.user.requests){var j=new b.GalaxyMastheadTab({id:"lab",title:"Lab"});j.add({title:"Sequencing Requests",content:"requests/index"});j.add({title:"Find Samples",content:"requests/find_samples_index"});j.add({title:"Help",content:this.options.lims_doc_url});this.masthead.append(j)}var c={id:"visualization",title:"Visualization",content:"visualization/list",title_attribute:"Visualize datasets"};if(!this.options.user.valid){c.disabled=true}var m=new b.GalaxyMastheadTab(c);if(this.options.user.valid){m.add({title:"New Track Browser",content:"visualization/trackster",target:"_frame"});m.add({title:"Saved Visualizations",content:"visualization/list",target:"_frame"})}this.masthead.append(m);if(this.options.enable_cloud_launch){var f=new b.GalaxyMastheadTab({id:"cloud",title:"Cloud",content:"cloudlaunch/index"});f.add({title:"New Cloud Cluster",content:"cloudlaunch/index"});this.masthead.append(f)}if(this.options.is_admin_user){var h=new b.GalaxyMastheadTab({id:"admin",title:"Admin",content:"admin",extra_class:"admin-only",title_attribute:"Administer this Galaxy"});h.add({title:"Beta Admin",content:"admin/beta",target:"_frame"});this.masthead.append(h)}var l=new b.GalaxyMastheadTab({id:"help",title:"Help",title_attribute:"Support, contact, and community hubs"});if(this.options.biostar_url){l.add({title:"Galaxy Biostar",content:this.options.biostar_url_redirect,target:"_blank"});l.add({title:"Ask a question",content:"biostar/biostar_question_redirect",target:"_blank"})}l.add({title:"Support",content:this.options.support_url,target:"_blank"});l.add({title:"Search",content:this.options.search_url,target:"_blank"});l.add({title:"Mailing Lists",content:this.options.mailing_lists,target:"_blank"});l.add({title:"Videos",content:this.options.screencasts_url,target:"_blank"});l.add({title:"Wiki",content:this.options.wiki_url,target:"_blank"});l.add({title:"How to Cite Galaxy",content:this.options.citation_url,target:"_blank"});if(this.options.terms_url){l.add({title:"Terms and Conditions",content:this.options.terms_url,target:"_blank"})}this.masthead.append(l);if(!this.options.user.valid){var k=new b.GalaxyMastheadTab({id:"user",title:"User",extra_class:"loggedout-only",title_attribute:"Account registration or login"});k.add({title:"Login",content:"user/login",target:"galaxy_main"});if(this.options.allow_user_creation){k.add({title:"Register",content:"user/create",target:"galaxy_main"})}this.masthead.append(k)}else{var k=new b.GalaxyMastheadTab({id:"user",title:"User",extra_class:"loggedin-only",title_attribute:"Account preferences and saved data"});k.add({title:"Logged in as "+this.options.user.email});k.add({title:"Preferences",content:"user?cntrller=user",target:"galaxy_main"});k.add({title:"Custom Builds",content:"user/dbkeys",target:"galaxy_main"});k.add({title:"Logout",content:"user/logout",target:"_top",divider:true});k.add({title:"Saved Histories",content:"history/list",target:"galaxy_main"});k.add({title:"Saved Datasets",content:"dataset/list",target:"galaxy_main"});k.add({title:"Saved Pages",content:"page/list",target:"_top"});k.add({title:"API Keys",content:"user/api_keys?cntrller=user",target:"galaxy_main"});if(this.options.use_remote_user){k.add({title:"Public Name",content:"user/edit_username?cntrller=user",target:"galaxy_main"})}this.masthead.append(k)}if(this.options.active_view){this.masthead.highlight(this.options.active_view)}}});return{GalaxyMenu:a}});