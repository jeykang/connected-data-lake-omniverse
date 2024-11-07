# Connected Data Lake - NVIDIA Omniverse Extensions

## Getting Started

### Requirements

- busybox
- curl
- findutils
- [Just `cargo install just`](https://github.com/casey/just)
- [Rust (rustup)](https://rustup.rs/)

#### Ubuntu 24.04 or Above

```bash
# Install the dependencies
sudo apt-get update && sudo apt-get install -y \
  busybox \
  curl \
  findutils \
  just \
  rustup

# Install the latest stable cargo & rustc (>=1.82)
rustup default stable
```

### One-shot Command Line

```bash
just run editor.base
```

## LICENSE

Please check our [LICENSE file](/LICENSE).
