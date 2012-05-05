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
                } else {
                    message.failure();
                }
            };
            sandbox.asynchronous(
                cb,
                "get",
                recall_config["api-base-url"] + "/user/" + message.email,
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
              message.success(sandbox.get("email", sandbox.get("password")));
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
                        sandbox.publish("email-verified");
                        sandbox.publish("logged-in", {email: message.email,
                                                      password: message.password});
                    } else {
                        if (status === 404) {
                            sandbox.publish("error", "Wrong link or email address");
                        } else if (status === 403) {
                            sandbox.publish("error", "Account already verified");
                        }
                        sandbox.publish("email-not-verified");
                        sandbox.drop("email");
                        sandbox.drop("email");
                    }
                },
                "post",
                recall_config["api-base-url"] + "/user/" + message.email_key,
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

        var send = function(mark){
            authentication();
            var serialisedMark = JSON.stringify(mark);
            sandbox.asynchronous(
                function(status, content){
                    if (status === 201){
                        sandbox.publish("mark-sent");
                    } else if (status === 202){
                        var message = "Your bookmarks have been imported" +
                            " (reload the page to see them)";
                        sandbox.publish("info", message);
                    } else{
                        sandbox.publish("error", "Problem while sending mark");
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

        var authentication = function(email, password){
            this.email = email;
            this.password = password;
        };

        var marks = function(message){
            sandbox.publish("logged-in?", {"success": authentication,
                                           "failure": function(){}});
            sandbox.asynchronous(
                function(status, content){
                    var marks = JSON.parse(content);
                    message.display(marks);
                },
                "get",
                recall_config["api-base-url"] + "/mark",
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