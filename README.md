# Connected Data Lake - NVIDIA Omniverse Extensions

## Getting Started

### Requirements

- bash
- busybox
- curl
- findutils
- [Just `cargo install just`](https://github.com/casey/just)
- [Rust (rustup)](https://rustup.rs/)

#### Ubuntu 24.04 or Above

```bash
# Install the dependencies
sudo apt-get update && sudo apt-get install -y \
  bash \
  busybox \
  curl \
  findutils \
  just \
  rustup

# Install the latest nightly cargo & rustc (>=1.84)
rustup default nightly
```

#### Windows 11 or Above

```bash
# Install the dependencies
winget install -e --id Git.Git  # git (bash, curl, findutils)
winget install -e --id frippery.busybox-w32  # busybox
winget install -e --id Casey.Just  # just
winget install -e --id Rustlang.Rustup  # rustup

# Install the latest nightly cargo & rustc (>=1.84)
rustup default nightly
```

### Download nuScenes Dataset by manual

The dataset will be automatically downloaded when started.
If you preper to download **ahead**, please follow this guide.

On your bash shell, type below:

```bash
# Install the dependencies
./app/python/python -m pip install \
  'numpy<2' \
  nuscenes-devkit \
  open3d \
  requests \
  usd-core

# Download the dataset
./exts/nuscenes_viz/nuscenes_viz/utils/download_datasets.py --samples

# If you preper to download all, then type below:
./exts/nuscenes_viz/nuscenes_viz/utils/download_datasets.py --samples --sweeps
```

### One-shot Command Line

On your bash shell, type below:

```bash
just run editor.base

# or, just type "just"!
```

## LICENSE

Please check our [LICENSE file](/LICENSE).
