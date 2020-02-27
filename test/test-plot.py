import sys
sys.path.append('..')
import numpy as np

import line

line.plot([1,2,3], [4,5,6], xlabel='t', ylabel='xy_nodesc')
line.plot([1,2,3], [4.1,5.1,6.1], 'mx', xlabel='t', ylabel='xy_desc')
l1 = line.plot([1,2,3], 'gs', xlabel='123', ylabel='xy_single_nodesc')
l2 = line.plot([1.2,2.2,3.2], xlabel='t', ylabel='xy_single_desc')

line.fill(l1, l2, color='green')
line.fill(l1, 0.5, color='violet')
line.fill(l2, color='grey', alpha=0.1)

line.show()

line.clear()
line.bar([1,2,3], [2,3,4], ylabel='bar', width=0.8)
line.bar([1,2,3], ylabel='bar2', width=0.8)
line.show()
line.clear()

line.hist(np.random.rand(100), label='hist', norm='count')

line.show()
