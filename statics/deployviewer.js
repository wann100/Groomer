!function(){function a(a){for(var b,c=[],d=/[&?]debugArtifacts?=([^&]+)/gi;b=d.exec(a);){var e=decodeURIComponent(b[1]);c=c.concat(e.split(","))}return c=c.map(function(a){var b=a.toLowerCase().replace(/\s/g,"");return"web"===b&&(b="wysiwyg"),b}).filter(function(a){return a}),c.reduce(function(a,b){return a[b]=!0,a},{})}function b(a){var b={};for(var c in a)b[c.toLowerCase()]=a[c].toLowerCase();return b}function c(){for(var a=window.location.search.toLowerCase().replace("?",""),b=a.split("&"),c=0;c<b.length;c++){var d=b[c].split("=");if("experiment"==d[0]){var e=d[1].split(":");window.rendererModel.runningExperiments[e[0]]=e[1]||"new"}}}function d(){window.rendererModel.runningExperiments=b(window.rendererModel.runningExperiments),c();var a=["common","viewer"];"preview"===window.viewMode&&a.push("preview");var d=rendererModel.runningExperiments;for(var e in d)a.push(e.toLowerCase()+":"+d[e].toLowerCase());return a}define.resource("tags",d()),define.resource("mode",{debug:"debug"===rendererModel.debugMode,test:!1}),define.resource("debugModeArtifacts",a(window.location.search)),define.deployment("wysiwyg.deployment.PrepViewer",function(a){a.atPhase(PHASES.BOOTSTRAP,function(){window.wixData&&resource.getResources(["dataFixer"],function(a){var b=a.dataFixer.fix(window.wixData);this.define.dataItem.multi(b.document_data),this.define.dataPropertyItem.multi(b.component_properties),this.define.dataThemeItem.multi(b.theme_data)})}),a.atPhase(PHASES.MANAGERS,function(a){a.createClassInstance("W.Layout","wysiwyg.viewer.managers.LayoutManager"),a.createClassInstance("W.Viewer","wysiwyg.viewer.managers.WViewManager"),a.createClassInstance("W.SiteMembers","wysiwyg.viewer.managers.SiteMembersManager"),a.createClassInstance("W.MessagesController","wysiwyg.viewer.utils.MessageViewController")}),a.atPhase(PHASES.POST_DEPLOY,function(a){if("preview"===window.viewMode)return null;if(window.siteHeader&&window.rendererModel&&"UGC"===rendererModel.documentType){var b=a.getClassManagerInstance();b.getClass("core.utils.BeatStatisticsAndKeepAlive",function(a){window.BeatStatisticsAndKeepAliveInstance=new a("hve",siteHeader.id,$$("title")[0].innerHTML,siteHeader.documentType,!1,rendererModel.metaSiteId,function(){})})}})})}(),resource.getResources(["mode","debugModeArtifacts","scriptLoader"],function(a){window.getIndexTopology.call(a,{debug:a.mode.debug,debugModeArtifacts:a.debugModeArtifacts},{aliases:{web:"wysiwyg"},exclude:{langs:!0,mock:!0,sitemembers:!0,ecommerce:W.isExperimentOpen("EcomArtifactDeploy")?void 0:!0},baseUrls:{external_apis:""},"main-artifacts":["ck-editor","bootstrap","sitemembers","ecommerce","langs","wixapps","core","tpa","skins","wysiwyg","html-test-framework","mock"]},function(b){define.resource("topology",b.all),a.mode.test&&b.manifestsUrls.unshift(getTestManifestFromTheSpecRunner()),define.resource("manifestsUrls",b.manifestsUrls),define.deployment("wysiwyg.deployment.Wysiwyg-Common",function(a){a.atPhase(PHASES.MANAGERS,function(a){a.createClassInstance("W.CookiesManager","wysiwyg.managers.WCookiesManager")})}),a.scriptLoader.loadAllIndexes(b.manifestsUrls,function(){define.resource("deployment",define.createBootstrapClassInstance("bootstrap.bootstrap.deploy.Deploy").init(window))})})}),define.deployment("core.deployment.DeployViewer",function(a){function b(a){if(window.W.isExperimentOpen("PageManagerRefactor2"))return c(a),void 0;if(!this.alreadyLoadedInPrev340&&(this.alreadyLoadedInPrev340=W.Viewer.isSiteReady(),(!window.viewMode||"site"===window.viewMode)&&LOG.isThisSiteInEventSampleRatio(wixEvents.LOAD_PAGE_DATA.sampleRatio))){for(var b=-1!==document.referrer.indexOf("editor.wix.com/html/editor"),d=deployStatus.logs.pageLoad||[],e=deployStatus.logs.pageDataLoad||[],f=deployStatus.logs.viewerRender||[],g=deployStatus.logs.phases||[],h={},i=0;i<d.length;++i){var j=d[i],l=j.pageId,m=h[l]=h[l]||{};m.steps=m.steps||[];var n={time:j.time,host:j.host,step:j.type};j.errorDesc&&(n.error=j.errorDesc.substr(0,50)),void 0!==j.httpsStatus&&(n.status=j.httpsStatus),m.steps.push(n),m.time=j.time,m.step=j.type}var o=-1,p=-1,q=-1,r=-1,s=-1,t=-1;e.length>0&&(p=e[0].time),e.length>1&&(q=e[1].time),f.length>2&&"site ready"===f[2].step&&(r=f[2].time,t=f[2].time),f.length>0&&(s=f[0].time),g.length>0&&(o=_.last(g).time);for(var u={},v=0,i=0;i<g.length;i++)u[i]=g[i].time-v,v=g[i].time;var w={isFromEditor:b,isMobile:W.Config.mobileConfig?W.Config.mobileConfig.isMobileOrTablet():"unknown",isLoaded:W.Viewer.isSiteReady(),siteReadyTime:r,classRepoIsReadyTime:deployStatus.classRepoIsReadyTime,experimentsIsReadyTime:deployStatus.experimentsIsReadyTime,deployment:{start:0,done:o,phases:u},pages:{start:p,done:q,pages:h},render:{start:s,done:t}};w.isEcom=!1;var x=deployStatus.logs.wixappsLoad||[];if(x.length>=1&&"loading ecom"==x[1].step&&(w.isEcom=!0),x.length){w.wixapps={start:x[0].time,done:_.last(x).time,phases:{}};for(var y=0,i=0,z=x.length;z>i;i++)w.wixapps.phases[i]=x[i].time-y,y=x[i].time}LOG.reportEvent(wixEvents.LOAD_PAGE_DATA,{c1:JSON.stringify(w),c2:JSON.stringify(k()),i1:a})}}function c(a){if(!this.alreadyLoadedInPrev340&&(this.alreadyLoadedInPrev340=W.Viewer.isSiteReady(),(!window.viewMode||"site"===window.viewMode)&&LOG.isThisSiteInEventSampleRatio(wixEvents.LOAD_PAGE_DATA.sampleRatio))){var b=-1!==document.referrer.indexOf("editor.wix.com/html/editor"),c={isFromEditor:b,isMobile:W.Config.mobileConfig?W.Config.mobileConfig.isMobileOrTablet():"unknown",isLoaded:W.Viewer.isSiteReady(),classRepoIsReadyTime:deployStatus.classRepoIsReadyTime,experimentsIsReadyTime:deployStatus.experimentsIsReadyTime};d(c),e(c),f(c),i(c),h(c),LOG.reportEvent(wixEvents.LOAD_PAGE_DATA,{c1:JSON.stringify(c),c2:JSON.stringify(k()),i1:a})}}function d(a){var b=deployStatus.logs.loadStaticHtml||[],c=-1,d=-1,e=-1,f=null,g=!1;b.length>0&&"start loading"===b[0].step&&(d=b[0].time),b.length>1&&"end loading"===b[1].step&&(c=b[1].time,f=b[1].errorDesc),b.length>2&&"dom ready"===b[2].step&&(e=b[2].time,g=b[2].hasGalleries),a.staticHtml={start:d,endLoading:c,done:e},e>0&&(a.staticHtml.hasTPAGalleries=g),f&&(a.staticHtml.hadErrors=!0)}function e(a){var b=deployStatus.logs.viewerRender||[],c=-1,d=-1,e=-1;b.length>1&&"site ready"===b[1].step&&(c=b[1].time,e=b[1].time),b.length>0&&(d=b[0].time),a.render={start:d,done:e},a.siteReadyTime=c}function f(a){var b=deployStatus.logs.pageLoad||[],c=g(b),d=c.pagesReport,e=c.startTime;a.pages={start:e,pages:d}}function g(a){for(var b={},c=-1,d=0;d<a.length;++d){var e=a[d],f=e.pageId,g=b[f]=b[f]||{};if(g.steps=g.steps||[],!g.error){var h={time:e.time,step:e.type};"start loading page data"===e.type&&(-1===c||e.time<c)&&(c=e.time),g.steps.push(h),g.time=e.time,g.step=e.type,e.errorDesc&&(g.error=e.errorDesc.substr(0,50))}}return{pagesReport:b,startTime:c}}function h(a){a.isEcom=!1;var b=deployStatus.logs.wixappsLoad||[];if(b.length>1&&"loading ecom"==b[1].step&&(a.isEcom=!0),b.length){a.wixapps={start:b[0].time,done:_.last(b).time,phases:{}};for(var c=0,d=0,e=b.length;e>d;d++)a.wixapps.phases[d]=b[d].time-c,c=b[d].time}}function i(a){var b=deployStatus.logs.phases||[],c=-1;b.length>0&&(c=_.last(b).time);for(var d={},e=0,f=0;f<b.length;f++)d[f]=b[f].time-e,e=b[f].time;a.deployment={start:0,done:c,phases:d}}function j(){function a(a,b){c[b].length<e&&c[b].push(a)}if(window._imagePerformance){for(var b={_100k:0,_200k:0,_300k:0,_400k:0,_500k:0,_over500k:0},c={_100k:[],_200k:[],_300k:[],_400k:[],_500k:[],_over500k:[]},d=0,e=3,f=0;f<window._imagePerformance.timing.length;f++){var g=window._imagePerformance.timing[f],h=g.size;1e5>h?(b._100k++,a(g,"_100k")):2e5>h?(b._200k++,a(g,"_200k")):3e5>h?(b._300k++,a(g,"_300k")):4e5>h?(b._400k++,a(g,"_400k")):5e5>h?(b._500k++,a(g,"_500k")):(b._over500k++,a(g,"_over500k")),g.hadError&&d++}var i={loading:window._imagePerformance.started-window._imagePerformance.timing.length,imagesBySize:b,imagesSamples:c,errors:d};LOG.reportEvent(wixEvents.LOAD_IMAGES_DATA,{c1:JSON.stringify(i)})}}function k(){function a(a,b){return a==b?0:Number(a)>Number(b)?-1:1}for(var b,c={},d=Object.keys(deployStatus.files),e=0;e<d.length;e++)b=deployStatus.files[d[e]].end-deployStatus.files[d[e]].start,c[b]=d[e];var f=Object.keys(c);f.reverse(a);for(var g,h,i=f.slice(0,10),j={},e=0;e<i.length;e++)g=c[i[e]].split("/"),h=/index\.json/.test(g[g.length-1])||/index\.debug\.json/.test(g[g.length-1])?g[g.length-3]:g[g.length-1],h=encodeURIComponent(h),j[h]=i[e];return j}setTimeout(function(){b(10),j()},1e4),setTimeout(function(){b(20)},2e4),setTimeout(function(){b(30)},3e4),a.atPhase(PHASES.BOOTSTRAP,function(){var a,b=window.rendererModel&&window.rendererModel.runningExperiments&&window.rendererModel.runningExperiments;for(var c in b)if("initfromstatic"===c.toLowerCase()){a=b[c];break}var d=window.location.search.toLocaleLowerCase().indexOf("experiment=initfromstatic:new")>=0,e=a&&"new"===a.toLowerCase();if(d||e){for(var f=document.querySelectorAll("head *"),g=document.querySelectorAll("body *"),h=0;h<f.length;h++)f[h].serverGenerated=!0,f[h].setAttribute("serverGenerated",!0);for(h=0;h<g.length;h++)g[h].serverGenerated=!0,g[h].setAttribute("serverGenerated",!0)}}),a.atPhase(PHASES.INIT,function(){function a(a,e){var f=c(a),h=b(f);h&&h[f.componentName]&&(e=d(e,h[f.componentName])),W.Experiments.applyExperiments("Editor."+a,e,g)}function b(a){var b;try{b=this.define.getDefinition("component","Editor."+a.componentNamespace)}catch(c){b=null}return b}function c(a){var b={},c=a.lastIndexOf(".");return b.componentNamespace=a.substring(0,c),b.componentName=a.substring(c+1),b}function d(a,b){var c,d=this.define.createBootstrapClassInstance("bootstrap.managers.experiments.ExperimentStrategy"),c=this.define.createBootstrapClassInstance("core.managers.component.ComponentDefinition"),e=a;"function"==typeof a&&(e=new c,a(e));var f=c;return b(f,d),e.resources(d._mergeField_(e._resources_,f._resources_)),e.binds(d._mergeField_(e._binds_,f._binds_)),e.traits(f._traits_||e._traits_),e.utilize(d._mergeField_(e._imports_,f._imports_)),e.statics(d._mergeObjects_(e._statics_,f._statics_)),e.fields(d._mergeObjects_(e._fields_,f._fields_)),e.methods(d._mergeObjects_(e._methods_,f._methods_)),e.states(d._mergeField_(e._states_,f._states_)),e.panel(f._panel_),e.styles(f._styles_),e.helpIds(f._helpIds_),e.toolTips(f._toolTips_),e}function e(){try{if("preview"!==window.viewMode)return;if(!(window.wixData&&wixData.document_data&&wixData.document_data.MAIN_MENU&&wixData.document_data.MAIN_MENU.items))return;var a=wixData.document_data.MAIN_MENU.items,b=$("SITE_PAGES");if(!b)return;for(var c=0;c<a.length;c++)if(a[c].refId&&f(a[c].refId,b),a[c].items)for(var d=0;d<a[c].items.length;d++)a[c].items[d].refId&&f(a[c].items[d].refId,b)}catch(e){}}function f(a,b){try{var c=a.substr(1);if(null==b.getElementById(c)){var d=new Element("div",{id:c,dataquery:a,comp:"mobile.core.components.Page",styleid:"p1","class":"initHidden",x:"0",y:"0",width:"980",height:"600",skin:"wysiwyg.viewer.skins.page.BasicPageSkin"});b.appendChild(d),wixData.document_data[c].hidePage=!0,LOG.reportError(wixErrors.RESTORED_BLANK_PAGE_WHERE_MISSING_PAGE_DATA)}}catch(e){}}var g;W.Experiments.isDeployed("PerfExperiments")&&(g="ExperimentComponentPlugin"),W.ComponentLifecycle.setComponentErrorHandler(function(a,b,c){"use strict";var d=a.component.$className;LOG.reportError(wixErrors.COMPONENT_ERROR,d,c,b.stack)}),W.Config.env.$isEditorViewerFrame&&W.Components.setComponentDefinitionModifier(function(b,c){a(b,c)}),resource.getResourceValue("status.structure.loaded",function(a){if(!a)throw new Error("Site structure failed to load");e(),W.Viewer.initiateSite()})}),a.atPhase(PHASES.MANAGERS,function(a){W.Experiments.isDeployed({EditorScripting:"New"})&&a.createClassInstance("W.ScriptingManager","wysiwyg.common.managers.ScriptingManager")}),a.atPhase(PHASES.POST_DEPLOY,function(){if(W.Experiments.isDeployed({verifypremium:"New"})&&W.Classes.getClass("wysiwyg.viewer.VerifyPremium",function(a){var b=new a;b.verify()}),W.Experiments.isDeployed({ClientSideUserGUIDCookie:"New"})&&"WixSite"==rendererModel.documentType&&resource.getResourceValue("scriptLoader",function(a){a.loadScript({url:"http://static.wix.com/services/third-party/misc/ClientSideUserGUIDCookie.js"},{})}),W.Experiments.isDeployed({Feedme:"New"})){var a=W.Utils.getQueryStringParamsAsObject();if("true"===a.feedback){var b=new Element("div",{id:"reviewsContainer"});document.body.appendChild(b),W.Components.createComponent("wysiwyg.common.components.sitefeedbackpanel.viewer.SiteFeedbackPanel","wysiwyg.common.components.sitefeedbackpanel.viewer.skins.SiteFeedbackPanelSkin",null,null,null,function(a){a.getViewNode().insertInto(b)}.bind(this))}}})});