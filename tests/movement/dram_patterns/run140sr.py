import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cores140
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'syncrot.py')).read(), 'syncrot.py', 'exec'))
