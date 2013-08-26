
" ntk
"
" A vim plugin for 93k
"
" A vim plugin for editing files for HP Agilent Verigy Advantest 93000
" Automated Test Equipment.
"
" Fixes up EQSP when you save files so they can be loaded under smarTest.
"
" [F8] fixes up and sends the current buffer directly to smarTest resurecting
" a classic feature from way back.
"
" Name your files with .ntk extension, for example: timing.ntk, levels.ntk
"
" Requires vim compiled with +python
"
" Tested with smarTest 6.5.4 under RHEL 5 and smarTest 5.4.2 under RHEL 3
"
" Get the latest version on github.
"
" Thanks to Dejan Noveski for his article How to Write vim Plugins with Python
" http://brainacle.com/how-to-write-vim-plugins-with-python.html
"
" TODO: Fix DVVC and other binary commands too
" TODO: Find send_to_mcd.py and myhpt relative to ntk.vim

" Only do these settings when not done yet for this buffer
if exists("b:did_ftplugin")
  finish
endif

" Don't do other file type settings for this buffer
let b:did_ftplugin = 1

" echo "hello ntk"

" TODO: Detect 93k file based on hp93000,config,0.1 in first line and warn that
" this wipes out all settings.

" Get the real path of this script. Does not work inside a function so here it is at
" top scope.

let s:this_script_path = resolve(expand("<sfile>"))
let s:this_script_directory = substitute(s:this_script_path, "[^/]*$", "", "")

function! Echo_script_path()
python << EOF

import vim

print vim.eval("s:this_script_directory")

EOF

endfunction

function! s:ntk_open()
"     echo ".ntk file detected"
    map <F8> :call NtkSendToMCD()<CR>
endfunction

" TODO: remove this after files are properly detected
map <F8> :call NtkSendToMCD()<CR>

autocmd BufNewFile,BufRead *.ntk call s:ntk_open()
" Write automatically triggers fix EQSP
autocmd BufWritePre *.ntk call NtkFixEQSP()



if !has('python')
    echo "Error: ntkmode requires vim compiled with +python. Did you type 'vi' instead of 'vim' by mistake?"
    finish
endif

function! NtkSendToMCD()
" write automatically triggers save
    write
" TODO: Handle missing send_to_mcd.py or unbuilt myhpt
    echo(system(s:this_script_directory . "myhpt/send_to_mcd.py ".bufname("%")))
endfunction

function! AboutNtkVim()
    echo "ntk.vim Copyright (c) 2013 Michael Fox and licensed under The MIT License "
endfunction

function! OpenWebPage(url)
    if filereadable("/usr/bin/firefox")
        silent! execute "!/usr/bin/firefox \"" . a:url . "\""
    elseif filereadable("/usr/bin/mozilla")
        silent! execute "!/usr/bin/mozilla \"" . a:url . "\""
    elseif filereadable("/usr/bin/xdg-open")
        silent! execute "!/usr/bin/xdg-open \"" . a:url . "\""
    else
        echo "ERROR: No browser in /usr/bin/firefox or /usr/bin/mozilla"
    endif
endfunction

" Menu for gvim
:menu 100.1 h&p93k.&Send\ File\ To\ hp93k<Tab>F8 :call NtkSendToMCD()<CR>
:menu 100.100 h&p93k.-sep1- :
" TODO: popup an about
:menu 100.110 h&p93k.About\ ntk\.vim :call AboutNtkVim()<CR>
" TODO: open www.antikc.com in web browser
:menu 100.120 h&p93k.www\.github\.com/gitfoxi/ntk\.vim :call OpenWebPage("https://www.github.com/gitfoxi/ntk-vim")<CR>
:menu 100.130 h&p93k.www\.aNTiKc\.com :call OpenWebPage("http://www.antikc.com")<CR>

function! NtkFixEQSP()

python << EOF
import vim
import re

in_eqsp = False
find_eqsp = re.compile('^(EQSP\s+[^,\s]+\s*,\s*[^,\s]+\s*,\s*#9)(\d{9})(.*)',re.DOTALL)

# TODO: If download errors then jump back to the line the error occurs on
# TODO: Split into several buffers, one for each EQSP section, fixing it up on write or download
# TODO: Transform vector files for editing (will require VECC reverse engineering)
# TODO: Transform testflows into python and back
# TODO: Menus in gvim
# Use autocommands (autocmd) to hook reading and writing

def in_quote(s):
    return s.count('"') % 2 == 1

            
for i, l in enumerate(vim.current.buffer):
    if not in_eqsp:
        m = find_eqsp.match(l)
        if m:
            (pre, tnbytes, post) = m.groups()
            in_eqsp = True
            eqsp_count = len(post) + 1
            eqsp_line = i
    else:  # in_eqsp
        at_idx = l.find('@')
        if(at_idx != -1):
            is_comment = l[0:at_idx].count('#') != 0
            is_quote = in_quote(l[0:at_idx])
        if(at_idx != -1 and not is_comment and not is_quote):
            in_eqsp = False
            eqsp_count += at_idx + 1
            vim.current.buffer[eqsp_line] = ''.join([
                pre,
                '%09d' % (eqsp_count),
                post])
        else:
            eqsp_count += len(l) + 1

if in_eqsp:
    print "Error: File ended after 'EQSP' but before '@'"


EOF

endfunction
