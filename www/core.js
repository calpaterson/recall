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
                if (selector !== undefined){
                    return document.querySelectorAll("#" + moduleName + " " + selector);
                } else {
                    return document.querySelectorAll("#" + moduleName);
                }
            },
            bind: function(moduleName, selector, eventName, handler){
                // FIXME Should take moduleName
                var elements = this.queryWithin(moduleName, selector);
                for (var index = 0; index < elements.length; index++){
                    elements[index]["on" + eventName] = handler;
                }
            },
            append: function(moduleName, selector, element){
                core.dom.queryWithin(moduleName, selector)[0].appendChild(element);
            },
            deleteContentsOf: function(moduleName, selector){
		var parent = this.queryWithin(moduleName, selector)[0];
		while(parent.hasChildNodes()){
		    parent.removeChild(parent.lastChild);
		}
            },
            hiddenWrapHack : function(moduleName, selector){
                var elements = this.queryWithin(moduleName, selector);
                for(var index = 0; index < elements.length; index++){
                    elements[index].style.display = "none";
                }
            },
            unHiddenWrapHack : function(moduleName, selector){
                var elements = this.queryWithin(moduleName, selector);
                for(var index = 0; index < elements.length; index++){
                    elements[index].style.display = "block";
                }
            }
        };
        core.offdom = {
            find: function(element, selector){
                return element.querySelectorAll(selector);
            }
        };
        core.asynchronous = function(handler, verb, url, data, mime, headers){
            var request = new XMLHttpRequest();
            request.onload = function(xhrProgressEvent){
                handler(
                    xhrProgressEvent.currentTarget.status,
                    xhrProgressEvent.currentTarget.responseText);
            };
            request.open(verb, url);
            for (var key in headers){
                if (headers.hasOwnProperty(key)){
                    request.setRequestHeader(key, headers[key]);
                }
            }
            request.send(data);
        };
        return core;
    }()
);

document.addEventListener("DOMContentLoaded", function(){
    core.startAll();
});