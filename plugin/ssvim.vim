let s:job_id = 0
let s:path = expand('<sfile>:p:h' ). "/python/ssvim.py"


function! s:handle_stdout(job_id, data, event)
    " Seperate the stdin by our magic marker
    let l:commands = split(join(a:data[:-1], "\n"), "0b6f83ef")
    " The last command is concatenated with a "\n". We want to remove it.
    let l:commands[-1] = substitute(l:commands[-1], "\n$", "", "")

    for cmd in l:commands
        let l:command = split(cmd, " ")[0]
        let l:filename = split(cmd, " ")[1]

        if l:command == ":badd"
            let l:bufnr = bufnr(l:filename)
            if l:bufnr == -1 " Buffer doesn't exist
                execute cmd
            elseif getbufvar(l:bufnr, "&mod") == 0 " Buffer unmodified
                execute cmd
            endif
        else
            execute cmd
        endif

        if split(cmd, " ")[0] == ":badd"
            if getbufvar(1, "&mod") == 0
                if bufname(1) == ""
                    " The first 'scrach' buffer is unmodified and open.
                    " Close it.
                    silent! bd 1
                endif
            endif
        endif
    endfor
endfunction


function! s:handle_yank()
    call async#job#send(s:job_id, json_encode(v:event) . "\n")
endfunction


function! s:handle_buf_new()
    let l:data = {'cwd': getcwd(), 'new': expand("<afile>")}
    call async#job#send(s:job_id, json_encode(l:data) . "\n")
endfunction


function! s:handle_buf_delete()
    let l:data = {'cwd': getcwd(), 'delete': expand("<afile>")}
    call async#job#send(s:job_id, json_encode(l:data) . "\n")
endfunction


function! s:handle_vim_opened()
    redir => l:buffers
    silent buffers
    redir END

    let l:data = {'cwd': getcwd(), 'buffers': l:buffers}
    call async#job#send(s:job_id, json_encode(l:data) . "\n")
endfunction


function s:ssvim_disable()
    augroup SSVIMAutoCommands
        autocmd!
    augroup END
endfunction



function s:ssvim_decorator(func)
    if s:job_id == 0
        call s:ssvim_disable()
        return
    else
        call a:func()
    endif
endfunction


function! SSVIMActivate(port)
    augroup SSVIMAutoCommands
        autocmd!
        autocmd TextYankPost * call s:ssvim_decorator(function('s:handle_yank'))
        autocmd BufNew * call s:ssvim_decorator(function('s:handle_buf_new'))
        autocmd BufDelete * call s:ssvim_decorator(function('s:handle_buf_delete'))
        autocmd VimEnter * call s:ssvim_decorator(function('s:handle_vim_opened'))
    augroup END

    let l:opts = {'on_stdout': function('s:handle_stdout')}
    let s:job_id = async#job#start([g:python3_host_prog, s:path, a:port], l:opts)
    call s:handle_vim_opened()
endfunction


function! SSVIMStop()
    if s:job_id
        call s:ssvim_disable()
        call async#job#stop(s:job_id)
    endif
endfunction


" Force redraw for airline
autocmd BufNew * set mod!|redraws|set mod!
