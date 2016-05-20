# A pseudo terminal for Yocto-Serial

This is a very basic terminal for a Yocto-Serial (or a Yocto-RS232). By Default the programm will use the first
Yocto-Serial connected by USB, but you can use a remote Yocto-Serial with the option "-r". If multiples Yocto-Serial
are connected you can use the "-s" option to select the module to use. To terminate the program you need to send
two consecutive Ctrl-C.

See more detail on: http://www.yoctopuce.com/EN/article/a-pseudo-terminal-for-yocto-serial