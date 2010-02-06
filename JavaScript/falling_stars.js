/*
* Copyright (c) 2009, 2010, Yu-Jie Lin
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
* THIS SOFTWARE IS PROVIDED BY <copyright holder> ''AS IS'' AND ANY
* EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL <copyright holder> BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
/*
Author   : Yu-Jie Lin
Website  : http://j.mp/livibetter
Demo page: http://yjl.googlecode.com/JavaScript/falling_stars.html
*/

// Load jQuery
google.load("jquery", "1.3");

// Settings
// How many hearts?
FH_HEARTS = 40;
// Size range of heart in pixel
FH_HEART_SIZE = [12, 24];
// Possible range of falling interval in millisecond
FH_HEART_FALL_INTERVAL = [100, 1000];
// Possible range of falling distance in pixel
FH_HEART_FALL_DISTANCE = [1, 10];
// Possible range of flying distance in pixel
FH_HEART_FLY_DISTANCE = [-5, 5];
// Crating interval in millisecond
FH_CREATE_INTERVAL = 1000;
// Colors
FH_COLORS = [
  'FFD700',
  'D4AF37',
  'CBA135',
  'C5B358',
  'CFB53B',
  'FCC200',
  'FFCC33',
  'FFDF00',
  '996515'
  ]
// End of Settings

var falling_hearts = [];

function heart_on_timer(heart_id) {
  var heart = falling_hearts[heart_id];
  heart.fall();
  }

// Heart class
function Heart(index) {
  var $ = jQuery;
  // Construction
  if (index != undefined)
    this.index = index;
  this.$heart = $('<div>&#9733;</div>');
  this.$heart.css({
    'display': 'none',
    'position': 'absolute',
    'margin': 0,
    'padding': 0,
    'color': '#f00',
    'background' : 'none',
    'font-size': '16px',
    'cursor': 'default',
    'z-index': '1000'
    });
  this.heart_size = 16;
  // Methods
  this.set_position = function(x, y) {
    // Check if it goes out of screen
    if (x < 3)
      x = 3;
    var right_most = $(window).width() - this.$heart.width() - 3
    if (x > right_most)
      x = right_most;
    var bottom_most = $(window).height() - this.$heart.height() - 3
    if (y > bottom_most) {
      y = -this.$heart.height();
      this.$heart.fadeTo(1, 1);
      }
    else
      // Fading out if too close the bottom
      if (bottom_most - y <= 100)
        this.$heart.fadeTo('slow', (bottom_most - y) / 100)
    this.$heart.css({
      'display': 'block',
      'left': x.toString() + 'px',
      'top': y.toString() + 'px'
      });
    }

  this.fall = function() {
    var pos = this.$heart.position();
    // Falls
    this.set_position(
        pos.left + Math.floor(Math.random() * (FH_HEART_FLY_DISTANCE[1] - FH_HEART_FLY_DISTANCE[0] + 1)) + FH_HEART_FLY_DISTANCE[0],
        pos.top + Math.floor(Math.random() * (FH_HEART_FALL_DISTANCE[1] - FH_HEART_FALL_DISTANCE[0] + 1)) + FH_HEART_FALL_DISTANCE[0]);
    // Flashs in colors
    this.$heart.css('color', '#' + FH_COLORS[Math.floor(Math.random() * FH_COLORS.length)]);
    // Sizing
    this.heart_size = this.heart_size + 2 - Math.floor(Math.random() * 4);
    if (this.heart_size < FH_HEART_SIZE[0])
      this.heart_size = FH_HEART_SIZE[0];
    if (this.heart_size > FH_HEART_SIZE[1])
      this.heart_size = FH_HEART_SIZE[1];
    this.$heart.css('font-size', this.heart_size.toString() + 'px');
    window.setTimeout('heart_on_timer(' + this.index.toString() + ');',
        Math.floor(Math.random() * (FH_HEART_FALL_INTERVAL[1] - FH_HEART_FALL_INTERVAL[0] + 1)) + FH_HEART_FALL_INTERVAL[0]);
    }
  $('body').append(this.$heart);
  this.set_position(Math.floor(Math.random() * $('body').width()) + this.$heart.width(), -this.$heart.height());
  this.fall();
  }

// Main function
function start_falling_hearts() {
  var index = falling_hearts.length;
  if (index < FH_HEARTS) {
    falling_hearts.push(new Heart(index));
    window.setTimeout(start_falling_hearts, FH_CREATE_INTERVAL)
    }
  }

google.setOnLoadCallback(start_falling_hearts);

// vim:et:ts=2:sts=2:sw=2:ai
