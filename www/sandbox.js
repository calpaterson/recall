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
    make: function(core, elementID) {	
	var interface_ = {};
	interface_.find = function (selector){
	    // Return a dom element
	    return core.dom.queryWithin(elementID, selector);
	};
	interface_.bind = function (element, event, handler){
	    // Call handler when event happens to element
	    core.dom.bind(element, event, handler);
	};
	interface_.free = function (element, event){
	    // No longer call any function when event happens to element
	};
	interface_.publish = function (message){
	    // Publish a message
	};
	interface_.subscribe = function (messageType){
	    // Subscribe to a type of message
	    core.subscribe(elementID, messageType);
	};
	interface_.unsubscribe = function (messageType){
	    // Unsubscripe to a type of message
	};
	interface_.make = function (element){
	    // Make and append an element to the sandbox
	};
	interface_.asynchronous = function(handler, verb, url, data, mime,
					   header){
	    // Make an XHR
	    core.asynchronous(handler, verb, url, data, mime, header);
	};
	return interface_;
    }
};