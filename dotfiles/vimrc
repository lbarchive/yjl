" Can not use the next setting with tmux
set t_Co=256 

colorscheme koehler

set sts=0
set ai ts=4
set sw=4
set tw=0
"set expandtab

set mouse=a
set ttymouse=xterm
set sessionoptions=blank,buffers,curdir,folds,help,resize,tabpages,winsize
" http://www.linux.com/archive/articles/54936
imap <F6> <ESC>:set ttym=xterm2<CR>
nmap <F6> <ESC>:set ttym=xterm2<CR>
imap <F6><F6> <ESC>:set ttym=<CR>
nmap <F6><F6> <ESC>:set ttym=<CR>

imap <C-X><C-X> <ESC>:tabnew<CR>
nmap <C-X><C-X> :tabnew<CR>
imap <C-X><Left> <ESC>:tabp<CR>
nmap <C-X><Left> :tabp<CR>
imap <C-X><Right> <ESC>:tabn<CR>
nmap <C-X><Right> :tabn<CR>

imap <F4> <C-R>=strftime("%FT%T%z")<CR>
nmap <F4> "=strftime("%FT%T%z")<CR>p

"nmap <F5><F5> :!bash sync<CR>

" no highlight
nmap @ :nohl<CR>

" Fix key control codes
map OC <Right>
map OD <Left>
map [C <S-Right>
map [D <S-Left>
"map [C <C-Right>
"map [D <C-Left>
map [31~ <S-F7>

" Spell check
map <F7> <ESC>:setlocal spell! spelllang=en_us<CR>

set pastetoggle=<F12>
set modeline

" " For i18n
" vmap <F2> "xd"="__("<CR>P"xp"=")"<CR>p
" vmap <F2><F2> "xd"="_e("<CR>P"xp"=")"<CR>p
" "nmap <F3> :.s/_[_e](\(['"]\).\{-}\1)/<?php &; ?>/g<CR> :nohlsearch<CR>
" vmap <F3> "xd"="<?php _e('"<CR>P"xp"="'); ?>"<CR>p
" 
" fu! LoadPHPDebugger()
"     so $HOME/.vim/plugin/debugger
"     echo "PHP Debugger loaded."
" endf

set dictionary-=/usr/share/dict/words dictionary+=/usr/share/dict/words

" For Python source
" autocmd BufWritePre *.py normal m`:%s/\s\+$//e ``
autocmd BufRead *.py set tabstop=2
autocmd BufRead *.py set shiftwidth=2
autocmd BufRead *.py set smarttab
autocmd BufRead *.py set expandtab
autocmd BufRead *.py set softtabstop=2
autocmd BufRead *.py set autoindent
autocmd BufRead *.py set smartindent cinwords=if,elif,else,for,while,try,except,finally,def,class
autocmd BufWritePre *.py normal m`:%s/\s\+$//e ``

fu! CheckGoogleGadgets()
	let gg=0
	silent! exec 'g/<Content type="html">/let gg=1'
	if gg==1
		runtime! syntax/GoogleGadgets.vim
		echo "Google Gadgets syntax loaded."
	endif
endf

autocmd BufRead *.xml call CheckGoogleGadgets()

" http://blog.sontek.net/2008/05/11/python-with-a-modular-ide-vim/
" Freely jump between your code and python class libraries
python << EOF
import os
import sys
import vim
for p in sys.path:
    if os.path.isdir(p):
        vim.command(r"set path+=%s" % (p.replace(" ", r"\ ")))
EOF

set tags+=$HOME/.vim/tags/python.ctags

" Code Completion
autocmd FileType python set omnifunc=pythoncomplete#Complete

" Syntax Checking
" http://vim.wikia.com/wiki/Python_-_check_syntax_and_run_script
autocmd BufRead *.py set makeprg=python\ -c\ \"import\ py_compile,sys;\ sys.stderr=sys.stdout;\ py_compile.compile(r'%')\"
autocmd BufRead *.py set efm=%C\ %.%#,%A\ \ File\ \"%f\"\\,\ line\ %l%.%#,%Z%[%^\ ]%\\@=%m
autocmd BufRead *.py nmap <F5> :!python %<CR>

python << EOL
import vim
def EvaluateCurrentRange():
	eval(compile('\n'.join(vim.current.range),'','exec'),globals())
EOL
map <C-h> :py EvaluateCurrentRange()<CR>

" Set shell title
" http://vim.wikia.com/wiki/Automatically_set_screen_title
let &titlestring = "vim:" . expand("%:t")
if &term == "screen"
  " ^[ is by pressing Ctrl+V ESC
  set t_ts=k
  set t_fs=\
endif
if &term == "screen" || &term == "xterm" || &term == "urxvt"
  set title
endif

" Append modeline after last line in buffer.
" Use substitute() (not printf()) to handle '%%s' modeline in LaTeX files.
" http://vim.wikia.com/wiki/Modeline_magic
function! AppendModeline()
  let save_cursor = getpos('.')
  let append = ' vim: set ts='.&tabstop.' sw='.&shiftwidth.' tw='.&textwidth.': '
  $put =substitute(&commentstring, '%s', append, '')
  call setpos('.', save_cursor)
endfunction
nnoremap <silent> <Leader>ml :call AppendModeline()<CR>


" Markdown syntax
" http://plasticboy.com/markdown-vim-mode/
augroup mkd

  autocmd BufRead *.mkd set tabstop=2
  autocmd BufRead *.mkd set shiftwidth=2
  autocmd BufRead *.mkd set smarttab
  autocmd BufRead *.mkd set expandtab
  autocmd BufRead *.mkd set softtabstop=2

  autocmd BufRead *.mkd set ai formatoptions=tcroqn2 comments=n:&gt;

  autocmd BufRead *.mkd map <F5> <ESC>:w<CR>:!gen-blog-markdown.sh "%"<CR>
  autocmd BufRead *.mkd imap <F5> <ESC>:w<CR>:!gen-blog-markdown.sh "%"<CR>

augroup END

" For Chrome Extension manifest.json
augroup json

  autocmd BufRead *.json set tabstop=2
  autocmd BufRead *.json set shiftwidth=2
  autocmd BufRead *.json set smarttab
  autocmd BufRead *.json set expandtab
  autocmd BufRead *.json set softtabstop=2
  autocmd BufRead *.json set ai
  autocmd BufRead *.json set syntax=javascript
  
augroup END

" vim: set sw=2 ts=2 et:
