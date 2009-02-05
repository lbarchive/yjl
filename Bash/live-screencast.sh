#!/bin/bash

FPS=5
VIDEO_DEVICE=/dev/video0
GRAB_OFFSET=+0,25
IN_WIDTH=960
IN_HEIGHT=720

show_menu() {
  echo "Live Screencast Helper
1) Start to capture
2) Blur screen
3) Desaturate screen

L) Load Another Video Loopback Device
U) Unload Another Video Loopback Device

Q) Quit
"
  }

while [[ 1 ]]; do
  show_menu
  read -p "Choose? " choice
  case $choice in
    1)
      ffmpeg -f x11grab -vc rawvideo -s ${IN_WIDTH}x${IN_HEIGHT} -r $FPS -an -i :0.0$GRAB_OFFSET -f rawvideo -pix_fmt rgb24 - | mencoder - -demuxer rawvideo -rawvideo fps=$FPS:w=$IN_WIDTH:h=$IN_HEIGHT:format=rgb24 -nosound -ovc raw -vf scale=320:240,format=bgr24 -of rawvideo -ofps $FPS -o $VIDEO_DEVICE
      ;;
    2)
      ffmpeg -f x11grab -vc rawvideo -s ${IN_WIDTH}x${IN_HEIGHT} -r $FPS -an -i :0.0$GRAB_OFFSET -f rawvideo -pix_fmt rgb24 - | mencoder - -demuxer rawvideo -rawvideo fps=$FPS:w=$IN_WIDTH:h=$IN_HEIGHT:format=rgb24 -nosound -ovc raw -vf scale=320:240,format=bgr24 -ssf lgb=10:cgb=10 -of rawvideo -ofps $FPS -o $VIDEO_DEVICE
      ;;
    3)
      ffmpeg -f x11grab -vc rawvideo -s ${IN_WIDTH}x${IN_HEIGHT} -r $FPS -an -i :0.0$GRAB_OFFSET -f rawvideo -pix_fmt rgb24 - | mencoder - -demuxer rawvideo -rawvideo fps=$FPS:w=$IN_WIDTH:h=$IN_HEIGHT:format=rgb24 -nosound -ovc raw -vf hue=0:0,scale=320:240,format=bgr24 -of rawvideo -ofps $FPS -o $VIDEO_DEVICE
      ;;
    l|L)
      lsmod | grep avld &> /dev/null
      if [[ $? == 0 ]]; then
        echo "AVLD has been loaded, please unload it first."
        continue
      fi
      sudo modprobe avld width=320 height=240 fps=$FPS palette=0
      sleep 1
      sudo chmod 666 $VIDEO_DEVICE
      ;;
    u|U)
      lsmod | grep avld &> /dev/null
      if [[ $? == 0 ]]; then
        sudo rmmod avld
      fi
      ;;
    q|Q|x|X)
      echo "Bye!"
      break
      ;;
  esac

#Check
#mplayer tv:// -tv "driver=v4l:device=/dev/video0:noaudio:outfmt=bgr24" -vo x11 -fps 5

done

# vim:et:ts=2:sts=2:sw=2:ai
