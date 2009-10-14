/*
* Copyright (c) 2009, Yu-Jie Lin
* All rights reserved.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*     * Redistributions of source code must retain the above copyright
*       notice, this list of conditions and the following disclaimer.
*     * Redistributions in binary form must reproduce the above copyright
*       notice, this list of conditions and the following disclaimer in the
*       documentation and/or other materials provided with the distribution.
*
* THIS SOFTWARE IS PROVIDED BY Yu-Jie Lin ''AS IS'' AND ANY
* EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL Yu-Jie Lin BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
/*
Bookmarklet URI:
javascript:void((function(){$.getScript('http://yjl.googlecode.com/hg/JavaScript/TwitRT.js')})())

Author   : Yu-Jie Lin
Website  : http://livibetter.mp/
Demo page: 
*/
// Make each status holder taller
$('ol.statuses > li').css('padding-bottom', '1.6em');

var eles = $('#timeline > .status > .actions > div');
if (eles.length == 0)
	// Search results do not have a div wrapper
	eles = $('#timeline > .status > .actions')
eles.each(function(){
	var ele = $(this);
	// Make sure this script does not add more than one retweet button to each status
	if (ele.find('.retweet').length == 0)
		var rt_ele = $('<a class="retweet" title="retweet this tweet" href="#"><img src="http://yjl.googlecode.com/hg/JavaScript/TwitRT.png"/></a>').click(function(){
			var ele = $(this);
			var par = ele.parents('.status');
			var rt_status = 'RT @' + par.find('.screen-name').text() + ' '
				// Home or profile pages
				+ par.find('.entry-content').text()
				// Search page
				+ par.find('.msgtxt').text;
			var ele_status = $('#status');
			if (ele_status.length == 0) {
				// This page has NO status input box such as someone's profile page
				window.open('http://twitter.com/?status=' + encodeURIComponent(rt_status));
				}
			else {
				// This page has status input box such as home page
				ele_status.val(rt_status);
				}
			});
		ele.append(rt_ele);
	});
