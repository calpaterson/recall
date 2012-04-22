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
                        if (user.hasOwnProperty("self")){
                            sandbox.publish("logged-in",
                                            {email: email,
                                             password: password});
                        } else {
                            sandbox.publish("logged-in", false);
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
        
        var login = function(data){
            sandbox.set("email", data.email);
            sandbox.set("password", data.password);
            isLoggedIn();
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

        var loadRecentMarks = function(){
            sandbox.asynchronous(
                function(status, content){
                    var marks = JSON.parse(content);
                    for (var index in marks){
                        sandbox.publish("mark", marks[index]);
                    }
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
            sandbox.subscribe("new-mark", sendMark);
            sandbox.subscribe("logged-in", whenLoggedIn);
        };
    }());