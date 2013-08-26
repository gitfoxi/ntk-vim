
# ntk.vim

Edit hp93k configuration files such as timing and levels in Vim. Press `F8` to
send changes to the tester.

## Install

Choose a place to keep *ntk.vim* where it will be convenient to go back and
pull in new updates. It's not recommended to put it directly under your
`.vim/plugins` directory, but instead put it in a project folder and symlink.

    mkdir -p ~/src
    cd ~/src
    git clone https://github.com/gitfoxi/ntk-vim.git
    mkdir -p ~/.vim/plugins
    ln -s ~/src/ntk.vim/ntk.vim ~/.vim/plugins/

## Update

When a new version is available:

    cd ~/src/ntk.vim
    git pull

## Usage

    vim timing/mydevice.tim

Make your edits then press [F8] to download.

## GUI

If you run under gvim, you will get an `hp93k` menu of available commands.

    gvim levels/mydevice.lev

![Menu Screenshot](https://raw.github.com/gitfoxi/ntk-vim/master/images/menu_screenshot.png)

## Hacking

Under `ntk.vim/myhpt` you'll find two useful programs:

### myhpt

Sends any firmware-based file to the tester. Smart enough to not send
`hp93000,config,0.1` type lines but not much smarter than that. Usage:

    myhpt configuration/mydevice.conf

or

    cat configuration/mydevice.conf | myhpt

The latter is convenient if you want to start using `myhpt` under another
program for your own evil purposes.

### send_to_mcd.py

Wraps *myhpt* and adds a little smarts. Detects the file type using the
`hp93000,XXX,0.1` line and sends extra firmware commands to make the loading go
smoothly. You can change it's behavior by editing files like:

    - config.fw.pre     -- Firmware commands to send **before** sending a config file
    - config.fw.post    -- Firmware commands to send **after** sending a config file

Extra smarts lets you use this to load a Pattern Master File:

    send_to_mcd.py vectors/mydevice.pmf

## If you Have a Problem

I'm developing this with **hp93k smarTest 6.5.4** under **RHEL5u6** on
**PinScale** but do aim to support other smarTest versions in the **4.x** to
**7.x** range and platforms like **C400**, **P600** and **SmartScale** . One
problem that might arise with other versions of smarTest and other testers is
that they might require different magic firmware incantations before and after
sending a firmware file.

You should know about `hpt` and `diag 2`. If you want to see what firmware
commands should go before loading a configuration file, start logging firmware
commands:

    /opt/hp93000/soc/pws/bin/hpt
    *task:* diag 2

`diag 2` starts firmware logging. Then load your configuration file. Then in at
the `hpt` *task:* prompt:

    *task:* diag -2

`diag -2` stops logging. Now open up `/var/opt/hp93000/soc/MCDLog` and do some
research!

## Check Vim Python Support

In order to use *ntk.vim* you need Vim compiled with Python support. The
default Vim on RHEL3u7 and RHEL5u7 which is the normal platform for the hp93k
has this. You can check with:

    vim --version | grep +python -c

If all is well it will say:

    1

If it says:

    0

Then you have a problem. Remember to use `vim` and not `vi` because `vi` starts
a retarded version of Vim.

## License

The MIT License (MIT)

Copyright (c) 2013 Michael Fox

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

