// Recall is a program for storing bookmarks of different things
// Copyright (C) 2012  Cal Paterson

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.

// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

core.add(
    "about",
    function(){
        var sandbox;

        var show = function(){
            sandbox.find()[0].hidden = false;
            return false;
        };

        var hide = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };
        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("show-about", show);
            sandbox.subscribe("hide-all", hide);
        };
    }());

core.add(
    "verify-email",
    function(){
        var sandbox;

        var token;

        var verify = function(){
            var button = sandbox.find("#v-e-submit")[0];
            button.classList.add("disabled");
            button.textContent = "Verifying...";

            sandbox.publish(
            "verify-email", {
                "email_key": token,
                "email": sandbox.find("#v-e-email")[0].value,
                "password": sandbox.find("#v-e-password")[0].value,
                "success": function(){
                    sandbox.publish("show-post-login");
                },
                "failure": failure
            });
            return false;
        };

        var show = function(data){
            sandbox.find()[0].hidden = false;
            token = data.split("/")[2];
            return false;
        };

        var hide = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };

        var failure = function(){
            var button = sandbox.find("#v-e-submit")[0];
            button.textContent = "Try Again";
            button.classList.remove("disabled");
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.bind("#v-e-submit", "click", verify);
            sandbox.subscribe("show-verify-email", show);
            sandbox.subscribe("hide-all", hide);
        };
    }());

core.add(
    "request-invite-form",
    function(){
        var sandbox;

        var typeShowing = "#r-i-real-name";

        var send = function(){
            var button = sandbox.find("#r-i-submit")[0];
            button.classList.add("disabled");
            button.textContent = "Sending...";

            var data = {};

            data.email = sandbox.find("#r-i-email")[0].value;
            if (data.email.indexOf("@") === -1){
                failure();
                return false;
            }

            var typeSelect = sandbox.find("#r-i-type")[0];
            if (typeSelect.selectedIndex === 0){
                data.firstName = sandbox.find("#r-i-first-name")[0].value;
                data.surname = sandbox.find("#r-i-surname")[0].value;
                if (data.firstName === "" || data.surname === ""){
                    failure();
                    return false;
                }
            } else if (typeSelect.selectedIndex === 1){
                data.pseudonym = sandbox.find("#r-i-pseudonym")[0].value;
                if (data.pseudonym === ""){
                    failure();
                    return false;
                }
            }

            sandbox.asynchronous(
                function(status, content){
                    if(status !== 202){
                        failure();
                    } else {
                        success();
                    }
                },
                "post",
                recall_config["api-base-url"] + "/people/" + data.email + "/",
                JSON.stringify(data),
                null,
                {"Content-Type": "application/json"}
                );
            return false;
        };

        var success = function(){
            var button = sandbox.find("#r-i-submit")[0];
            button.textContent = "Sent!";
        };

        var failure = function(){
            var button = sandbox.find("#r-i-submit")[0];
            button.textContent = "Error (try again?)";
            button.classList.remove("disabled");
        };

        var changeType = function(event){
            var realNameID = "#r-i-real-name";
            var pseudonymID = "#r-i-pseudonym-div";
            if (typeShowing === realNameID){
                sandbox.find(realNameID)[0].hidden = true;
                sandbox.find(pseudonymID)[0].hidden = false;
                typeShowing = pseudonymID;
            } else if (typeShowing === pseudonymID){
                sandbox.find(pseudonymID)[0].hidden = true;
                sandbox.find(realNameID)[0].hidden = false;
                typeShowing = realNameID;
            }
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.bind("#r-i-submit", "click", send);
            sandbox.bind("#r-i-type", "change", changeType);
        };
    }());

core.add(
    "search",
    function()
    {
        var sandbox;

        var hadAuthLastTime = false;

        var search = function(event){
            var button = sandbox.find("#v-search-button")[0];
            button.classList.add("disabled");
            button.textContent = "Searching...";
            var displayMarks = function(marks){
                sandbox.deleteContentsOf("#list-of-marks");
                if(marks.length > 1){
                    for (var i = 0; i < marks.length; i++){
                        sandbox.append("#list-of-marks", markToElement(marks[i]));
                    }
                    button.classList.remove("disabled");
                    button.textContent = "Seach Again?";
                } else {
                    button.classList.remove("disabled");
                    button.textContent = "No results!";
                }

            };
            sandbox.publish("get-marks?",
                            { "q": sandbox.find("#v-search-field")[0].value,
                              "callback": displayMarks });
            return false;
        };
        
        var humanTime = function(then){
            var then_ = new Date(then * 1000);
            // var minute = new Date(60 * 1000);
            // var hour = new Date(minute * 60);
            // var day = new Date(hour * 24);
            // var since = new Date() - then_;
            // if (since > day){
            return then_.toLocaleTimeString() +
                " - " + then_.toLocaleDateString();
            // } else if (since > hour) {
            //     return "some hours ago";
            // } else if (since > minute) {
            //     return "some minutes ago";
            // } else {
            //     return "seconds ago";
            // }
        };

        var markToElement = function(mark){
            if (mark.hasOwnProperty("hyperlink")){
                var template = sandbox.find("#hyperlink-template")[0];
                var hyperlink = template.cloneNode(true);
                hyperlink.id = "mark-" + mark["@"] + "-" + mark["~"];
                sandbox.offdom.find(hyperlink, ".who")[0].textContent = mark["@"];
                sandbox.offdom.find(hyperlink, ".hyperlink-url")[0].href = mark.hyperlink;
                sandbox.offdom.find(hyperlink, ".hyperlink-title")[0].textContent = mark.title;
                sandbox.offdom.find(hyperlink, ".when")[0].textContent = humanTime(mark["~"]);
                return hyperlink;
            } else if (mark.hasOwnProperty("#")) {
                var comment = sandbox.find("#comment-template")[0].cloneNode(true);
                comment.id = "mark-" + mark["@"] + "-" + mark["~"];
                sandbox.offdom.find(comment, ".who")[0].textContent = mark["@"];
                sandbox.offdom.find(comment, ".what")[0].textContent = mark["#"];
                sandbox.offdom.find(comment, ".when")[0].textContent = humanTime(mark["~"]);
                return comment;
            }
        };

        var show = function(){
            sandbox.find()[0].hidden = false;
            return false;
        };

        var hide = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("show-search", show);
            sandbox.subscribe("hide-all", hide);
            sandbox.bind("#v-search-button", "click", search);
        };
    }());

core.add(
    "getting-started",
    function(){
        var sandbox;

        var hide = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };

        var show = function(){
            sandbox.find()[0].hidden = false;
            return false;
        };
        var netscapeElementToMark = function(element, email){
            var htmlDecode = function(text){
                var div = document.createElement("div");
                div.innerHTML = text;
                return div.textContent;
            };
            if (!element.attributes.hasOwnProperty("ADD_DATE")){
                // This is not a bookmark, or the bookmark has no date
                return null;
            }
            var mark = {
                "hyperlink": element.attributes.HREF.nodeValue,
                "~": parseInt(element.attributes.ADD_DATE.nodeValue, 10),
                "title": htmlDecode(element.textContent),
                "@": localStorage.getItem("authorisationService$email") // FIXME: hack
            };
            if (element.attributes.hasOwnProperty("PRIVATE")){
                if (element.attributes.PRIVATE.nodeValue === "1"){
                    mark["%private"] = true;
                }
            }
            if (element.attributes.hasOwnProperty("TOREAD")){
                if (element.attributes.TOREAD.nodeValue === "1"){
                    mark.unread = true;
                }
            }
            if (element.attributes.hasOwnProperty("TAGS")){
                var string = element.attributes.TAGS.nodeValue;
                mark["%tags"] = string.split(/ *, */);
            }
            return mark;
        };

        var importBookmarks = function(){
            var button = sandbox.find("#m-i-import")[0];
            button.classList.add("disabled");
            button.textContent = "Importing...";
            var bookmarksFile = sandbox.find("#m-i-bookmarks-file-input")[0].files[0];
            var reader = new FileReader();
            reader.onload = function(event){
                alert("bookmark import temporarily disabled");
                // var contents = event.target.result;
                // var bookmarkRegex = /<[Aa][\W|\w]+?[Aa]>/gi;
                // var matches = contents.match(bookmarkRegex);
                // var bookmarks = [];
                // for (var each in matches){
                //     var dom = HTMLtoDOM(matches[each]);
                //     var element = $(dom).find("a")[0];
                //     var bookmark = netscapeElementToMark(element);
                //     if (bookmark){
                //         bookmarks.push(bookmark);
                //     }
                // }
                // sandbox.publish("new-marks", bookmarks);
                button.textContent = "Imported!";
            };
            reader.readAsText(bookmarksFile, "UTF-8");
            return false;
        };

        var insertJavasciptLink = function(){
            var insert = function(status, content){
                var bookmarkletAnchor = sandbox.find("#bookmarklet-a")[0];
                var url = "javascript:" + content.replace(
                    "WWW_BASE_URL", recall_config["www-base-url"]);
                bookmarkletAnchor.href = url;
            };

            var trampolineURL = recall_config["www-base-url"] + "/bookmarklet-trampoline";
            
            sandbox.asynchronous(
                insert,
                "get",
                trampolineURL
            );
        };

        return function (sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("show-getting-started", show);
            sandbox.subscribe("hide-all", hide);
            insertJavasciptLink();
            sandbox.bind("#m-i-import", "click", importBookmarks);
        };
    }());

core.add(
    "navigation",
    function(){
        var sandbox;

        var moveTo = function(show){
            sandbox.publish("hide-all");
            sandbox.publish("show-" + show, window.location.pathname);
            if (typeof history !== "undefined"){
                history.pushState({}, "Recall", "/" + show + "/");
            }
        };

        var vistorModeDisplay = {
            showing: ["#show-login", "#show-about"],
            hiding: ["#show-getting-started", "#logout"]
        };

        var userModeDisplay = {
            showing: vistorModeDisplay.hiding,
            hiding: vistorModeDisplay.showing
        };

        var flip = function(display){
            display.hiding.map(function(id){
                sandbox.find(id)[0].style.display = "none";
            });
            display.showing.map(function(id){
                sandbox.find(id)[0].style.display = "";
            });
        };

        var vistorMode = function(){
            flip(vistorModeDisplay);
        };

        var userMode = function(){
            flip(userModeDisplay);
        };

        return function(sandbox_){
            sandbox = sandbox_;
            if (window.location.pathname !== "/"){
                moveTo(window.location.pathname.split("/")[1]);
            } else {
                moveTo("about");
            }

            sandbox.bind(".recall-show", "click", function(event){
                moveTo(event.currentTarget.id.slice(5));
            });
            
            sandbox.bind("#logout", "click", function(){
                vistorMode();
                sandbox.publish("logout");
            });
            
            sandbox.subscribe("logged-in", userMode);
            

            sandbox.subscribe("show-post-login", function(){
                moveTo("marks");
            });
            
            sandbox.publish("logged-in?", {
                "success": userMode,
                "failure": vistorMode
            });
        };
    }());