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

makeSandbox = function(core, moduleName) {
    var interface_ = {};

    // DOM
    interface_.find = function (selector){
        return core.dom.queryWithin(moduleName, selector);
    };
    interface_.bind = function (element, event, handler){
        core.dom.bind(moduleName, element, event, handler);
    };
    interface_.create = function(tagName){
	return core.dom.create(tagName);
    };
    interface_.append = function(selector, element){
        core.dom.append(moduleName, selector, element);
    };
    interface_.deleteContentsOf = function(selector){
	core.dom.deleteContentsOf(moduleName, selector);
    };
    interface_.hiddenWrapHack = function(selector){
	core.dom.hiddenWrapHack(moduleName, selector);
    };
    interface_.unHiddenWrapHack = function(selector){
	core.dom.unHiddenWrapHack(moduleName, selector);
    };

    // Off-DOM
    interface_.offdom = {
        find: function(element, selector){
            return core.offdom.find(element, selector);
        },
	append: function(element, newChild){
	    return core.offdom.append(element, newChild);
	}
    };

    // Events
    interface_.publish = function (messageType, messageData){
        core.publish(messageType, messageData);
    };
    interface_.subscribe = function (messageType, handler){
        core.subscribe(moduleName, messageType, handler);
    };

    // XHR
    interface_.asynchronous = function(handler, verb, url, data, mime,
                                       headers){
        core.asynchronous(handler, verb, url, data, mime, headers);
    };

    // Module Storage
    interface_.get = function(key){
        return localStorage.getItem(moduleName + "$" + key);
    };
    interface_.set = function(key, value){
        return localStorage.setItem(moduleName + "$" + key, value);
    };
    interface_.has = function(key){
	return localStorage.getItem(moduleName + "$" + key) !== null;
    };
    interface_.drop = function(key){
	return localStorage.removeItem(moduleName + "$" + key);
    };

    return interface_;
};