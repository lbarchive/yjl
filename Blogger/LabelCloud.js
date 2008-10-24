/*
LabelCloud for Blogger
Link          : http://makeyjl.blogspot.com
Version       : 0.1
Creation Date : 2008-09-25T08:03:57+0800
Modified Date : 2008-09-25T13:14:50+0800
License       : LGPLv3

Author        : Yu-Jie Lin
Author Link   : http://friendfeed.com/livibetter
*/
// Refer to variables
var LblCld;
var LblCldTitle;
var LblCldMinFontSize;
var LblCldMaxFontSize;
var LblCldFontSizeUnit;
var LblCldLimit;
var LblCldSortByName;
var LblCldTarget;

function RenderLabelCloud() {
	// Setting variables
	if (LblCldTarget == undefined) return;
	if (LblCld == undefined || LblCld.length == 0) return;
	if (LblCldMinFontSize == undefined ||
	    LblCldMaxFontSize == undefined ||
		LblCldFontSizeUnit == undefined) {
		LblCldMinFontSize = 1.0;
		LblCldMaxFontSize = 2.0;
		LblCldFontSizeUnit = 'em';
		}
	var LblCldFontSizeSpan = LblCldMaxFontSize - LblCldMinFontSize;
	// TODO: get nothing
	var ele = $(LblCldTarget).select('div.widget-content')[0];
	// Sort by count
	LblCld = LblCld.sortBy(function(lbl) { return lbl[2]; });
	// Find maximum count
	var LblCldMaxCount = LblCld[LblCld.length - 1][2];
	// Need to use max of int
	var LblCldMinCount = LblCld[0][2];
	// TODO: dividen by zero
	var LblCldCountSpan = LblCldMaxCount - LblCldMinCount;
	// Select only top/least items
	if (LblCldLimit != undefined)
		LblCld = LblCld.slice(LblCldLimit);
	// Sort by name?
	if (LblCldSortByName != undefined && LblCldSortByName == true)
		LblCld = LblCld.sortBy(function(lbl) { return lbl[0]; });
	// Print them out
	// Has title?
	if (LblCldTitle != undefined && LblCldTitle.length > 0)
		ele.insert({before: new Element('h2').update(LblCldTitle)});
	for (var i = 0; i < LblCld.length; i++) {
		ele.appendChild(new Element('a', {
			'href': LblCld[i][1],
			'style': 'font-size: ' + (LblCldMinFontSize+(LblCld[i][2]-LblCldMinCount)/LblCldCountSpan*LblCldFontSizeSpan).toString()+LblCldFontSizeUnit+';'
			}).update(LblCld[i][0]));
		ele.appendChild(document.createTextNode(' '));
		}
	}
