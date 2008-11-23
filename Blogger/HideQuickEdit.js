// Hide Quick Edit Buttons
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


google.load('jquery', '1.2.6');
google.setOnLoadCallback(function() {
  var $ = jQuery;
  // Check if there is any quick edit buttons
  $buttons = $('a.quickedit');
  if ($buttons.length == 0) return;
  $buttons.hide();
  // Add restore button
  $('<img style="position:absolute;left:10px;top:40px;z-index:1000;cursor:pointer;" title="Restore Quick Edit Buttons" height="18" src="http://img1.blogblog.com/img/icon18_wrench_allbkg.png" width="18"/>')
    .appendTo('body')
    .click(function() {
      $('a.quickedit').show();
      $(this).hide();
      });
  });

// vim:ts=2:expandtab
