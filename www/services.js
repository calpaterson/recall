core.add(
    "authorisationService",
    function(){
	var sandbox;
	
	var isLoggedIn = function(){
	    if (sandbox.has("email") && sandbox.has("password")){
		sandbox.publish("logged-in",
				{email: sandbox.get("email"),
				 password: sandbox.get("password")});
	    } else {
		sandbox.publish("logged-in", false);
	    }
	};
	
	var login = function(data){
	    sandbox.set("email", data.email);
	    sandbox.set("password", data.password);
	    sandbox.publish("logged-in", {email: data.email,
					  password: data.password});
	};
	
	return function(sandbox_){
	    sandbox = sandbox_;
	    sandbox.subscribe("logged-in?", isLoggedIn);
	    sandbox.subscribe("login", login);
	};
    }());



core.add(
    "markService",
    function(){
	var sandbox;
	
	var email, password;
	
	var sendMark = function(mark){
	    var serialisedMark = JSON.stringify(mark);
	    sandbox.asynchronous(
		function(status, content){
		    if (status !== 201){
			sandbox.publish("error", "Problem while sending mark");
			alert(content);
		    } else {
			sandbox.publish("mark-sent");   
		    }
		},
		"post",
		recall_config["api-base-url"] + "/mark",
		serialisedMark,
		"application/json",
		{"X-Email": email,
		 "X-Password": password}
	    );
	};
	
	var storeEmailAndPassword = function(data){
	    email = data.email;
	    password = data.password;
	};
	
	return function(sandbox_){
	    sandbox = sandbox_;
	    sandbox.subscribe("new-mark", sendMark);
	    sandbox.subscribe("logged-in", storeEmailAndPassword);
	};
    }());