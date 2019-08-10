
import line


line.plot.initialize(False)

c = line.cmd_handle.CMDHandler()
c.proc_file('test.txt')

line.plot.finalize(False)
