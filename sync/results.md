
### 8b-fp8: 19.77 ms/token

| kernel | us/launch | streaming bound | excess | compute-only (`nodram`) | per-tile syncs off (`nodram+t0semfix+t1nosync`) |
|---|---:|---:|---:|---:|---:|
| qkv | 63.3 | 49.7 | +13.6 | 51.9 | 49.9 |
| o | 47.3 | 33.2 | +14.1 | 40.2 | 38.9 |
| gate | 248.3 | 232.1 | +16.2 | 187.2 | 178.2 |
| down | 144.3 | 116.0 | +28.3 | 97.3 | 92.2 |
| lm | 2074.9 | 2076.4 | -1.5 | 920.4 | 919.1 |
| attention | 40.0 | ~0 | +40.0 | | |
| attention_merge | 8.5 | ~0 | +8.5 | | |
| embedding | 5.2 | ~0 | +5.2 | | |
| argmax | 9.2 | ~0 | +9.2 | | |

Time not explained by streaming weights at 506 GB/s: 3.88 ms/token (20%).

### 8b-bf16: 33.37 ms/token

| kernel | us/launch | streaming bound | excess | compute-only (`nodram`) | per-tile syncs off (`nodram+t0semfix+t1nosync`) |
|---|---:|---:|---:|---:|---:|
| qkv | 113.0 | 99.5 | +13.5 | 61.0 | 60.9 |
| o | 80.7 | 66.3 | +14.4 | 45.5 | 45.5 |
| gate | 480.9 | 464.2 | +16.8 | 238.6 | 238.4 |
| down | 253.7 | 232.1 | +21.6 | 99.4 | 96.5 |
| lm | 2081.9 | 2076.4 | +5.5 | 996.9 | 996.3 |
| attention | 39.6 | ~0 | +39.6 | | |
| attention_merge | 8.5 | ~0 | +8.5 | | |
| embedding | 5.3 | ~0 | +5.3 | | |
| argmax | 8.9 | ~0 | +8.9 | | |

Time not explained by streaming weights at 506 GB/s: 3.68 ms/token (11%).

### 1b: 6.28 ms/token

| kernel | us/launch | streaming bound | excess | compute-only (`nodram`) | per-tile syncs off (`nodram+t0semfix+t1nosync`) |
|---|---:|---:|---:|---:|---:|
| qkv | 38.1 | 24.9 | +13.3 | 29.3 | – |
| o | 29.2 | 16.6 | +12.6 | 23.6 | – |
| gate | 146.5 | 132.6 | +13.9 | 112.6 | – |
| down | 77.9 | 66.3 | +11.6 | 36.0 | – |
| lm | 1048.2 | 1038.2 | +10.0 | 783.3 | – |
| attention | 27.2 | ~0 | +27.2 | | |
| attention_merge | 5.7 | ~0 | +5.7 | | |
| embedding | 4.0 | ~0 | +4.0 | | |
| argmax | 8.9 | ~0 | +8.9 | | |

Time not explained by streaming weights at 506 GB/s: 1.37 ms/token (22%).

### All runs

| model | variant | ms/token | tokens match | gate | down | qkv | o | lm |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1b | `base` | 6.28 | 24/24 | 146.5 | 77.9 | 38.1 | 29.2 | 1048.2 |
| 1b | `nodram` | 4.57 | 0/24 | 112.6 | 36.0 | 29.3 | 23.6 | 783.3 |
| 1b | `nodram+t0semfix` | 4.56 | 0/24 | 112.5 | 36.0 | 29.3 | 23.7 | 783.2 |
| 1b | `t0semfix` | 6.27 | 24/24 | 146.6 | 77.9 | 38.1 | 29.2 | 1048.4 |
| 1b | `t0semfix+t1nosync` | 6.27 | 24/24 | 146.5 | 77.8 | 38.1 | 29.2 | 1048.3 |
| 1b | `t1nosync` | 6.27 | 24/24 | 146.5 | 77.9 | 38.2 | 29.2 | 1048.2 |
| 8b-bf16 | `base` | 33.37 | 24/24 | 480.9 | 253.7 | 113.0 | 80.7 | 2081.9 |
| 8b-bf16 | `nodram` | 16.81 | 0/24 | 238.6 | 99.4 | 61.0 | 45.5 | 996.9 |
| 8b-bf16 | `nodram+t0semfix` | 16.81 | 0/24 | 238.8 | 99.3 | 61.0 | 45.5 | 997.7 |
| 8b-bf16 | `nodram+t0semfix+t1nosync` | 16.70 | 0/24 | 238.4 | 96.5 | 60.9 | 45.5 | 996.3 |
| 8b-bf16 | `t0semfix` | 33.38 | 24/24 | 481.0 | 253.6 | 113.0 | 80.7 | 2082.3 |
| 8b-bf16 | `t0semfix+t1nosync` | 33.36 | 24/24 | 480.8 | 253.4 | 113.0 | 80.7 | 2081.8 |
| 8b-fp8 | `base` | 19.77 | 24/24 | 248.3 | 144.3 | 63.3 | 47.3 | 2074.9 |
| 8b-fp8 | `nobarrier` | 24.23 | 0/24 | 335.7 | 167.0 | 75.9 | 55.0 | 2355.8 |
| 8b-fp8 | `nodram` | 14.57 | 0/24 | 187.2 | 97.3 | 51.9 | 40.2 | 920.4 |
| 8b-fp8 | `nodram+nobarrier` | 14.63 | 0/24 | 187.9 | 100.3 | 52.8 | 41.1 | 804.2 |
| 8b-fp8 | `nodram+t0nodrain` | 14.31 | 0/24 | 183.1 | 94.8 | 51.0 | 39.6 | 920.2 |
| 8b-fp8 | `nodram+t0semfix` | 14.31 | 0/24 | 183.1 | 94.8 | 51.0 | 39.6 | 920.4 |
| 8b-fp8 | `nodram+t0semfix+t1nosync` | 14.01 | 0/24 | 178.2 | 92.2 | 49.9 | 38.9 | 919.1 |
| 8b-fp8 | `nodram+t1halfsfpu` | 14.23 | 0/24 | 180.1 | 96.3 | 50.3 | 39.2 | 919.8 |
| 8b-fp8 | `nodram+t1nosfpu` | 13.92 | 0/24 | 174.6 | 95.2 | 48.7 | 38.0 | 919.1 |
| 8b-fp8 | `nodram+t1nosync` | 14.53 | 0/24 | 186.3 | 97.2 | 51.7 | 40.1 | 920.4 |
| 8b-fp8 | `t0nodrain` | 19.77 | 0/24 | 248.2 | 144.2 | 63.3 | 47.3 | 2075.0 |
| 8b-fp8 | `t0semfix` | 19.77 | 24/24 | 248.2 | 144.2 | 63.3 | 47.3 | 2075.0 |
| 8b-fp8 | `t0semfix+t1nosync` | 19.76 | 24/24 | 248.2 | 144.1 | 63.3 | 47.2 | 2074.6 |
| 8b-fp8 | `t1nosync` | 19.77 | 24/24 | 248.2 | 144.4 | 63.3 | 47.3 | 2074.0 |
