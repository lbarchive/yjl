if (chrome.extension.getURL('').indexOf('mhhfojhaplkgphlfkenicgdacjkhhjhd') < 0) {
  // Probably the published one, shut console's mouth up
  // TODO Add a wrapper so user can choose (in Options page) to see debug information
  console.debug = function() {};
  }


var config = null;
// Current logged user's screen name
var screen_name = null;

// A hack
var before_reply_cursor_pos = null;
var before_reply_status = null;

// Trending Topic
var RE_TT_DIM = [];
var RE_TT_REMOVE = [];


/**
 * Insert Quick Text into status box
 */
function quicktext_insert (texts) {

  var e = $('#status')[0];
  var start = e.selectionStart;
  var end = e.selectionEnd;
  var text_before = e.value.substring(0, start);
  var text_selected = e.value.substring(start, end);
  var text_after = e.value.substring(end);
  
  e.value = text_before + texts[0] + text_selected + texts[1] + text_after;

  e.selectionStart = e.selectionEnd = start + texts[0].length + texts[1].length + text_selected.length +
    // If there is no selection, then put cursor in between two inserted texts
    (text_selected.length == 0 ? -texts[1].length : 0)
  
  }


/**
 * A callback to handle returned data from XHR for shortening URLs
 */
function update_surl(resp) {

  console.debug(resp);
  if (!resp.data || !resp.data.data || !resp.data.data.url) {
    // Reset cursor
    var e = $('#status')[0];
    e.focus();
    console.debug('ERROR: ', resp.xhr.responseText);
    $('#jbar').bar({
        message: 'ERROR ' + resp.data.status_code + ': ' + resp.data.status_txt,
        class: 'jbar-error',
        time: 5000
        })
        .click();
    return
    }

  var data = resp.data.data;
  var e = $('#status')[0];
  var start = e.selectionStart;
  var end = e.selectionEnd;
  var text_before = e.value.substring(0, start);
  var text_selected = e.value.substring(start, end);
  var text_after = e.value.substring(end);
  console.debug('XHR result: ', data);
  e.value = text_before + '<' + data.url + '>' + text_after;
  e.selectionStart = e.selectionEnd = start + data.url.length + 2;
  
  }


/**
 * Initialize shortening URL process
 */
function do_surl(service) {

  var e = $('#status')[0];
  var start = e.selectionStart;
  var end = e.selectionEnd;
  var url = $.trim(e.value.substring(start, end));
  if (url == '' && (url = $.trim(prompt('Enter a URL'))) == '')
    return
  
  switch (service) {
    case 'bitly':
      chrome.extension.sendRequest({command: 'request_xhr', method: 'GET',
        url: 'http://api.bit.ly/v3/shorten?uri=' + encodeURI(url) + '&login=livibetter&apiKey=R_78405bb48525800fb880b41721029724&format=json'
        }, update_surl);
      break;
    case 'jmp':
      chrome.extension.sendRequest({command: 'request_xhr', method: 'GET',
        url: 'http://api.j.mp/v3/shorten?uri=' + encodeURI(url) + '&login=livibetter&apiKey=R_78405bb48525800fb880b41721029724&format=json'
        }, update_surl);
      break;
    }
  
  }


/**
 * Add Self-reply button to own tweets
 */
function process_self_reply() {

  var path_start = (document.location.protocol + '//' + document.location.host).length + 1;
  // The second selector is for status page
  $('#timeline.statuses li.status:not(.twpp-self-reply-check),' +
      '#show div#permalink.status:not(.twpp-self-reply-check)').each(function (idx, ele) {
      var $status = $(ele).addClass('twpp-self-reply-check');
      if ($status.find('ul.actions-hover span.reply').length > 0)
        return
      //var tweet_screen_name = ($status.attr('id') == 'permalink') ? $status.find(: $status.find('span.status-content a.screen-name').text();
      var tweet_screen_name = $status.find('.thumb a.profile-pic').attr('href').substring(path_start);
      var tweet_status_id = $status.attr('id').split('_')[1];
      console.debug('tweet screen_name: %s status_id: %s', tweet_screen_name, tweet_status_id);
      var $reply_button = $('<li/>').append(
          $('<span/>', {class: 'reply'})
              .append($('<span/>', {class: 'reply-icon icon'}))
              .append($('<a/>', {
                  href: '/?status=%40' + tweet_screen_name + '&in_reply_to_status_id=' + tweet_status_id + '&in_reply_to=' + tweet_screen_name,
                  title: 'reply to ' + tweet_screen_name,
                  text: 'Self-reply'
                  }))
          );
      $status.find('ul.actions-hover').prepend($reply_button);
      })

  }


/**
 * Find atoms
 */
function find_atoms($tweet) {
  
  var $entry_content = $tweet.find('span.entry-content');
  var users = [];
  var lists = [];
  var hashtags = [];

  var path_start = (document.location.protocol + '//' + document.location.host).length + 1;

  function push_user(idx, a) {
    // Grab from href, it has correct character cases
    if (!!screen_name && $(a).text().toLowerCase() == screen_name.toLowerCase())
      return
    var user = '@' + a.href.substring(path_start);
    if ($.inArray(user, users) > -1)
      return
    users.push(user);
    }

  // Find users
  if (config.pull_users_enabled)
    $entry_content.find('a.username').each(push_user);
  
  // Put RTer into `users`, should only have one at most
  if (config.pull_rter_enabled)
    $tweet.find('span.shared-content a.screen-name').each(push_user);

  // Find lists
  if (config.pull_lists_enabled)
    $entry_content.find('a.list-slug').each(function (idx, a) {
        // Grab from href, it has correct character cases
        var list = '@' + a.href.substring(path_start);
        if ($.inArray(list, lists) > -1)
          return
        lists.push(list);
        });
  
  // Find hashtags
  if (config.pull_hashtags_enabled)
    $entry_content.find('a.hashtag').each(function (idx, a) {
        var hashtag = $(a).text();
        if ($.inArray(hashtag, hashtags) > -1)
          return
        hashtags.push(hashtag);
        });

  if (users.length || lists.length || hashtags.length)
    console.debug(users, lists, hashtags);

  return [users, lists, hashtags];
  }


/**
 * Hack to store cursor position and status text
 */
function track_status() {

  var e = $('#status')[0];
  before_reply_cursor_pos = e.selectionEnd;
  before_reply_status = e.value;
  
  }


/**
 * Handle Reply button click
 */
function onreply() {

  console.debug(arguments.callee.name, '()');
  
  // Clean up all tweets with class twpp-onreply
  $('#timeline.statuses li.status.twpp-onreply').removeClass('twpp-onreply');
  
  var $tweet = $(this).parents('li.status');
  $tweet.addClass('twpp-onreply');

  var $status_box = $('#status');
  var tweet_screen_name = $tweet.find('span.status-content a.screen-name').text();
  var re = new RegExp('@' + tweet_screen_name + '\\b', 'gi');

  var endpos = before_reply_cursor_pos;
  if ($.trim(before_reply_status) == '')
    // Empty status
    endpos = tweet_screen_name.length + 2;
  if (!re.exec(before_reply_status))
    // tweet_screen_name not in #status before, characters are inserted by
    // Twitter's reply function.
    endpos += tweet_screen_name.length + 2
  else
    // Already has that screen_name
    if (before_reply_status.indexOf('@' + tweet_screen_name) >= before_reply_cursor_pos)
      endpos += tweet_screen_name.length + 2;
    // FIXME need to check if under cursor

  var ret = find_atoms($tweet);
  var users = ret[0];
  var lists = ret[1];
  var hashtags = ret[2];

  var items = [];
  if (config.pull_users_enabled || config.pull_rter_enabled)
    $.merge(items, users);
  if (config.pull_lists_enabled)
    $.merge(items, lists);
  if (config.pull_hashtags_enabled)
    $.merge(items, hashtags);
 
  $.each(items, function (idx, item) {
      var s = $status_box.val();
      // FIXME '@aaa' skips if '@aaabbb' already in `s`.
      if (s.indexOf(item) == -1)
        $status_box.val($.trim(s) + ' ' + item);
      });
  var text = $status_box.val();
  if (endpos < text.length && text[endpos - 1] == ' ' && text[endpos] != ' ')
    $status_box.val(text.substring(0, endpos) + ' ' + text.substring(endpos));
  // Reset cursor the previous position before insert users/lists/hashtags.
  $status_box[0].selectionStart = $status_box[0].selectionEnd = endpos;
  
  }


/**
 * Fix Reply button's href, use in pages without #status
 * Need to put atoms into href
 */
function fix_reply_href() {
  
  // The second selector is for status page
  $('li.status:not(.twpp-fix-reply-check) ul.actions-hover span.reply a,' +
      'div.status:not(.twpp-fix-reply-check) ul.actions-hover span.reply a').each(function (idx, a) {

      var $a = $(a);
      var $tweet = $(this).parents('li.status, div.status');
      $tweet.addClass('twpp-fix-reply-check');
      
      var href = a.href;
      // http://twitter.com/?status=@screen_name&in_reply_to_status_id=99999999999&in_reply_to=screen_name
      // Find the first '&'
      var ins_pos = href.indexOf('&');
      
      var ret = find_atoms($tweet);
      var users = ret[0];
      var lists = ret[1];
      var hashtags = ret[2];

      // The replyee may be in tweet
      var tweet_screen_name = '@' + $tweet.find('span.status-content a.screen-name').text();
      users = users.filter(function (u) {return u != tweet_screen_name});

      var items = [];
      if (config.pull_users_enabled || config.pull_rter_enabled)
        $.merge(items, users);
      if (config.pull_lists_enabled)
        $.merge(items, lists);
      if (config.pull_hashtags_enabled)
        $.merge(items, hashtags);
        
      if (items.length == 0)
        return
      
      var ins_text = ' ' + items.join(' ');
      a.href = a.href.substring(0, ins_pos) + encodeURIComponent(ins_text) + a.href.substring(ins_pos);
      });
  
  }


/**
 * Process trending topics
 */
function process_trending_topic() {

  $('#trends ul.trends-links li a:not(.twpp-tt-check)').each(function (idx, ele) {
      var $topic = $(ele);
      $topic.addClass('twpp-tt-check');
      var text = $topic.text();
      
      if (config.tt_remove_enabled) {
        $.each(RE_TT_REMOVE, function (idx, ele) {
            var re = new RegExp(ele, 'gi');
            if (re.exec(text)) {
              console.debug('Remove', text, ele);
              $topic.addClass('twpp-tt-remove');
              return true
              }
            })

        if ($topic.hasClass('twpp-tt-remove'))
          return
        }
        
      if (config.tt_dim_enabled)
        $.each(RE_TT_DIM, function (idx, ele) {
            var re = new RegExp(ele, 'gi');
            if (re.exec(text)) {
              console.debug('Dim', text, ele);
              $topic.addClass('twpp-tt-dim');
              return true
              }
            });
      });

  }


/**
 * Process new stuff
 */
function periodic_process() {

  if (config.self_reply_enabled)
    process_self_reply();

  if (config.pull_users_enabled || config.pull_lists_enabled ||
      config.pull_hashtags_enabled || config.pull_rter_enabled)
    fix_reply_href();
  
  if ($('#status').length == 1)
    if (config.tt_dim_enabled || config.tt_remove_enabled)
      process_trending_topic();
  
  setTimeout(periodic_process, 1000);

  }


/**
 * Initialize Shortening URL area
 */
function initialize_surl() {
  
  console.debug(arguments.callee.name, '()');
  var $surl = $('#twpp_surl');

  $.each(config.surl_services, function (key, surl) {
      if (!surl.enabled)
        return
      $surl.append($('<input/>', {type: 'button', value: surl.name, click: function () {do_surl(key);}}));
      });
  
  $twpp.append($surl);

  }


/**
 * Initialize QuickText area
 */
function initialize_quicktext() {
  
  console.debug(arguments.callee.name, '()');
  var $quicktext = $('#twpp_quicktext');
  
  var quicktext = config.quicktext;


  $.each(quicktext.split('\n'), function (idx, val) {
    var vals = val.split(':', 3);
    if (vals[0] == '')
      return
    var title = vals[0];
    var texts = (vals.length == 1) ? [title] : vals.slice(1);
    if (texts.length == 1)
      texts.push('')
    $quicktext.append($('<input/>', {type: 'button', value: title, click: function() {quicktext_insert(texts)}}));
    });

  $twpp.append($quicktext);
 
  }


/**
 * Initialize Twpp replying
 */
function initialize_reply() {

  $('#timeline.statuses li.status span.reply').live('click', onreply);
  // Use mouseenter to catch current cursor in #status, hope no one move mouse
  // over, then type something, then click
  $('#status').bind('blur', track_status);
  
  }


/**
 * Initialize Trending process
 */
function initialize_trending_process() {

  // Compile regexps
  var tt_dim = config.tt_dim.split('\n');
  var tt_remove = config.tt_remove.split('\n');

  $.each(tt_dim, function(idx, ele) {
      if (ele)
        RE_TT_DIM.push(ele);
      });

  $.each(tt_remove, function(idx, ele) {
      if (ele)
        RE_TT_REMOVE.push(ele);
      });
  
  }


/**
 * When there is a preload tweet status, the cursor should be after @reply, not
 * the end of tweet.
 */
function fix_cursor_preload_tweet() {

  console.debug(arguments.callee.name, '()');

  var $status = $('#status');
  var text;

  if (location.href.indexOf('status=') < 0 || $status.length == 0 || (text = $status.val()) == '')
    return

  var status = $status[0];

  var m = /^@[_a-z0-9]+\b/i.exec(text);
  console.debug(text, m);

  if (m.length == 0)
    return

  m = m[0];

  console.debug(m.length, text.length);
  text = text.substring(0, m.length) + ' ' + ((m.length == text.length) ? '' : text.substring(m.length));
  
  $status.val(text);
  status.selectionStart = status.selectionEnd = m.length + 1;

  }


/**
 * Main initialization subroutine, bring up other initializations
 */
function initialize() {

  console.debug(arguments.callee.name, '()');

  $('body').append($('<div/>', {id: 'jbar'}));

  screen_name = $('meta[name=session-user-screen_name]').attr('content');
  console.debug('Current user: ', screen_name);

  fix_cursor_preload_tweet();

  if ($('#status').length == 1) {
    $twpp = $('<div/>', {id: 'twpp'});
    var $surl = $('<div/>', {id: 'twpp_surl'});
    var $quicktext = $('<div/>', {id: 'twpp_quicktext'});

    // Layout
    $twpp
        .append($surl)
        .append($quicktext)

    $('#status').before($twpp);
    $twpp.hide()

    if (config.surl_enabled)
      initialize_surl();
    if (config.qt_enabled)
      initialize_quicktext();
    if (config.pull_users_enabled || config.pull_lists_enabled ||
        config.pull_hashtags_enabled || config.pull_rter_enabled)
      initialize_reply();
    if (config.tt_dim_enabled || config.tt_remove_enabled)
      initialize_trending_process();

    $twpp.animate({height: 'toggle', opacity: 'toggle'}, 'normal');
    }
  
  periodic_process();

  }


/**
 * Load config from storage
 */
function load_config(callback) {
  
  console.debug(arguments.callee.name, '()');
  chrome.extension.sendRequest({command: 'request_config'}, function(response) {
    console.debug('Config loadded');
    config = response;
    callback();
    });

  }


load_config(initialize);
// vim: set sw=2 ts=2 et:
