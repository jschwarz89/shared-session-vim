let g:job_id = 0

function! s:handle_stdout(job_id, data, event)
    echo a:data[0]
    execute a:data[0]
endfunction

function! s:handle_yank()
    if g:job_id == 0
        call RunProcess(1337)
    endif

    call async#job#send(g:job_id, json_encode(v:event) . "\n")
endfunction

function! RunProcess(port)
    let l:opts = {'on_stdout': function('s:handle_stdout')}
    let l:path = expand("%:p:r") . "python/ssvim.py"
    let g:job_id = async#job#start([g:python3_host_prog, l:path, a:port], l:opts)
endfunction

call RunProcess(1337)

autocmd TextYankPost * call s:handle_yank()
