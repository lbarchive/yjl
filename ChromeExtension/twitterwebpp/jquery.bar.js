(function($) {
	
	$.fn.bar = function(options) {

		var opts = $.extend({}, $.fn.bar.defaults, options);
		
    return this.each(function() {
			$this = $(this);
			var o = $.meta ? $.extend({}, opts, $this.data()) : opts;

      // Make sure we have new click, so new opts
			$this.unbind('click');
			
      $this.click(function(e){
				if(!$('.jbar').length){
					timeout = setTimeout('$.fn.bar.removebar()', o.time);
          var _message_span = $('<span/>', {class: 'jbar-content', html: o.message});

					var _wrap_bar;
          _wrap_bar = $('<div/>', {
              class: 'jbar jbar-bottom ' + o.class,
              css: {
                  backgroundColor: o.background_color,
                  color: o.color,
                  cursor: "pointer"
                  },
              click: function(e){$.fn.bar.removebar();}
              });

          _wrap_bar
              .append(_message_span)
              .hide()
              .appendTo($('body'))
              .animate({height: '+=' + o.height, opacity: o.opacity}, 'slow');
				}
			})
		});
	};

	var timeout;
	
  $.fn.bar.removebar 	= function() {
		if($('.jbar').length){
			clearTimeout(timeout);
      $('.jbar').animate({height: '-=50', opacity: 0}, 'slow', function(){
  				$(this).remove();
		    	});
		}	
	};
	
  $.fn.bar.defaults = {
		background_color: '#467D99',
		color: '#FFF',
    height: 50,
    opacity: 0.9,
		time: 1500
	};
	
})(jQuery);
