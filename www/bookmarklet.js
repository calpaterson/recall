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

$(document).ready(
    function(){
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
	
	$("button.send-mark").click(
	    function(event){
		var commentRegex = /comment/;
		var locationRegex = /location/;
		
		var buttonClasses = $(event.target).attr("class");
		if (commentRegex.test(buttonClasses)){
		    var mark = {
			"#": $("#comment-body").val(),
			"~": Math.floor(new Date().getTime() / 1000),
			"@": "cal@calpaterson.com"
		    };
		    $.ajax(
			recall_config["api-base-url"] + "/mark",
			{
			    type: 'post',
			    data: JSON.stringify(mark),
			    contentType: 'application/json',
			    dataType: 'json',
			    success: function(data, textStatus, jqXHR){
				if (textStatus === "success"){
				    $("#mark-alert-success").fadeIn();
				} else {
				    $("#mark-alert-failure").fadeIn();
				}
			    }
			}
		    );
		} else if (locationRegex.test(buttonClasses)) {
		    $("#mark-alert-failure").fadeIn();		
		}
	    });
    }
);