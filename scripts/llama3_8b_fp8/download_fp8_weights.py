"""Download Neural Magic's calibrated Llama 3 8B Instruct FP8 checkpoint."""
import argparse
from huggingface_hub import snapshot_download
REPO = 'RedHatAI/Meta-Llama-3-8B-Instruct-FP8'
REVISION = 'c5c6b5700a4178ef1fdae2ae37827382b90eb400'
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--output', default='weights/llama3-8b-fp8')
  args = parser.parse_args()
  snapshot_download(REPO, revision=REVISION, local_dir=args.output,
                    allow_patterns=['*.json', '*.safetensors', '*.jinja', 'LICENSE*', 'README.md', 'USE_POLICY*'], max_workers=2)
