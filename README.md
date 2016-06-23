shared-session-vim
==================

Shared Session Vim (or ssvim) is used to synchronize more than one by making
them use the same registers, open the same files, etc...

Basically, whenever you open a new buffered or yank data into some register, it
will be shared across Vim instances. Awesome! :>


## Demo

![ssvim demo](https://github.com/jschwarz89/demos/blob/master/ssvim.gif)


## Requirements:

Python3 is required (the python processes depend on "selectors" which was
introduced in Python 3.4. Also, either Neovim or Vim 7.4 running patch 1274 is
required.


## Installation

This plugin was written in Neovim with Vim in mind. Vim 7.4.1274 added its own
version of async IO, with different API than Neovim's. For this reason,
this plugin uses prabirshrestha/async.vim in order to make sure that the plugin
works for both Vim and Neovim.

Installation is a breeze: with your favorite bundler, add the following to your
vimrc:

For dein.vim:

```viml
call dein#add('prabirshrestha/async.vim')
call dein#add('jschwarz89/shared-session-vim')
```

For Vundle:

```viml
Bundle 'prabirshrestha/async.vim'
Bundle 'jschwarz89/shared-session-vim'
```

And so on...

**Note**: most bundlers accept the "user/repo" syntax as a bundle name. Just
yank and paste as required :)


## Usage

Please spend a minute to read the following - it will make your life easier:

0. "Shared Sessions" are basically 1 or more Vim/Neovim which have run the
   "SSVIMActivate" function with some shared port. For example, having 2 Vim
   instances run SSVIMActivate(1337) will connect them together to one session.
   Adding a new SSVIMActivate(1338) will create *another* shared session which
   is not shared with the one using port 1337.
1. As mentioned, each vim instance you want to join in some session need to run
   the following function:

   ```viml
   :call SSVIMActivate(<port>)
   ```

2. That's it. From now on, opening a buffer or yanking some data to one of the
   registers will propegate this data to the other Vims which are connected to
   the same port.
3. To detach a Vim from a session, run:

   ```viml
   :call SSVIMStop()
   ```

Note that closing a Vim process also closes the ssvim under it, and closing all
the Vim processes of some session will cause the leader to shut down, thus
closing the shared session completely.


## Architecture

The architecture is a bit more complicated. Basically, each Vim/Neovim that
joins a session spawns a python process, 'ssvim.py', which is ran using Vim's
or NeoVim's Async IO features. Whenever some Vim session with an attached ssvim
process does something of interest (read: yanks/opens a nonhidden buffer), that
information is sent to the ssvim.py process.

In addition, whenever an ssvim.py spawns he also tries to spawn another
process, 'leader.py'. The leader process is the one that binds the specified
port number, accepts TCP connections from the 'ssvim.py' processes (one for
each Vim/Neovim) and distributes :badd and :let commands as needed to propegate
information to all the other clients. Since only one process can bind some port
at a time, only one leader per shared session is possible. Also, if and when a
leader crashes, the ssvim.py processes spawn new leaders, and the first one to
bind the port is elected. Distributed algorithms for the poor, anyone? :)

So basically:

```

       --------------                    --------------
       |            |                    |            |
       | Vim/Neovim |      . . . .       | Vim/Neovim |
       |            |                    |            |
       --------------                    --------------
             |                                 |
             |                                 |
             |                                 |
             |                                 |
            \ /                               \ /
       --------------                    --------------
       |            |                    |            |
       |  ssvim.py  |      . . . .       |  ssvim.py  |
       |            |                    |            |
       --------------                    --------------
             |                                 |
             |                                 |
             |                                 |
             |         ---------------         |
             |         |             |         |
             \-------->|  leader.py  |<--------/
                       |             |
                       ---------------
```
