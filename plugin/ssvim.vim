let s:job_id = 0
let s:path = expand('<sfile>:p:h' ). "/python/ssvim.py"

function! s:handle_stdout(job_id, data, event)
    echo a:data[0]
    execute a:data[0]
endfunction

function! s:handle_yank()
    if s:job_id == 0
        call RunProcess(1337)
    endif

    call async#job#send(s:job_id, json_encode(v:event) . "\n")
endfunction

function! RunProcess(port)
    let l:opts = {'on_stdout': function('s:handle_stdout')}
    let s:job_id = async#job#start([g:python3_host_prog, s:path, a:port], l:opts)
endfunction

call RunProcess(1337)

autocmd TextYankPost * call s:handle_yank()
