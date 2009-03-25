// Blogger.com Related Posts Service (http://brps.appspot.com/)
//
// Copyright (C) 2008, 2009  Yu-Jie Lin
//  
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//  
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


var brps_options;


google.load('jquery', '1.3');
google.setOnLoadCallback(function() {
  BRPS_get();
  });

function BRPS_render_widget_title() {
  var $ = jQuery;
  if (brps_options && brps_options.title)
    $(brps_options.title).appendTo('#related_posts');
  else
    $('<h2>Related Posts</h2>').appendTo('#related_posts');
  }

function BRPS_get() {
  var $ = jQuery;
  // Get Blog ID
  link = $($('link[rel=EditURI]')[0]).attr('href')
  var blog_id = ''
  blog_id = /.*blogID=(\d+)/.exec(link)[1]
  // Get Post ID
  links = $('link[rel=alternate]')
  var post_id = ''
  for (var i=0; i < links.length; i++) {
    m = /.*\/feeds\/(\d+)\/comments\/default/.exec($(links[i]).attr('href'))
    if (m != null)
      if (m.length == 2) {
        post_id = m[1];
        break;
        }
    }
  if (blog_id != '' && post_id != '') {
    $('#related_posts').empty()
    BRPS_render_widget_title();
    $('<i>Loading...</i>').appendTo('#related_posts');
    max_results = (brps_options && brps_options.max_results)
        ? '&max_results=' + brps_options.max_results.toString()
        : '';
    $.getJSON("http://brps.appspot.com/get?blog=" + blog_id + "&post=" + post_id + max_results + "&callback=?",
        function(data){
	    	  var $ = jQuery;
          $('#related_posts').empty()
          BRPS_render_widget_title();
          if (data.error) {
            $('<p>' + data.error + '</p>').appendTo('#related_posts');
            if (data.code == 3)
              // Need to retry in 5 seconds
              window.setTimeout('BRPS_get()', 5000);
    		  	}
		      else {
            if (data.entry.length > 0) {
              src = (brps_options && brps_options.append_src) ? '?src=brps' : '';
              $('<ul></ul>').appendTo('#related_posts');
              $.each(data.entry, function(i, entry){
                $('<li><a hr' + 'ef="' + entry.link + src + '" title="Score: ' + entry.score.toString() + '">' + entry.title + '</a></li>').appendTo('#related_posts ul');
                });
              }
            else {
              $('<p>No related posts found.</p>').appendTo('#related_posts');
              }
            }
        });
    }
  }
// vim:ts=2:sw=2:et:
