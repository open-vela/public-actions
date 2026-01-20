# OpenVela Public Actions

Reusable GitHub Actions and workflows for OpenVela projects.

## Available Workflows

### 1. Checkpatch Workflow
Automated code style checking and watermark detection for pull requests.

**Usage:**
```yaml
jobs:
  checkpatch:
    uses: YOUR_USERNAME/public-actions/.github/workflows/checkpatch.yml@dev
    secrets: inherit
```

**Features:**
- Code style validation (for nuttx/nuttx-apps)
- Watermark detection in images
- Chinese character detection in commits and source files
- Gerrit Change-ID validation

### 2. CLA Workflow
Contributor License Agreement verification.

**Usage:**
```yaml
jobs:
  cla:
    uses: YOUR_USERNAME/public-actions/.github/workflows/cla.yml@dev
    secrets: inherit
```

### 3. CI Workflow
Continuous Integration workflow that routes to appropriate CI based on target branch.

**Usage:**
```yaml
jobs:
  ci:
    uses: YOUR_USERNAME/public-actions/.github/workflows/ci.yml@dev
    secrets: inherit
```

**Features:**
- Routes to trunk CI for trunk branch PRs
- Routes to dev CI for dev branch PRs
- Supports rebase branch detection

### 4. Docs Workflow
Documentation and multi-repository PR dependency management.

**Usage:**
```yaml
jobs:
  docs:
    uses: YOUR_USERNAME/public-actions/.github/workflows/docs.yml@dev
    secrets: inherit
```

**Features:**
- Parses PR dependencies from description (`depends-on: [repo/pull/123]`)
- Fetches and cherry-picks dependent PRs
- Updates status on dependent PRs
- Manages multi-repo synchronization

### 5. Stale Workflow
Automatically closes stale issues and PRs.

**Usage:**
```yaml
jobs:
  stale:
    uses: YOUR_USERNAME/public-actions/.github/workflows/stale.yml@dev
```

**Configuration:**
- Issues: Marked stale after 30 days, closed after 7 more days
- PRs: Marked stale after 30 days, closed after 7 more days
- Runs daily at 1:30 AM UTC

## Watermark Detection

Automatically detects sensitive watermarks (Feishu/DingTalk) in images using geometric angle filtering.

📖 **[Complete Documentation](WATERMARK-DETECTION.md)**

**Quick Start:**
```bash
# Using Docker
docker run --rm -v "$(pwd):/workspace" \
  ghcr.io/YOUR_USERNAME/watermark-detector:latest image.jpg

# Using Python
python detect_watermark.py image.jpg
```

**Docker Image:** `ghcr.io/YOUR_USERNAME/watermark-detector:latest`

## Chinese Character Detection

Automatically detects Chinese characters in commit messages and source files to maintain code internationalization.

📖 **[Complete Documentation](CHINESE-DETECTION.md)**

**Quick Start:**
```bash
# Check commit messages
python check_commit_msg.py main..HEAD

# Check source files (with exclusions)
python check_source_files.py main..HEAD --exclude README.md .md docs/

# Using Docker
docker run --rm -v "$(pwd):/workspace" -w /workspace \
  ghcr.io/YOUR_USERNAME/chinese-detector:dev \
  python /usr/local/bin/check_commit_msg.py "main..HEAD"
```

**Features:**
- Detects Chinese characters in commit messages
- Scans modified source files for Chinese comments/strings
- Configurable exclusion rules (README, docs, etc.)
- Integrated into CI/CD pipeline

**Docker Image:** `ghcr.io/YOUR_USERNAME/chinese-detector:dev`

## Files

### Workflows
- `.github/workflows/checkpatch.yml` - Code style and watermark check
- `.github/workflows/cla.yml` - CLA verification
- `.github/workflows/ci.yml` - CI routing workflow
- `.github/workflows/ci-real.yml` - Actual CI implementation
- `.github/workflows/docs.yml` - Multi-repo PR dependency management
- `.github/workflows/stale.yml` - Stale issue/PR management
- `.github/workflows/build-watermark-docker.yml` - Watermark detection Docker image builder
- `.github/workflows/build-chinese-detection-docker.yml` - Chinese detection Docker image builder
- `.github/workflows/clang-format.yml` - Code formatting check
- `.github/workflows/docker_linux.yml` - Linux Docker build
- `.github/workflows/docker_linux_from_apache-nuttx.yml` - Apache NuttX Docker build

### Actions
- `.github/actions/watermark-check/` - Reusable watermark detection action

### Scripts
- `detect_watermark.py` - Watermark detection script
- `check_commit_msg.py` - Chinese character detection in commits
- `check_source_files.py` - Chinese character detection in source files
- `test-watermark.sh` - Test Python environment
- `test-docker.sh` - Test Docker image
- `test-chinese-detection.sh` - Test Chinese detection scripts

### Docker
- `Dockerfile.watermark` - Watermark detection image
- `Dockerfile.chinese-detection` - Chinese character detection image
- `.dockerignore` - Build optimization

### Documentation
- `WATERMARK-DETECTION.md` - Complete watermark detection guide
- `CHINESE-DETECTION.md` - Complete Chinese character detection guide
- `README-CLA.md` - CLA workflow documentation
- `CLA-CONFIG.md` - CLA configuration guide

## Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- Tests pass locally
- Documentation is updated

## License

See LICENSE file for details.
