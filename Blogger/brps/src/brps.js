// Blogger.com Related Posts Service (http://brps.appspot.com/)
//
// Copyright (C) 2008  Yu-Jie Lin
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
//
// Author : Yu-Jie Lin
// Website: http://friendfeed.com/livibetter


google.load('jquery', '1.2.6');
google.setOnLoadCallback(function() {
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
    $.getJSON("http://brps.appspot.com/get?blog=" + blog_id + "&post=" + post_id + "&callback=?",
        function(data){
          $('<h2>Related Posts</h2>').appendTo('#related_posts');
          if (data.entry.length > 0)
            $('<ul></ul>').appendTo('#related_posts');
            $.each(data.entry, function(i, entry){
              $('<li><a href="' + entry.link + '">' + entry.title + '</a></li>').appendTo('#related_posts ul');
            });
          else
            $('<p>No related post found.</p>').appendTo('#related_posts');
        });
    }
  });
