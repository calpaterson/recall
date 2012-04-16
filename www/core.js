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

core = (
    function () {
        var core = {};
        var modules = {};
        
        core.add = function (moduleName, controller){
            // Add a module
            modules[moduleName] = {
                controller: controller,
                instance: null};
        };
        core.start = function(moduleName){
            // Start a module
            var controller = modules[moduleName].controller;
            modules[moduleName].instance = controller(
                makeSandbox(this, moduleName));
        };
        core.startAll = function(){
            // Start all modules
            for (var moduleName in modules){
                core.start(moduleName);
            }
        };
        core.subscribe = function (moduleName, messageType, handler){
            // Subscribe a module to a message
            if(!modules[moduleName].hasOwnProperty("subscriptions")){
                modules[moduleName].subscriptions = {};
            }
            modules[moduleName].subscriptions[messageType] = handler;
            
        };
        core.publish = function (messageType, messageData){
            // Publish a message
            for (var moduleName in modules){
                var subscriptions = modules[moduleName].subscriptions;
                for (var subscription in subscriptions){
                    if(subscription === messageType){
                        subscriptions[subscription](messageData);
                    }
                }
            }
        };
        core.dom = {
            // Domain object model
            queryWithin: function(moduleName, selector){
                var module = $("#" + moduleName);
                if (module.length > 1){
                    throw "#" + moduleName + " is used more than once";
                }
                if (selector !== undefined){
                    return $(module).find(selector);   
                } else {
                    return $(module);
                }
            },
            bind: function(element, event, handler){
                $(element).bind(event, handler);
            }
        };
        core.asynchronous = function(handler, verb, url, data, mime, headers){
            $.ajax(url,
                  {
                      type: verb,
                      data: data,
                      contentType: mime,
                      headers: headers,
                      complete: function(jqXHR, textStatus){
                          handler(jqXHR.status, jqXHR.responseText);
                      }
                  }
                  );
        };
        return core;
    }()
);

$(document).ready(
    function(){
        core.startAll();
    }
);