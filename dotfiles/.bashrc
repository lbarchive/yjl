# .bashrc
# Author: Yu-Jie Lin
# Creation Date: 2007-12-27T05:58:17+0800

# User specific aliases and functions
alias ll='ls -l --color=auto'
alias l.='ls -d .* --color=auto'
alias ls='ls --color=auto'

alias vi='vim'
alias mc='/usr/bin/mc -x'
alias hl='highlight -q -s vim-dark -M'
alias lhl='less -R'

# Let shell-fm run with socket opening
#alias shell-fm="$HOME/bin/shell-fm -i localhost"

# for root
if [ `id -u` -eq 0 ]; then
	alias rm='rm -i'
	alias cp='cp -i'
	alias mv='mv -i'
fi

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

export XMODIFIERS="@im=gcin"
export GTK_IM_MODULE="gcin"
export QT_IM_MODULE="gcin"
#export XMODIFIERS="@im=ibus"
#export GTK_IM_MODULE="ibus"
#export QT_IM_MODULE="ibus"

[[ -f $HOME/p/yjl/Bash/g ]] && . /home/livibetter/p/yjl/Bash/g || echo "Can not found g script!"

for comp in ~/.bash_completion.d/* ; do
    if [ -r "$comp" ] ; then
        . "$comp"
    fi
done
unset comp

if [[ $RUNDIALOG == 1 ]]; then
	. /home/livibetter/.runrc
else
# Prompt
[ $TERM == 'linux' ] && STR_MAX_LENGTH=2 || STR_MAX_LENGTH=3
DIR_COLOR='\[\e[1;32m\]'
DIR_SEP_COLOR='\[\e[1;31m\]'
ABBR_DIR_COLOR='\[\e[1;37m\]'
HOSTNAME_COLOR='\[\e[1;33m\]'
AT_COLOR='\[\e[1;36m\]'
[ $UID == '0' ] && USER_COLOR='\[\e[1;31m\]' || USER_COLOR='\[\e[1;34m\]'

NEW_PWD='$(
p="${PWD/$HOME/}";
[ "$p" != "$PWD" ] && echo -n "~";
i=0;
until [ "$p" = "$d" ]; do
    p=${p#*/};
    d=${p%%/*};
    dirnames[i]=$d;
    (( i += 1 ));
done;
for i in $(seq 0 $((${#dirnames[@]} - 1))); do
    if [ $i -eq 0 ] || [ $i -eq $((${#dirnames[@]} - 1)) ] || [ ${#dirnames[$i]} -le '"$STR_MAX_LENGTH"' ]; then
        echo -n "'"$DIR_SEP_COLOR"'/'"$DIR_COLOR"'${dirnames[$i]}";
    else
        echo -n "'"$DIR_SEP_COLOR"'/'"$ABBR_DIR_COLOR"'${dirnames[$i]:0:'"$STR_MAX_LENGTH"'}";
    fi;
done
)'
PS1_ERROR='$(
ret=$?;
if [ $ret -gt 0 ]; then
    (( i = 3 - ${#ret} ));
    echo -n "\[\e[41;1;37m\] [";
    [ $i -gt 0 ] && echo -n " ";
    echo -n "$ret";
    [ $i -eq 2 ] && echo -n " ";
    echo -n "] \[\e[0m\]";
fi
)'

if [ $TERM == 'screen' ]; then
    PS1="$PS1_ERROR$USER_COLOR\u$AT_COLOR@$HOSTNAME_COLOR\h $DIR_COLOR$NEW_PWD"'\[\033k\033\\\]'" $USER_COLOR> \[\e[0m\]"
else
    PS1="$PS1_ERROR$USER_COLOR\u$AT_COLOR@$HOSTNAME_COLOR\h $DIR_COLOR$NEW_PWD $USER_COLOR> \[\e[0m\]"
fi

unset STR_MAX_LENGTH DIR_COLOR DIR_SEP_COLOR ABBR_DIR_COLOR HOSTNAME_COLOR AT_COLOR USER_COLOR NEW_PWD PS1_ERROR
fi
