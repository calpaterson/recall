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
    function() {
	// Brand
	// -----
	$('#brand').click(
	    function(){
		document.reload();
	    }
	);
	
	// Hero Unit
        // ---------
	if (localStorage.getItem("show-hero-unit") === null){
	    $("#hero-unit").hide();
	}
	$('#toggle-hero-unit').click(
	    function(){
		var show = localStorage.getItem("show-hero-unit");
		if (show === "true"){
		    $("#hero-unit").fadeOut();
		    localStorage.removeItem("show-hero-unit");
		} else if (show === null){
		    $("#hero-unit").fadeIn();
		    localStorage.setItem("show-hero-unit", "true");
		}
	    }
	);
	$('#hide-hero-unit-btn').click(
	    function(){
		localStorage.removeItem("show-hero-unit");
		$('#hero-unit').fadeOut();	    
	    });
	$('#learn-more-btn').click(
	    function (){
		$("#learn-more-btn").fadeOut();
		$('#hero-initial').fadeOut(
		    "slow",
		    function (){
			$('#learn-more').fadeIn();
		    });
	    }
	);

	// List of posts
	// -------------
	$.getJSON(recall_config["api-base-url"] + "/mark/cal@calpaterson.com",
		 function (data){
		     var convertUnixtimeToDate = function(unixtime){
			 var now = new Date();
			 var then = new Date(unixtime * 1000);
			 return (((now - then) / 1000) / 60) + "minutes ago";
		     };
		     $.each(data,
			    function(_, elem){
				$("#marks").append(
				    "<li><strong>" + elem["@"] + "</strong> at " + convertUnixtimeToDate(elem["~"]) + ":",
				    "<em>" + elem["#"] + "</em></li>");
			    });
		 });
    }
);