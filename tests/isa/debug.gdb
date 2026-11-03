# Run through tt-device-queue; see crash_investigation.md for the command.
set pagination off
set confirm off
set disable-randomization off
handle SIGSEGV stop print nopass
handle SIGBUS stop print nopass
handle SIGABRT stop print nopass
run
python
inferior = gdb.selected_inferior()
if inferior.pid:
    gdb.execute('thread apply all bt full')
    gdb.execute('info registers')
    gdb.execute('info proc mappings')
    gdb.execute('x/12i $pc')
    gdb.execute('generate-core-file /tmp/blackhole-isa-reproduced.core')
    gdb.execute('quit 139')
end
