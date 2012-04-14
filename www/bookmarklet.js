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


bookmarklet = function(){
    var sandbox;

    var restoreTabSelection = function(){
	var bookmarkletTabSelection = localStorage.getItem(
	    "bookmarklet-tab-selection");
	if (bookmarkletTabSelection){
            sandbox.find(".active").removeClass("active");
            sandbox.find(bookmarkletTabSelection).addClass("active");
            sandbox.find(bookmarkletTabSelection + "-tab").addClass("active");
        } else {
	    sandbox.find("#hyperlink-tab").addClass("active");
	    sandbox.find("#hyperlink-tab-tab").addClass("active");
	}
    };

    var saveTabSelection = function(event){
        localStorage.setItem("bookmarklet-tab-selection",
			     $(event.target).attr("href"));
    };

    var preloadHyperlinkTabFields = function(){
        var url = location.href;
        var banana_split = url.split("&");
        for (var i = 1; i < banana_split.length; i++){
            var sub_split = banana_split[i].split("=");
            if (sub_split[0] === "title"){
                sandbox.find("#hyperlink-title").val(
		    decodeURIComponent(sub_split[1]));
            } else if (sub_split[0] === "url"){
                sandbox.find("#hyperlink-url").val(
		    decodeURIComponent(sub_split[1]));
            }
        }
    };

    var makeMark = function(event){
	var unixtimeNow = function() {
	    return Math.floor(new Date().getTime() / 1000);
	};
	var mark = { "~": unixtimeNow() };
	if (sandbox.find("#private")[0].checked){
	    mark["%private"] = true;
	}
	mark["@"] = localStorage.getItem("email");
	if (sandbox.find("#comment-tab-tab").hasClass("active")){
	    mark["#"] = sandbox.find("#comment-body").val();
	} else if (sandbox.find("#hyperlink-tab-tab").hasClass("active")){
	    mark.title = sandbox.find("#hyperlink-title").val();
	    mark.hyperlink = sandbox.find("#hyperlink-url").val();
	}
	
	var serialisedMark = JSON.stringify(mark);
	sandbox.asynchronous(
	    function(status, content){
		if (status !== 201){
		    alert(content);
		}
	    },
	    "post",
	    recall_config["api-base-url"] + "/mark",
	    serialisedMark,
	    "application/json",
	    {"X-Email": localStorage.getItem("email"),
	     "X-Password": localStorage.getItem("password")}
	    );
    };

    return function (sandbox_) {
	sandbox = sandbox_;
	restoreTabSelection();
	preloadHyperlinkTabFields();
	sandbox.bind(".tab", "click", saveTabSelection);
	sandbox.bind("#mark-button", "click", makeMark);
    };
}();

core.add("bookmarklet", bookmarklet);