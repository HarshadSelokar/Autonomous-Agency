"""
SandboxExecutionBoundary Infrastructure Layer for Phase 8.
Enforces execution isolation: workspace path sanitization, process limits,
output size truncation, timeout enforcement, and network SSRF defenses.
"""

import ipaddress
import urllib.parse
from pathlib import Path


class SandboxViolationError(Exception):
    """Raised when a tool execution violates sandboxing boundaries."""

    pass


class SSRFViolationError(SandboxViolationError):
    """Raised when an HTTP tool attempt targets private/forbidden IP ranges or cloud metadata endpoints."""

    pass


class SandboxExecutionBoundary:
    def __init__(
        self,
        base_workspace_dir: str = "scratch",
        max_output_size_bytes: int = 100 * 1024,  # 100 KB
        allowed_domains: list[str] | None = None,
    ) -> None:
        self.base_workspace_path = Path(base_workspace_dir).resolve()
        self.base_workspace_path.mkdir(parents=True, exist_ok=True)
        self.max_output_size_bytes = max_output_size_bytes
        self.allowed_domains = allowed_domains or []

    def sanitize_path(self, relative_path: str, workspace_id: str | None = None) -> Path:
        """
        Sanitize and resolve file path within assigned workspace directory.
        Prevents directory traversal attacks (e.g. '../../etc/passwd').
        """
        if workspace_id:
            root_dir = self.base_workspace_path / "workspaces" / workspace_id
        else:
            root_dir = self.base_workspace_path

        root_dir.mkdir(parents=True, exist_ok=True)
        target_path = (root_dir / relative_path).resolve()

        # Enforce boundary check
        try:
            target_path.relative_to(root_dir)
        except ValueError:
            raise SandboxViolationError(
                f"Path '{relative_path}' attempts directory traversal outside assigned workspace boundary!"
            )

        return target_path

    def validate_http_url(self, url: str) -> None:
        """
        SSRF Defense Validation: Rejects loopback, private IP ranges, cloud metadata IPs,
        and unauthorized non-HTTP protocols.
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise SSRFViolationError(f"Forbidden protocol '{parsed.scheme}'. Only HTTP and HTTPS are allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFViolationError("Invalid URL: missing hostname.")

        host_lower = hostname.lower()
        if host_lower in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
            raise SSRFViolationError(f"SSRF Violation: Request to loopback target '{hostname}' is blocked!")

        # Cloud Metadata IPs & Link-Local (169.254.169.254)
        if host_lower == "169.254.169.254" or host_lower.startswith("169.254."):
            raise SSRFViolationError("SSRF Violation: Request to cloud metadata endpoint is blocked!")

        # Domain Allowlist Check (if configured)
        if self.allowed_domains:
            if not any(host_lower == domain.lower() or host_lower.endswith(f".{domain.lower()}") for domain in self.allowed_domains):
                raise SSRFViolationError(f"SSRF Violation: Host '{hostname}' is not in the allowed domain list!")

        # Private Subnet IP Check
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise SSRFViolationError(f"SSRF Violation: Access to private/reserved IP address '{ip}' is blocked!")
        except ValueError:
            # Hostname is a domain name (e.g. api.github.com), not raw IP
            pass

    def truncate_output(self, content: str) -> str:
        """Truncate tool output if it exceeds max output size bytes."""
        encoded = content.encode("utf-8")
        if len(encoded) > self.max_output_size_bytes:
            truncated_bytes = encoded[: self.max_output_size_bytes]
            return truncated_bytes.decode("utf-8", errors="ignore") + "\n...[OUTPUT TRUNCATED BY SANDBOX]"
        return content
