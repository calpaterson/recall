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

$(document).ready(
    function() {
        // Brand
        // -----
        $('#brand').click(
            function(){
                $(document).reload();
            }
        );
        
        // Hero Unit
        // ---------
        if (localStorage.getItem("show-hero-unit") === null){
            $("#hero-unit").hide();
        }
        $('#toggle-hero-unit').click(
            function(){
                var show = localStorage.getItem("show-hero-unit");
                if (show === "true"){
                    $("#hero-unit").fadeOut();
                    localStorage.removeItem("show-hero-unit");
                } else if (show === null){
                    $("#hero-unit").fadeIn();
                    localStorage.setItem("show-hero-unit", "true");
                }
            }
        );
        $('#hide-hero-unit-btn').click(
            function(){
                localStorage.removeItem("show-hero-unit");
                $('#hero-unit').fadeOut();          
            });
        $('#learn-more-btn').click(
            function (){
                $("#learn-more-btn").fadeOut();
                $('#hero-initial').fadeOut(
                    null,
                    function (){
                        $('#learn-more').fadeIn();
                    });
            }
        );

        var getTime = function(elem){
            var then = new Date(elem['~'] * 1000);
            return $.timeago(then);
        };

        var renderComment = function(elem){
            var comment = $($("#comment-template")).clone();
            comment.find(".who")[0].innerText = elem["@"];
            comment.find(".what")[0].innerText = elem["#"];
            comment.find(".when")[0].innerText = getTime(elem);
            return comment;
        };

        var renderLocation = function(elem){
            var location = $($('#location-template').clone());
            location.find(".who")[0].innerText = elem["@"];
            location.find(".when")[0].innerText = getTime(elem);
            location.find(".location-map")[0].src = 'https://maps.googleapis.com/maps/api/staticmap?center=' +
                elem.latitude + ',' + elem.longitude + '&sensor=false&size=400x400&' +
                'markers=color:red%7C' + elem.latitude + ',' + elem.longitude;
            return location;
        };

        // List of posts
        // -------------
        $.getJSON(recall_config["api-base-url"] + "/mark",
                  function (data){
                      $.each(
                          data,
                          function(_, elem){
                              if(elem.hasOwnProperty('latitude')){
                                  var loc = renderLocation(elem);
                                  $("#marks").append(loc);
                              } else {
                                  $("#marks").append(renderComment(elem));        
                              }
                          });
                  });
    }
);
