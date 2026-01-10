"""
Node Provider - Automatic Node.js runtime provisioning for dashboards.

Provides frictionless Node.js access with this priority:
1. System Node >= 20.19 (if available)
2. Workspace-local bundled Node (if installed)
3. Auto-install workspace-local Node >= 22 LTS

No admin privileges required. Safe on corporate machines.
"""

import hashlib
import os
import platform
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Literal


class NodeProvider:
    """
    Manages Node.js runtime detection and provisioning.

    Provides frictionless access to Node.js for dashboard generation
    by automatically installing a workspace-local Node runtime if needed.
    """

    MIN_NODE_VERSION = (20, 19, 0)
    RECOMMENDED_NODE_VERSION = "22.13.0"  # Latest LTS as of 2025-01

    # Official Node.js distribution URLs
    NODE_DIST_BASE = "https://nodejs.org/dist"

    # Platform-specific download info
    PLATFORM_INFO = {
        "darwin-x64": {
            "filename": "node-v{version}-darwin-x64.tar.gz",
            "extract_dir": "node-v{version}-darwin-x64",
            "is_archive": True,
        },
        "darwin-arm64": {
            "filename": "node-v{version}-darwin-arm64.tar.gz",
            "extract_dir": "node-v{version}-darwin-arm64",
            "is_archive": True,
        },
        "win32-x64": {
            "filename": "node-v{version}-win-x64.zip",
            "extract_dir": "node-v{version}-win-x64",
            "is_archive": True,
        },
        "linux-x64": {
            "filename": "node-v{version}-linux-x64.tar.gz",
            "extract_dir": "node-v{version}-linux-x64",
            "is_archive": True,
        },
    }

    def __init__(self, project_root: Path):
        """
        Initialize Node Provider.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.tools_dir = self.project_root / ".kie" / "tools"
        self.node_dir = self.tools_dir / "node"

    def get_platform_key(self) -> str | None:
        """
        Get platform key for Node downloads.

        Returns:
            Platform key (e.g., 'darwin-x64', 'win32-x64') or None if unsupported
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize machine architecture
        if machine in ["x86_64", "amd64"]:
            machine = "x64"
        elif machine in ["arm64", "aarch64"]:
            machine = "arm64"
        else:
            return None

        # Map to platform key
        if system == "darwin":
            return f"darwin-{machine}"
        elif system == "windows":
            return "win32-x64"  # Only x64 Windows supported
        elif system == "linux":
            return f"linux-{machine}"
        else:
            return None

    def detect_system_node(self) -> tuple[bool, str | None, str]:
        """
        Detect system Node.js installation.

        Returns:
            Tuple of (is_compatible, version_string, message)
        """
        # Allow test override
        if "TEST_NODE_VERSION" in os.environ:
            version_str = os.environ["TEST_NODE_VERSION"]
            try:
                version_tuple = self._parse_version(version_str)
                is_ok = version_tuple >= self.MIN_NODE_VERSION
                return (is_ok, version_str, f"System Node {version_str}")
            except Exception:
                return (False, version_str, f"Invalid Node version: {version_str}")

        # Try to detect system Node
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version_str = result.stdout.strip().lstrip("v")
                try:
                    version_tuple = self._parse_version(version_str)
                    is_ok = version_tuple >= self.MIN_NODE_VERSION
                    if is_ok:
                        return (True, version_str, f"System Node {version_str} (compatible)")
                    else:
                        return (False, version_str, f"System Node {version_str} is too old (minimum: 20.19)")
                except Exception:
                    return (False, version_str, f"Could not parse Node version: {version_str}")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return (False, None, "System Node not found")

    def detect_bundled_node(self) -> tuple[bool, str | None, Path | None]:
        """
        Detect workspace-local bundled Node.

        Returns:
            Tuple of (exists, version_string, node_bin_path)
        """
        platform_key = self.get_platform_key()
        if not platform_key:
            return (False, None, None)

        platform_dir = self.node_dir / platform_key

        # Check for node executable
        if platform.system().lower() == "windows":
            node_bin = platform_dir / "bin" / "node.exe"
        else:
            node_bin = platform_dir / "bin" / "node"

        if not node_bin.exists():
            return (False, None, None)

        # Verify it works and get version
        try:
            result = subprocess.run(
                [str(node_bin), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version_str = result.stdout.strip().lstrip("v")
                return (True, version_str, node_bin)
        except Exception:
            pass

        return (False, None, None)

    def install_bundled_node(self, version: str | None = None) -> tuple[bool, str, Path | None]:
        """
        Install workspace-local Node.js runtime.

        Args:
            version: Node version to install (default: RECOMMENDED_NODE_VERSION)

        Returns:
            Tuple of (success, message, node_bin_path)
        """
        version = version or self.RECOMMENDED_NODE_VERSION

        platform_key = self.get_platform_key()
        if not platform_key:
            return (False, f"Unsupported platform: {platform.system()} {platform.machine()}", None)

        if platform_key not in self.PLATFORM_INFO:
            return (False, f"No Node distribution available for {platform_key}", None)

        platform_info = self.PLATFORM_INFO[platform_key]
        filename = platform_info["filename"].format(version=version)
        extract_dir = platform_info["extract_dir"].format(version=version)

        download_url = f"{self.NODE_DIST_BASE}/v{version}/{filename}"
        platform_dir = self.node_dir / platform_key

        # Create directories
        platform_dir.mkdir(parents=True, exist_ok=True)

        # Download file
        download_path = platform_dir / filename

        print(f"📦 Downloading Node.js {version} for {platform_key}...")
        print(f"   URL: {download_url}")

        try:
            import urllib.request

            # Download with progress indication
            def _progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    if percent % 10 == 0 and block_num > 0:
                        print(f"   {percent}% downloaded...")

            urllib.request.urlretrieve(download_url, download_path, _progress)
            print(f"   ✓ Downloaded {download_path.name}")

        except Exception as e:
            return (False, f"Download failed: {e}", None)

        # Extract archive
        print(f"📦 Extracting Node.js runtime...")

        try:
            if filename.endswith(".tar.gz"):
                with tarfile.open(download_path, "r:gz") as tar:
                    tar.extractall(platform_dir)
            elif filename.endswith(".zip"):
                with zipfile.ZipFile(download_path, "r") as zip_file:
                    zip_file.extractall(platform_dir)
            else:
                return (False, f"Unsupported archive format: {filename}", None)

            print(f"   ✓ Extracted to {platform_dir}")

        except Exception as e:
            return (False, f"Extraction failed: {e}", None)

        # Move extracted contents to bin/
        extracted_path = platform_dir / extract_dir
        bin_target = platform_dir / "bin"

        if extracted_path.exists():
            # Move bin directory from extracted archive
            extracted_bin = extracted_path / "bin"
            if extracted_bin.exists():
                if bin_target.exists():
                    shutil.rmtree(bin_target)
                shutil.move(str(extracted_bin), str(bin_target))

            # Clean up extracted directory
            shutil.rmtree(extracted_path)

        # Clean up download
        download_path.unlink()

        # Verify installation
        if platform.system().lower() == "windows":
            node_bin = bin_target / "node.exe"
        else:
            node_bin = bin_target / "node"

        if not node_bin.exists():
            return (False, f"Node binary not found after extraction: {node_bin}", None)

        # Make executable on Unix
        if platform.system().lower() != "windows":
            node_bin.chmod(0o755)

        # Verify it works
        try:
            result = subprocess.run(
                [str(node_bin), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                installed_version = result.stdout.strip().lstrip("v")
                print(f"   ✓ Node.js {installed_version} installed successfully")
                return (True, f"Installed Node {installed_version}", node_bin)
            else:
                return (False, f"Node verification failed: {result.stderr}", None)
        except Exception as e:
            return (False, f"Node verification failed: {e}", None)

    def get_node_bin(self) -> tuple[Literal["system", "bundled", "none"], Path | None, str]:
        """
        Get Node.js binary path with automatic provisioning.

        Priority:
        1. System Node >= 20.19
        2. Bundled workspace-local Node
        3. Auto-install bundled Node

        Returns:
            Tuple of (source, node_bin_path, message)
            source: 'system' | 'bundled' | 'none'
        """
        # Try system Node first
        system_ok, system_version, system_msg = self.detect_system_node()
        if system_ok:
            return ("system", Path("node"), system_msg)

        # Try bundled Node
        bundled_exists, bundled_version, bundled_bin = self.detect_bundled_node()
        if bundled_exists and bundled_bin:
            return ("bundled", bundled_bin, f"Bundled Node {bundled_version}")

        # Auto-install bundled Node
        print("🔧 Installing dashboard runtime (Node.js) locally for this workspace...")

        success, install_msg, node_bin = self.install_bundled_node()

        if success and node_bin:
            print("✅ Installed. Continuing build...")
            return ("bundled", node_bin, install_msg)
        else:
            return ("none", None, f"Auto-install failed: {install_msg}")

    def _parse_version(self, version_str: str) -> tuple[int, int, int]:
        """
        Parse version string to tuple.

        Args:
            version_str: Version string like "20.10.0", "20.10", or "20"

        Returns:
            Version tuple like (20, 10, 0)
        """
        parts = version_str.split(".")

        major = int(parts[0]) if len(parts) >= 1 else 0
        minor = int(parts[1]) if len(parts) >= 2 else 0
        patch = int(parts[2]) if len(parts) >= 3 else 0

        return (major, minor, patch)


def get_node_bin(project_root: Path) -> tuple[Literal["system", "bundled", "none"], Path | None, str]:
    """
    Get Node.js binary with automatic provisioning.

    Convenience function that creates NodeProvider and calls get_node_bin().

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (source, node_bin_path, message)
    """
    provider = NodeProvider(project_root)
    return provider.get_node_bin()
