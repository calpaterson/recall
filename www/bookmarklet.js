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

var sendMark = function(mark) {
    $.ajax(
	recall_config["api-base-url"] + "/mark",
	{
	    type: 'post',
	    data: JSON.stringify(mark),
	    contentType: 'application/json',
	    dataType: 'json',
	    complete: function(jqXHR, textStatus){
		if (textStatus === "success"){
		    window.close();
		} else {
		    $("#mark-alert-failure").fadeIn();
		}
	    }
	}
    );
};

var unixtime_now = function() {
    return Math.floor(new Date().getTime() / 1000);
};

$(document).ready(
    function(){
	// Remembering tab position
	// ------------------------
	var bookmarkletTabSelection = localStorage.getItem(
	    "bookmarklet-tab-selection");
	if (bookmarkletTabSelection){
	    $(".active").removeClass("active");
	    $(bookmarkletTabSelection).addClass("active");
	    $(bookmarkletTabSelection + "-tab").addClass("active");
	};

	$(".tab").click(
	    function(event){
		localStorage.setItem("bookmarklet-tab-selection",
				     $(event.target).attr("href"));
 	    });

	// Preloading hyperlink fields if possible
	// ---------------------------------------
	var url = location.href;
	var banana_split = url.split("&");
	for (var i = 1; i < banana_split.length; i++){
	    var sub_split = banana_split[i].split("=");
	    if (sub_split[0] === "title"){
		$("#hyperlink-title").val(decodeURIComponent(sub_split[1]));
	    } else if (sub_split[0] === "url"){
		$("#hyperlink-url").val(decodeURIComponent(sub_split[1]));
	    }
	};

	// Sending the mark
	// ----------------
	$("button.send-mark").click(
	    function(event){
		var commentRegex = /comment/;
		var locationRegex = /location/;
		var hyperlinkRegex = /hyperlink/;
		
		var buttonClasses = $(event.target).attr("class");
		if (commentRegex.test(buttonClasses)){
		    var mark = {
			"#": $("#comment-body").val(),
			"~": unixtime_now(),
			"@": "cal@calpaterson.com",
			"%email": localStorage.getItem("email"),
			"%password": localStorage.getItem("password")
		    };
		    sendMark(mark);
		} else if (hyperlinkRegex.test(buttonClasses)){
                    sendMark({
                                "title": $("#hyperlink-title").val(),
                                "hyperlink": $("#hyperlink-url").val(),
                                 "~": unixtime_now(),
                                 "@": "cal@calpaterson.com",
                                 "%email": localStorage.getItem("email"),
				 "%password": localStorage.getItem("password")
                             });
                } else {
		    $("#mark-alert-failure").fadeIn();		
		}
	    });
    }
);