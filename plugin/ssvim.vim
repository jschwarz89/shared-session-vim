function! HandleStdout(job_id, data, event)
endfunction


function! RunProcess()
    let l:opts = {'stdout': function('HandleStdout')}
    let l:job_id = JobStart(['python', 'python/ssvim.py'], l:opts)
endfunction

call RunProcess()
