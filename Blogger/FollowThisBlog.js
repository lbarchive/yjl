// Follow This Blog Bookmarklet for Blogger.com
//
// This script is in Public Domain
//
// Author : Yu-Jie Lin
// Website: http://sites.google.com/site/livibetter/

function getElementAttr(ele, attr_name) {
  for (var i=0; i<ele.attributes.length; i++)
    if (ele.attributes[i].nodeName.toLowerCase() == attr_name.toLowerCase())
      return ele.attributes[i].nodeValue;
  return null;
  }

function matchElementAttr(ele, attr_name, attr_value) {
  for (var i=0; i<ele.attributes.length; i++)
    if (ele.attributes[i].nodeName.toLowerCase() == attr_name.toLowerCase() &&
        ele.attributes[i].nodeValue == attr_value)
      return true;
  return false;
  }

var found_blog = false;
var links = document.getElementsByTagName('link');
for (var i=0; i<links.length; i++) {
  if (matchElementAttr(links[i], 'rel', 'EditURI')) {
    var m = /.*blogID=(\d+)/.exec(getElementAttr(links[i], 'href'));
    if (m != null) {
      var f = 'http://www.blogger.com/follow-blog.g?blogID=' + m[1];
      f += (f.indexOf("?") > 0 ? "&" : "?") + "loginTemplateDirectory=FOLLOWING";
      window.open(f, "_blank", "height=600, width=640, toolbar=no, menubar=no, scrollbars=yes, resizable=yes, location=no, directories=no, status=no")
      found_blog = true;
      break;
      }
    }
  }
if (!found_blog)
  alert('This is not a Blogger.com blog!');
// vim:ts=2:sw=2:et:
