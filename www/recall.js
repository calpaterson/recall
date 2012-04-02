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

var loggedIn = function (){
    return localStorage.getItem("email") !== null;
};

// List of posts
// -------------
var getTime = function(elem){
    var then = new Date(elem['~'] * 1000);
    return $.timeago(then);
};

var renderComment = function(elem){
    var comment = $($("#comment-template")).clone();
    comment.removeAttr("id");
    comment.find(".who").text(elem["@"]);
    comment.find(".what").text(elem["#"]);
    comment.find(".when").text(getTime(elem));
    return comment;
};

var renderLocation = function(elem){
    var location = $($('#location-template').clone());
    location.removeAttr("id");
    location.find(".who").text(elem["@"]);
    location.find(".when").text(getTime(elem));
    location.find(".location-map")[0].src = 'https://maps.googleapis.com/maps/api/staticmap?center=' +
        elem.latitude + ',' + elem.longitude + '&sensor=false&size=400x400&' +
        'markers=color:red%7C' + elem.latitude + ',' + elem.longitude;
    return location;
};

var renderHyperlink = function(elem){
    var hyperlink = $($("#hyperlink-template")).clone();
    hyperlink.removeAttr("id");
    hyperlink.find(".who").text(elem["@"]);
    $(hyperlink.find(".hyperlink-url")[0]).attr("href", elem["hyperlink"]);
    hyperlink.find(".title").text(elem.title);
    hyperlink.find(".when").text(getTime(elem));
    return hyperlink;
};

oldestMark = null;

var renderMarks = function (data){
    $.each(
        data,
        function(_, elem){
	    oldestMark = elem["~"];
            if(elem.hasOwnProperty('latitude')){
                var loc = renderLocation(elem);
                $("#marks").append(loc);
	    } else if (elem.hasOwnProperty("hyperlink")){
		$("#marks").append(renderHyperlink(elem));
            } else {
                $("#marks").append(renderComment(elem));        
            }
        });
};

var addMarks = function (before){
    if (before == undefined){
	before = 0;	
    }
    $.ajax(recall_config["api-base-url"] + "/mark",
	   {
	       type: "get",
	       headers: {"X-Email": localStorage.getItem("email"),
			 "X-Password": localStorage.getItem("password")},
	       contentType: "application/json",
	       dataType: "json",
	       data: {"maximum": 50, "before": before},
	       complete: function(jqXHR, textStatus) {
		   renderMarks(JSON.parse(jqXHR.responseText)); }
	   });
};

var updateNavbarUser = function(){
    // Auth Status ("Not Logged In"/"foo@example.com")
    if (loggedIn()){
	$("#auth-status").text(localStorage.getItem("email"));
	$("#login-toggle-dropdown").text("Logout");
    } else {
	$("#auth-status").text("Not Logged In");
	$("#login-toggle-dropdown").text("Login");
    }
}

$(document).ready(
    function() {
        // Brand
        // -----
        $('#brand').click(
            function(){
                $(document).reload();
            }
        );

	updateNavbarUser();


	// Login modal
	// -----------
	$("#send-login").click(
	    function(){
		localStorage.setItem(
		    "email", $("#login-email-input").val());
		localStorage.setItem(
		    "password", $("#login-password-input").val());
		updateNavbarUser();
		$("#login-modal").modal("hide");
	    }
	);

	// Login dropdown
	// --------------
	$("#login-toggle-dropdown").click(
	    function(event){
		if (loggedIn()){
		    localStorage.removeItem("email");
		    localStorage.removeItem("password");
		    $("#login-toggle-dropdown").text("Login");
		    updateNavbarUser();
		} else {
		    $("#login-modal").modal();
		    $("#login-toggle-dropdown").text("Logout");
		}
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
                    null,
                    function (){
                        $('#learn-more').fadeIn();
                    });
            }
        );

	// Request Invite Modal
	// --------------------
	$("#show-request-invite-modal").click(
	    function(){
		$("#request-invite-modal").modal();
	    });

	$("#name-type-select").change(
	    function(){
		var selection = $(this).children(":selected").html();
		if (selection === "Real Name"){
		    $("#pseudonym-div").hide();
		    $("#real-name-div").show();
		} else if (selection === "Pseudonym"){
		    $("#real-name-div").hide();
		    $("#pseudonym-div").show();
		}
	    }
	);

	$("#send-invite").click(
	    function(){
		var form = $("#request-invite-pseudo-form");
		var user = {"@": form.children("#email-input").val()};
		if (form.find("select").val() === "Real Name"){
		    user["firstName"] = form.find("#first-name-input").val();
		    user["surname"] = form.find("#surname-input").val();
		} else {
		    user["pseudonym"] = form.find("#pseudonym-input").val();
		}
		user["email"] = form.find("#email-input").val();
		$.ajax(
		    recall_config["api-base-url"] + "/user",
		{
		    type: "post",
		    data: JSON.stringify(user),
		    contentType: "application/json",
		    dataType: "json",
		    complete: function(jqXHR, textStatus){
			if (textStatus === "success"){
			    $("#invite-request-alert-success").fadeIn();
			} else {
			    $("#invite-request-alert-failure").fadeIn();
			}
		    }
		});
	    });

	// Email Address Verification Modal
	// --------------------------------
	var url_args = document.location.href.split("?")[1];
	if (urlParams.hasOwnProperty("email_key")){
	    var email_key = urlParams["email_key"];
	    $("#verify-email-modal").modal("show");
	    var password = "password";
	    $("#send-password").click(
	    	function(){
	    	    $.ajax(
	    		recall_config["api-base-url"] + "/user/" + email_key,
	    		{
	    		    "type": "post",
	    		    "data": JSON.stringify(
	    			{"%password": password}),
	    		    "contentType": "application/json",
	    		    "dataType": "json",
	    		    complete : function(jqXHR, textStatus){
	    			if (textStatus == "success"){
				    var email = JSON.parse(jqXHR.responseText)["email"];
	    			    localStorage.setItem("email", email);
	    			    localStorage.setItem("password", password);
	    			    $("#auth-status").text(
	    				localStorage.getItem("email"));
				    $("#verify-email-modal").modal("hide");
	    			} else {
	    			    alert("failure to verify email address");
	    			}
	    		    }
	    		});
	    	}
	    );
	}

	// Bookmarklet Modal
	// -----------------
	$('#show-bookmarklet-modal').click(
	    function(){
		$('#bookmarklet-modal').modal();
	    }
	);

	$.get("/bookmarklet-trampoline", function(data){
		  var bookmarklet = data.replace(
			  /BASE_API_URL/,
		      recall_config["api-base-url"]);
		  $("#bookmarklet").attr(
		      "href",
		      "javascript:" + bookmarklet);
	      }
	     );

	// Import Bookmarks Modal
	// ----------------------
	$("#show-import-bookmarks-modal").click(
	    function(){
		$("#import-bookmarks-modal").modal();
	    }
	);

	var netscapeElementToMark = function(element){
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
		"hyperlink": element.attributes["HREF"].nodeValue,
		"~": parseInt(element.attributes["ADD_DATE"].nodeValue, 10),
		"title": htmlDecode(element.textContent),
		"@": localStorage.getItem("email"),
		// "tags": element.attributes["TAGS"].nodeValue.split(/ |,/g)
	    };
	    if (element.attributes.hasOwnProperty("PRIVATE")){
		if (element.attributes["PRIVATE"].nodeValue === "1"){
		    mark["%private"] = true;
		}
	    }
	    if (element.attributes.hasOwnProperty("TOREAD")){
		if (element.attributes["TOREAD"].nodeValue === "1"){
		    mark["unread"] = true;
		}
	    }
	    return mark;
	};

	$("#import-bookmarks").click(
	    function(){
		var bookmarksFile = $("#bookmarks-file-input")[0].files[0];
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
		    $.ajax(
			recall_config["api-base-url"] + "/mark",
			{
			    type: 'post',
			    headers: {
				"X-Email": localStorage.getItem("email"),
				"X-Password": localStorage.getItem("password")},
			    data: JSON.stringify(bookmarks),
			    contentType: 'application/json',
			    dataType: 'json',
			    complete: function(jqXHR, textStatus){
				if (textStatus === "success"){
				    window.close();
				} else {
				    alert("Failed");
				}
			    }
			}
		    );
		};
		reader.readAsText(bookmarksFile, "UTF-8");
	    }
	);

	addMarks();

	// More marks button
	$("#more-btn").click(
	    function(){
		addMarks(oldestMark);
	});
    }
);
