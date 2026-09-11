"""BF16 reference utility shared with the mixed-FP8 tools."""
if __name__ == '__main__':
  import runpy
  runpy.run_module('scripts.llama3_8b.download_weights', run_name='__main__')
