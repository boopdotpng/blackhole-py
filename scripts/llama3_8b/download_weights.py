"""Fetch the pinned, full BF16 Llama 3 8B Instruct checkpoint."""
import argparse
from huggingface_hub import snapshot_download

REPO = 'unsloth/llama-3-8b-Instruct'
REVISION = 'f3710969eb766fb49d4d1ed3aeabcb03390772bd'

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--output', default='weights/llama3-8b-bf16')
  args = parser.parse_args()
  snapshot_download(REPO, revision=REVISION, local_dir=args.output,
                    allow_patterns=['*.json', '*.safetensors', '*.jinja', 'LICENSE*', 'README.md', 'USE_POLICY*'],
                    max_workers=4)
