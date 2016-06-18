let s:job_id = 0
let s:path = expand('<sfile>:p:h' ). "/python/ssvim.py"

function! s:handle_stdout(job_id, data, event)
    for cmd in a:data
        execute cmd
    endfor
endfunction

function! s:handle_yank()
    if s:job_id == 0
        call RunProcess(1337)
    endif

    call async#job#send(s:job_id, json_encode(v:event) . "\n")
endfunction

function! s:handle_buf_enter()
    if s:job_id == 0
        call RunProcess(1337)
    endif

    let l:data = {'cwd': getcwd(), 'filename': expand("<afile>")}
    call async#job#send(s:job_id, json_encode(l:data) . "\n")
endfunction

function! s:handle_vim_opened()
    if s:job_id == 0
        call RunProcess(1337)
    endif

    redir => l:buffers
    silent buffers
    redir END

    let l:data = {'cwd': getcwd(), 'buffers': l:buffers}
    call async#job#send(s:job_id, json_encode(l:data) . "\n")
endfunction

function! RunProcess(port)
    let l:opts = {'on_stdout': function('s:handle_stdout')}
    let s:job_id = async#job#start([g:python3_host_prog, s:path, a:port], l:opts)
endfunction

call RunProcess(1337)

autocmd TextYankPost * call s:handle_yank()
autocmd BufNew * call s:handle_buf_enter()
autocmd VimEnter * call s:handle_vim_opened()

" Force redraw for airline
autocmd BufNew * set mod!|redraws|set mod!
