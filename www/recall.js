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
    "navbar",
    function(){
        var sandbox;

        var displayUserNavbar = function(){
            
        };

        var displayVisitorNavbar = function(){
            var vistorNavEs = sandbox.find("#visitor-nav-stager").children();
            var navbarList = sandbox.find("#navbar-list")[0];
            for(var i = 0; i < vistorNavEs.length; i++){
                var original = vistorNavEs[i];
                var copy = original.cloneNode(true);
                copy.children[0].id = original.children[0].id.slice(0, -10);
                navbarList.appendChild(copy);
            }
            sandbox.bind("#navbar-log-in", "click", function(message){
                             sandbox.publish("show-login-form");
                         });
            sandbox.bind("#navbar-request-invite", "click", function(message){
                             sandbox.publish("show-request-invite-form");
                         });
        };

        var displayNavbar = function(message){
            if (message){
                displayUserNavbar();
            } else {
                displayVisitorNavbar();
            }
        };
        
        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("logged-in", displayNavbar);
            sandbox.publish("logged-in?");
        };
    }());

core.add(
    "login-form",
    function(){
        var sandbox;

        var send = function(){
            sandbox.publish(
            "login", {
                "email": sandbox.find("#login-form-email")[0].value,
                "password": sandbox.find("#login-form-password")[0].value
            });
            return false;
        };

        var nevermind = function(message){
            hide();
            return false;
        };

        var hide = function(){
            sandbox.find()[0].hidden = true;
        };

        var show = function(){
            sandbox.find()[0].hidden = false;
        };

        var complete = function(message){
            hide();
        };
        
        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.bind("#login-form-submit", "click", send);
            sandbox.bind("#login-form-nevermind", "click", nevermind);
            sandbox.subscribe("logged-in", complete);
            sandbox.subscribe("show-login-form", show);
        };
    }());

core.add(
    "request-invite-form",
    function(){
        var sandbox;

        var typeShowing = "#r-i-real-name";

        var send = function(){
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

        var nevermind = function(message){
            sandbox.find()[0].hidden = true;
            return false;
        };

        var show = function(){
            sandbox.find()[0].hidden = false;
        };
        
        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.bind("#r-i-submit", "click", send);
            sandbox.bind("#r-i-nevermind", "click", nevermind);
            sandbox.bind("#r-i-type", "change", changeType);
            sandbox.subscribe("show-request-invite-form", show);
        };
    }());

core.add(
    "view-of-marks",
    function()
    {
        var sandbox;

        var contents;

        var showMark = function(mark){
            sandbox.append(markToElement(mark));
        };

        var humanTime = function(unixtime){
            var then = new Date(unixtime * 1000);
            return $.timeago(then); // FIXME
        };

        var markToElement = function(mark){
            if (mark.hasOwnProperty("hyperlink")){
                var hyperlink = sandbox.find("#hyperlink-template")[0].cloneNode(true);
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

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("mark", showMark);
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
            sandbox.subscribe("logged-in", show);
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
            sandbox.offdom.find(infobox, ".info-contents")[0].innerText = message;
            sandbox.append(infobox);
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("info", info);
        };
    }());

// Temporary code stolen from http://stackoverflow.com/a/2880929
var urlParams = {};
(function () {
    var e,
        a = /\+/g,  // Regex for replacing addition symbol with a space
        r = /([^&=]+)=?([^&]*)/g,
        d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
        q = window.location.search.substring(1);

    while ((e = r.exec(q)))
       urlParams[d(e[1])] = d(e[2]);
})();


// $(document).ready(
//     function() {
//         // Email Address Verification Modal
//         // --------------------------------
//         var url_args = document.location.href.split("?")[1];
//         if (urlParams.hasOwnProperty("email_key")){
//             var email_key = urlParams.email_key;
//             $("#verify-email-modal").modal("show");
//             var password = "password";
//             $("#send-password").click(
//                 function(){
//                     $.ajax(
//                         recall_config["api-base-url"] + "/user/" + email_key,
//                         {
//                             "type": "post",
//                             "data": JSON.stringify(
//                                 {"%password": password}),
//                             "contentType": "application/json",
//                             "dataType": "json",
//                             complete : function(jqXHR, textStatus){
//                                 if (textStatus == "success"){
//                                     var email = JSON.parse(jqXHR.responseText).email;
//                                     localStorage.setItem("email", email);
//                                     localStorage.setItem("password", password);
//                                     $("#auth-status").text(
//                                         localStorage.getItem("email"));
//                                     $("#verify-email-modal").modal("hide");
//                                 } else {
//                                     alert("failure to verify email address");
//                                 }
//                             }
//                         });
//                 }
//             );
//         }
        // Import Bookmarks Modal
        // ----------------------
        $("#show-import-bookmarks-modal").click(
            function(){
                $("#import-bookmarks-modal").modal();
            }
        );



        $("#import-bookmarks").click(

        );