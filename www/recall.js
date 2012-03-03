var BASE_URL = "localhost";

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
	$.getJSON("http://" + BASE_URL + "/mark/cal@calpaterson.com",
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