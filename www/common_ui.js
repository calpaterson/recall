core.add(
    "login-form",
    function(){
        var sandbox;
        var button;

        var login = function(){
            button.classList.add("disabled");
            button.innerText = "Logging in...";
            sandbox.publish(
            "login", {
                "email": sandbox.find("#login-form-email")[0].value,
                "password": sandbox.find("#login-form-password")[0].value,
                "success": loginSuccess,
                "offline": offline,
                "failure": loginError
            });
            return false;
        };

        var loginSuccess = function(user){
            hide();
            button.innerText = "Login Again";
            button.classList.remove("disabled");
            sandbox.publish("show-post-login");
        };

        var offline = function(user){
            button.innerText = "You are offline";
        };

        var loginError = function(user){
            button.innerText = "Try Again";
            button.classList.remove("disabled");
        };

        var show = function(){
            sandbox.find()[0].hidden = false;
            return false;
        };

        var hide = function(){
            sandbox.find()[0].hidden = true;
            return false;
        };

        var complete = function(message){
            if(message){
                sandbox.publish("info", "Logged in");
            } else {
                sandbox.publish("error", "Wrong password");
            }
        };

        return function(sandbox_){
            sandbox = sandbox_;
            button = sandbox.find("#login-form-submit")[0];
            sandbox.bind("#login-form-submit", "click", login);
            sandbox.subscribe("logged-in", complete);
            sandbox.subscribe("show-login", show);
            sandbox.subscribe("hide-all", hide);
        };
    }());