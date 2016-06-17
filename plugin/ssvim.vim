let g:job_id = 0

function! HandleStdout(job_id, data, event)
    if g:job_id == 0
        call RunProcess(1337)
    endif

    execute a:data[0]
endfunction

function! HandleYank()
    if g:job_id == 0
        call RunProcess(1337)
    endif

    call JobSend(g:job_id, json_encode(v:event) . "\n")
endfunction

function! RunProcess(port)
    let l:opts = {'stdout': function('HandleStdout')}
    let l:path = expand("%:p:r") . "python/ssvim.py"
    let g:job_id = JobStart([g:python3_host_prog, l:path, a:port], l:opts)
endfunction


autocmd TextYankPost * call HandleYank()
