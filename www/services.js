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
        
        var isLoggedIn = function(){
            if (sandbox.has("email") && sandbox.has("password")){
                var email = sandbox.get("email");
                var password = sandbox.get("password");
                sandbox.asynchronous(
                    function(status, content){
                        var user = JSON.parse(content);
                        if (status === 200 && user.hasOwnProperty("self")){
                            sandbox.publish("logged-in",
                                            {email: email,
                                             password: password});
                        } else {
                            sandbox.publish("logged-in", false);
                            sandbox.drop("email");
                            sandbox.drop("password");
                        }
                    },
                    "get",
                    recall_config["api-base-url"] + "/user/" + email,
                    {},
                    "application/json",
                    {"X-Email": email,
                     "X-Password": password});
            } else {
                sandbox.publish("logged-in", false);
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
        
        var login = function(data){
            sandbox.set("email", data.email);
            sandbox.set("password", data.password);
            isLoggedIn();
        };
        
        return function(sandbox_){
            sandbox = sandbox_;
            sandbox.subscribe("logged-in?", isLoggedIn);
            sandbox.subscribe("login", login);
            sandbox.subscribe("verify-email", verifyEmail);
        };
    }());



core.add(
    "markService",
    function(){
        var sandbox;
        
        var email, password;

        var send = function(mark){
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
        
        var storeEmailAndPassword = function(data){
            email = data.email;
            password = data.password;
        };

        var marks = function(){
            sandbox.asynchronous(
                function(status, content){
                    var marks = JSON.parse(content);
                    sandbox.publish("display", marks);
                },
                "get",
                recall_config["api-base-url"] + "/mark",
                {"maximum": 50}, // FIXME
                "application/json",
                {"X-Email": email,
                 "X-Password": password});
        };

        var whenLoggedIn = function(data){
            storeEmailAndPassword(data);
            loadRecentMarks();
        };
        
        return function(sandbox_){
            sandbox = sandbox_;
	    marks();
            sandbox.subscribe("new-mark", send);
            sandbox.subscribe("new-marks", send);
            sandbox.subscribe("logged-in", whenLoggedIn);
        };
    }());