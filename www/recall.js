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
            $('#about-carousel').carousel({interval: 5000});
            sandbox.subscribe("show-about", show);
            sandbox.subscribe("hide-all", hide);
        };
    }());

core.add(
    "verify-email-form",
    function(){
        var sandbox;

        var email_key;

        var button;

        var verify = function(){
            // This is slightly different because we need to call .button
            // directly on the resultset of $("foo") in order to get it to
            // work
            button = sandbox.find("#v-e-submit");
            button.button("loading");
            sandbox.publish(
            "verify-email", {
                "email_key": email_key[0].slice(10),
                "email": sandbox.find("#v-e-email")[0].value,
                "password": sandbox.find("#v-e-password")[0].value
            });
            return false;
        };

        var toggle = function(){
            sandbox.find()[0].hidden = !(sandbox.find()[0].hidden);
            return false;
        };

        var failed = function(){
            button.button("reset");
        };

        return function(sandbox_){
            sandbox = sandbox_;
            email_key = document.documentURI.match(/email_key=[0-9\-a-f]{36}/);
            if (email_key){
                toggle();
            }
            sandbox.bind("#v-e-submit", "click", verify);
            sandbox.subscribe("email-verified", toggle);
            sandbox.subscribe("email-not-verified", failed);
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
            button.innerText = "Sending...";

            var data = {
                "email": sandbox.find("#r-i-email")[0].value
            };
            var typeSelect = sandbox.find("#r-i-type")[0];
            if (typeSelect.selectedIndex === 0){
                data.firstName = sandbox.find("#r-i-first-name")[0].value;
                data.surname = sandbox.find("#r-i-surname")[0].value;
            } else if (typeSelect.selectedIndex === 1){
                data.pseudonym = sandbox.find("#r-i-pseudonym")[0].value;
            }

            // FIXME: This is a breach of the division
            $.ajax(recall_config["api-base-url"] + "/user",
                {
                    success: function(){
                        button.innerText = "Sent!";
                    },
                    type: "post",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json"
                }
            );
            return false;
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
    "view",
    function()
    {
        var sandbox;

        var contents;

        var hadAuthLastTime = false;

        var display = function(marks){
            sandbox.deleteContentsOf("#list-of-marks");
            for (var i = 0; i < marks.length; i++){
                sandbox.append("#list-of-marks", markToElement(marks[i]));
            }
        };

        var humanTime = function(unixtime){
            var then = new Date(unixtime * 1000);
            return $.timeago(then); // FIXME
        };

        var markToElement = function(mark){
            if (mark.hasOwnProperty("hyperlink")){
                var template = sandbox.find("#hyperlink-template")[0];
                var hyperlink = template.cloneNode(true);
                hyperlink.id = "mark-" + mark["@"] + "-" + mark["~"];
                sandbox.offdom.find(hyperlink, ".who")[0].innerText = mark["@"];
                sandbox.offdom.find(hyperlink, ".hyperlink-url")[0].href = mark.hyperlink;
                sandbox.offdom.find(hyperlink, ".hyperlink-title")[0].innerText = mark.title;
                sandbox.offdom.find(hyperlink, ".when")[0].innerText = humanTime(mark["~"]);
                return hyperlink;
            } else {
                var comment = sandbox.find("#comment-template")[0].cloneNode(true);
                comment.id = "mark-" + mark["@"] + "-" + mark["~"];
                sandbox.offdom.find(comment, ".who")[0].innerText = mark["@"];
                sandbox.offdom.find(comment, ".what")[0].innerText = mark["#"];
                sandbox.offdom.find(comment, ".when")[0].innerText = humanTime(mark["~"]);
                return comment;
            }
        };

        var show = function(){
            if (!hadAuthLastTime){
                sandbox.publish("get-marks?", {"display": display});
            }
            sandbox.find()[0].hidden = false;
            return false;
        };

        var hide = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("show-view", show);
            sandbox.subscribe("hide-all", hide);
        };
    }());

core.add(
    "mark-importer",
    function(){
        var sandbox;

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
            return mark;
        };

        var importBookmarks = function(){
            var bookmarksFile = $("#m-i-bookmarks-file-input")[0].files[0];
            var reader = new FileReader();
            reader.onload = function(event){
                var contents = event.target.result;
                var bookmarkRegex = /<[Aa][\W|\w]+?[Aa]>/gi;
                var matches = contents.match(bookmarkRegex);
                var bookmarks = [];
                for (var each in matches){
                    var dom = HTMLtoDOM(matches[each]);
                    var element = $(dom).find("a")[0];
                    var bookmark = netscapeElementToMark(element);
                    if (bookmark){
                        bookmarks.push(bookmark);
                    }
                }
                sandbox.publish("new-marks", bookmarks);
                sandbox.find()[0].hidden = true;
            };
            reader.readAsText(bookmarksFile, "UTF-8");
            return false;
        };

        var nevermind = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };

        var show = function(success){
            if (success){
                sandbox.find()[0].hidden = false;
            }
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.bind("#m-i-import", "click", importBookmarks);
            sandbox.bind("#m-i-nevermind", "click", nevermind);
        };
    }());

core.add(
    "problem-box",
    function(){
        var sandbox;

        var info = function(message){
            var infobox = sandbox.find("#info-template")[0].cloneNode(true);
            infobox.id = undefined;
            infobox.hidden = false;
            infobox.classList.add("alert-success");
            sandbox.offdom.find(infobox, ".info-contents")[0].innerText = message;
            sandbox.append(infobox);
        };

        var error = function(message){
            var infobox = sandbox.find("#info-template")[0].cloneNode(true);
            infobox.id = undefined;
            infobox.hidden = false;
            infobox.classList.add("alert-error");
            sandbox.offdom.find(infobox, ".info-contents")[0].innerText = message;
            sandbox.append(infobox);
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("info", info);
            sandbox.subscribe("error", error);
        };
    }());

core.add(
    "navbar",
    function(){
        var sandbox;

        var showing;

        var previousMode;

        var display = function(event){
            if (event !== undefined){
                showing = "#" + event.currentTarget.id;
            }
            sandbox.publish("hide-all");
            sandbox.publish(showing.slice(1));
            var showElements = sandbox.find(".show");
            for (var i = 0; i<showElements.length; i++){
                showElements[i].classList.remove("active");
            }
            sandbox.find(showing)[0].classList.add("active");
            sandbox.set("showing", showing);
        };

        var navbarMode = function(mode){
            if (mode === "visitor"){
                if(previousMode){
                    sandbox.hiddenWrapHack(".navbar-" + previousMode);
                }
                sandbox.unHiddenWrapHack(".navbar-visitor");
            } else if (mode === "user"){
                if(previousMode){
                    sandbox.hiddenWrapHack(".navbar-" + previousMode);
                }
                sandbox.unHiddenWrapHack(".navbar-user");
            }
            previousMode = mode;
        };

        var setVersion = function(){
            var version;
            if (recall_config.version == "development"){
                version = "Development version";
            } else if (typeof recall_config.version === "number"){
                version = "Version " + recall_config.version;
            } else {
                version = "Unknown version";
            }

            sandbox.find("#recall-version")[0].innerText = version;
        };

        var logout = function(){
            sandbox.publish("logout");
            showing = "#show-about";
            display();
            navbarMode("visitor");
            localStorage.clear();
        };

        return function(sandbox_){
            sandbox = sandbox_;
            showing = sandbox.get("showing");
            if(showing === null){
                showing = "#show-about";
            }
            setVersion();
            display();
            sandbox.bind(".show", "click", display);
            sandbox.publish("logged-in?",
                            {"success": function(){ navbarMode("user");},
                             "failure": function(){ navbarMode("visitor");}
                             });
            sandbox.bind("#logout", "click", logout);
            sandbox.subscribe("login", function(){ navbarMode("user");});
            sandbox.subscribe("show-post-login", function(){
                                  showing = "#show-view";
                                  display();
                              });
        };
    }());