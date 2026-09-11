"""Default Llama runner: Llama 3.2 1B BF16."""
if __name__ == '__main__':
  import runpy
  runpy.run_module('examples.llama3_1b', run_name='__main__')
else:
  from examples.llama3_1b import *
