/*
LabelX for Blogger (http://code.google.com/p/yjl/wiki/LabelX)
Copyright 2008, 2009 Yu-Jie Lin

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Author      : Yu-Jie Lin
Author Link : http://sites.google.com/site/livibetter/
*/

/*
 * Parses labels from specific Label widget
 *
 * Returns an array of labels. Each element is [name, url, count].
 */
function LX_ParseLabels(ele_id) {
	var labels = []
	$('#' + ele_id + ' div.widget-content ul li').each(function () {
		var $label = $(this);
		if ($label.children('span').length == 2) {
			// Selected label, in label page
			var name = $label.children('span:first').text().replace(/\n/g, '');
			var url = '#';
			var count = $label.children('span:last').text();	
			}
		else {
			// Also remove the tailling line return
			var name = $label.children('a').text().replace(/\n/g, '');
			var url = $label.children('a').attr('href');
			var count = $label.children('span').text();
			}
		// Remove parenthesis
		count = parseInt(count.substring(1, count.length - 1));
		labels.push([name, url, count]);
		});
	return labels;
	}

/*
 * Renderer function dispatcher
 */
function LX_Render(ele_id, style, options) {
	if ($('#' + ele_id).length != 1)
		return;
	var labels = LX_ParseLabels(ele_id);
	if (labels.length == 0)
		return;
	switch (style) {
		case 'cloud':
			LX_RenderCloud(labels, ele_id, options);
			break;
		case 'dropdown':
			LX_RenderDropdown(labels, ele_id, options);
			break;
		}
	}

/*
 * Renders labels as a cloud
 */
function LX_RenderCloud(labels, ele_id, options) {
	if ($('#' + ele_id + ' div.widget-content').length != 1)
		return;
	var $target =$('#' + ele_id + ' div.widget-content').eq(0);
	if (labels.length == 0)
		return;
	if (options.MinFontSize == undefined ||
	    options.MaxFontSize == undefined ||
		options.FontSizeUnit == undefined) {
		options.MinFontSize = 1.0;
		options.MaxFontSize = 2.0;
		options.FontSizeUnit = 'em';
		}
	options.FontSizeSpan = options.MaxFontSize - options.MinFontSize;
	// Sort by count
	labels = labels.sort(function(a, b) {
		return a[2] - b[2];
		});
	// Find maximum count
	options.MaxCount = labels[labels.length - 1][2];
	// Need to use max of int
	options.MinCount = labels[0][2];
	// TODO: dividen by zero
	options.CountSpan = options.MaxCount - options.MinCount;
	// Select only top/least items
	if (options.Limit != undefined) {
		if (options.Limit > 0)
			labels = labels.slice(0, options.Limit);
		else
			labels = labels.slice(options.Limit);
		}
	// Sort by name?
	if (options.SortByName != undefined && options.SortByName == true)
		labels = labels.sort(function(a, b) {
			if (a[0] == b[0]) return 0;
			if (a[0] < b[0]) return -1;
			if (a[0] > b[0]) return 1;
			});
	// Reverse?
	if (options.Reverse != undefined && options.Reverse == true)
		labels.reverse()

	// Print them out
	// Clean it up! Folks!
	$target.empty();
	for (var i = 0; i < labels.length; i++) {
		var $a = $('<a href="' + labels[i][1] + '">' + labels[i][0] + '</a>')
		$a.css('font-size', 
			(options.MinFontSize + (labels[i][2] - options.MinCount) / options.CountSpan * options.FontSizeSpan).toString() + options.FontSizeUnit
			);
		if (labels[i][2] == 1) 
			$a.attr('title', labels[i][2] + ' post');
		else
			$a.attr('title', labels[i][2] + ' posts');
		$target.append($a);
		$target.append(' ');
		}
	}

/*
 * Renders labels as a dropdown box
 */
function LX_RenderDropdown(labels, ele_id, options) {
	if ($('#' + ele_id + ' div.widget-content').length != 1)
		return;
	var $target =$('#' + ele_id + ' div.widget-content').eq(0);
	if (labels.length == 0)
		return;
	// Sort by count
	labels = labels.sort(function(a, b) {
		return a[2] - b[2];
		});
	// Sort by name?
	if (options.SortByName != undefined && options.SortByName == true)
		labels = labels.sort(function(a, b) {
			if (a[0] == b[0]) return 0;
			if (a[0] < b[0]) return -1;
			if (a[0] > b[0]) return 1;
			});
	// Reverse?
	if (options.Reverse != undefined && options.Reverse == true)
		labels.reverse()
	// Select only top/least items
	if (options.Limit != undefined) {
		if (options.Limit > 0)
			labels = labels.slice(0, options.Limit);
		else
			labels = labels.slice(options.Limit);
		}

	// Print them out
	// Clean it up! Folks!
	$target.empty();
	$box = $('<select><option selected>Labels</option></select>');
	$box.change(function () {
		var $box = $(this);
		var $selected = $box.find("option:selected");
		if ($selected.length != 1) return;
		$selected = $selected.eq(0);
		if ($selected.attr('value') != null)
			document.location = $selected.attr('value');
		});
	for (var i = 0; i < labels.length; i++) {
		var $option = $('<option value="' + labels[i][1] + '">' + labels[i][0] + ' (' + labels[i][2] + ')</option>')
		$box.append($option);
		}
	$target.append($box);
	}
