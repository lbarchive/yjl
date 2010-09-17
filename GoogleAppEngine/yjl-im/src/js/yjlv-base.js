function collapse_pre() {
  $('.post-body pre').each(function (idx, pre) {
    var $pre = $(pre);
    if ($pre.height() <= 200 || $pre.hasClass('no-collapse'))
      return
    pre.expand_height = $pre.height();
    $pre
      .css({
        cursor: 'pointer',
        overflow: 'hidden'
        })
      .animate({
        height: 100,
        opacity: 0.5
        }, 'slow', function () {
          $(this)
            .attr('title', 'Click to expand')
            .click(function () {
              $(this).animate({
                height: this.expand_height,
                opacity: 1.0
                }, 'slow', function () {
                  $(this)
                    .unbind('click')
                    .css({
                      cursor: 'auto',
                      overflow: 'auto'
                      })
                    .attr('title', '')
                    ;
                  this.expand_height = undefined;
                  })
              })
            ;
          })
      ;
    });
  }

$(function(){
  // Image resizing
  var max_width = 640 - 1*2 - 5*2;
  $(".post-body img").each(function(i, e){
      var $e = $(e);
      if ($e.css("float") != "none" || $e.hasClass("no-autoresize")) return;
      if ($e.width() != max_width) $e.width(max_width);
      });
  // jknav
  $('h3').jknav();
  $.jknav.init({up: 'l', down: 'h', reevaluate: true}); 
  $('h3.post-title,.post-body h4,.post-body h5,.post-body h6').jknav(null, 'all-headers');
  $.jknav.init({name: 'all-headers', reevaluate: true});
  });

// Scope issue with getScript(), executing them directly seems fine.

// Code highlighting
if ($('pre code').length > 0)
  $.getScript('http://www.yjl.im/js/highlight.pack.js', function() {
      hljs.initHighlighting();
      // Collapse pre blocks
      collapse_pre();
      });
else
  // Collapse pre blocks
  $(function(){
      collapse_pre();
      });

// BRPS
if ($('#gas-results').length > 0) {
  window.brps_gas = {
      limit: 10,
      add_sites: [
          'blogarbage.blogspot.com',
          'fedoratux.blogspot.com',
          'getctrlback.blogspot.com',
          'makeyjl.blogspot.com',
          'thebthing.blogspot.com'
          ],
      remove_string_regexp: /(^(YJL --verbose|Blogarbage|Tux Wears Fedora|Get Ctrl Back|make YJL|The B Thing): | <<< \$\(YJL --verbose\)$)/,
      exclude_url_regexp: /(.*archive\.html|blog\.yjl\.im\/$|(blogarbage|fedoratux|getctrlback|makeyjl|thebthing)\.blogspot\.com\/$)/
      };
  $.getScript('http://brps.appspot.com/gas.js');
  }
// vim: set sw=2 ts=2 et:
