function collapse_pre() {
  $('.post-content pre').each(function (idx, pre) {
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
  $(".post-content img").each(function(i, e){
      var $e = $(e);
      if ($e.css("float") != "none" || $e.hasClass("no-autoresize")) return;
      if ($e.width() != max_width) $e.width(max_width);
      });
  // Unwrapper
  if ($('.wrapper').length > 0) {
    $(window).resize(function(){
      $.each($('.unwrapper'), function(idx, ele) {
        var $e = $(ele);
        // reset
        $e.css('margin-left', '0px');
        $e.css('margin-right', '0px');
      
        $e.css('margin-left', (-parseInt($e.offset().left) + parseInt($('body').css('margin-left')) + parseInt($('body').css('padding-left')))+ 'px');
        $e.css('margin-right', (-$('body').outerWidth() + $e.outerWidth() + parseInt($('body').css('margin-right')) + parseInt($('body').css('padding-right'))) + 'px');
        });
      });
    $(window).resize();
    }

  // Code highlighting
  if ($('pre code').length > 0) {
    $.getScript('http://www.yjl.im/js/highlight.pack.js', function() {
        hljs.initHighlighting();
        // Collapse pre blocks
        collapse_pre();
        });
    }
  else {
    // Collapse pre blocks
    $(function(){
        collapse_pre();
        });
    }
  
  // BRPS
  if ($('#gas-results').length > 0) {
    window.brps_gas = {
        remove_tags: ['OldBlogBlogarbage', 'OldBlogGetCtrlBack', 'OldBlogTheBThing', 'OldBlogTuxWearsFedora', 'OldBlogmakeYJL',
            'StatusDraft'],
        limit: 10,
        remove_string_regexp: /(^.*?: | &lt;&lt;.*$)/,
        exclude_url_regexp: /(\/search\/label\/|(archive\.html|blog\.yjl\.im\/|\.blogspot\.com\/)$)/
        };
    }

  // Clicked link highlighter
  function _highlight_a(e){
    // find old highlighted
    $('a.highlighted').removeClass('highlighted');
    $(e).addClass('highlighted');
    }
  
  $('a')
      .mousedown(function(evt){
          _highlight_a(this);
          })
      .keyup(function(evt){
          if (evt.keycode == 13)
            _highlight_a(this);
          })
      ;

  // Don't go below?
  if (document.location.protocol == 'file:' || document.location.host == 'localhost')
    return
  // Disqus
  var query = '?';
  $.each($('a[href$=#disqus_thread]'), function (idx, ele) {
      query += 'url' + idx + '=' + encodeURIComponent(ele.href) + '&';
      });
  $.getScript('http://disqus.com/forums/yjlv/get_num_replies.js' + query);
  // If visitors are led to comments, then load comments automatically.
  var href = document.location.href;
  if (href.indexOf('#disqus_thread') >= 0 || href.indexOf('#comment-') >=0) {
    $.getScript('http://yjlv.disqus.com/embed.js');
    $('#comments-loader-button').remove();
    }

  // Google Analytics
  function _track() {
    var _gaq = window._gaq || [];
    _gaq.push(['_setAccount', 'UA-15896368-3']);
    _gaq.push(['_trackPageview']);
    if (!window._gaq)
      window._gaq = _gaq;
    }
  if (window._gaq) {
    _track();
    }
  else {
    $.getScript(('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js', _track);
    }
  });

// vim: set sw=2 ts=2 et:
