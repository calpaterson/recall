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

var SANDBOX_FACTORY = {
    make: function(core, moduleName) {	
	var interface_ = {};
	interface_.find = function (selector){
	    // Return a dom element
	    return core.dom.queryWithin(moduleName, selector);
	};
	interface_.bind = function (element, event, handler){
	    // Call handler when event happens to element
	    core.dom.bind(element, event, handler);
	};
	interface_.publish = function (messageType, messageData){
	    // Publish a message
	    core.publish(messageType, messageData);
	};
	interface_.subscribe = function (messageType, handler){
	    // Subscribe to a type of message
	    core.subscribe(moduleName, messageType, handler);
	};
	interface_.asynchronous = function(handler, verb, url, data, mime,
					   headers){
	    // Make an XHR
	    core.asynchronous(handler, verb, url, data, mime, headers);
	};
	interface_.get = function(key){
	    return localStorage.getItem(moduleName + "$" + key);
	};
	interface_.set = function(key, value){
	    return localStorage.setItem(moduleName + "$" + key, value);
	};
	interface_.has = function(key){
	    return localStorage.hasOwnProperty(moduleName + "$" + key);
	};
	return interface_;
    }
};