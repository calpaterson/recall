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
    "authorisationService",
    function(){
        var sandbox;

        var login = function(message){
            var cb = function(status, content){
                var user = JSON.parse(content);
                if (status === 200 && user.hasOwnProperty("self")){
                    sandbox.set("email", message.email);
                    sandbox.set("password", message.password);
                    message.success(user);
                    sandbox.publish("logged-in");
                } else {
                    message.failure();
                }
            };
            sandbox.asynchronous(
                cb,
                "get",
                recall_config["api-base-url"] + "/v1/user/" + message.email,
                {},
                "application/json",
                {"X-Email": message.email,
                 "X-Password": message.password});
        };

        var logout = function(){
            sandbox.drop("email");
            sandbox.drop("password");
        };

        var loggedIn = function(message){
          if (sandbox.has("email")){
              message.success(sandbox.get("email"), sandbox.get("password"));
          } else {
              message.failure();
          }
        };

        var verifyEmail = function(message){
            sandbox.set("email", message.email);
            sandbox.set("password", message.password);
            sandbox.asynchronous(
                function(status, content){
                    if (status === 201){
                        sandbox.publish("logged-in", {email: message.email,
                                                      password: message.password});
                        message.success();
                    } else {
                        if (status === 404) {
                            sandbox.publish("error", "Wrong link or email address");
                        } else if (status === 403) {
                            sandbox.publish("error", "Account already verified");
                        }
                        message.failure();
                        sandbox.drop("email");
                        sandbox.drop("password");
                    }
                },
                "post",
                recall_config["api-base-url"] + "/v1/user/" + message.email_key,
                JSON.stringify({"email_key": message.email_key,
                                "email" : message.email,
                                "password": message.password}),
                 "application/json",
                {});
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("login", login);
            sandbox.subscribe("logout", logout);
            sandbox.subscribe("logged-in?", loggedIn);
            sandbox.subscribe("verify-email", verifyEmail);
        };
    }());



core.add(
    "markService",
    function(){
        var sandbox;

        var email, password;

        var send = function(message){
            authenticate();
            var serialisedMark = JSON.stringify(message.marks);
            sandbox.asynchronous(
                function(status, content){
                    if (status === 201){
                        message.success();
                    } else if (status === 202){
                        message.success();
                    } else{
                        message.failure();
                    }
                },
                "post",
                recall_config["api-base-url"] + "/v1/mark",
                serialisedMark,
                "application/json",
                {"X-Email": email,
                 "X-Password": password}
            );
        };

        var authenticate = function(){
            var authentication = function(email_, password_){
                email = email_;
                password = password_;
            };
            sandbox.publish("logged-in?", {"success": authentication,
                                           "failure": function(){}});
        };

        var marks = function(message){
            authenticate();
            var url = recall_config["api-base-url"] + "/v1/mark";
            if (message.hasOwnProperty("q")){
                url += "?q=";
                url += encodeURIComponent(message.q);
            }
            sandbox.asynchronous(
                function(status, content){
                    var marks = JSON.parse(content);
                    message.callback(marks);
                },
                "get",
                url,
                {"maximum": 50}, // FIXME
                "application/json",
                {"X-Email": email,
                 "X-Password": password});
        };

        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("get-marks?", marks);
            sandbox.subscribe("new-mark", send);
            sandbox.subscribe("new-marks", send);
        };
    }());