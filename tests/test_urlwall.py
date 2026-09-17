"""Tests for urlwall core logic."""

import os
import sys
import tempfile
import unittest

# Ensure we can import urlwall from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import urlwall
from urlwall import config


class TestGetCanonicalHost(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(
            urlwall.getCanonicalHost("https://example.com/path"), "example.com"
        )

    def test_www(self):
        self.assertEqual(
            urlwall.getCanonicalHost("https://www.example.com"), "example.com"
        )

    def test_trailing_dot(self):
        self.assertEqual(urlwall.getCanonicalHost("example.com."), "example.com")

    def test_lowercase(self):
        self.assertEqual(urlwall.getCanonicalHost("HTTPS://EXAMPLE.COM"), "example.com")

    def test_full_url(self):
        result = urlwall.getCanonicalHost("https://www.example.com:8080/path?q=1")
        self.assertEqual(result, "example.com")


class TestNiceHost(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(urlwall.niceHost("https://example.com"), "example.com")

    def test_safelinks(self):
        self.assertEqual(
            urlwall.niceHost("https://outlook.com/redirect?url=xxx"), "outlook.com"
        )

    def test_safelinks_protection(self):
        self.assertEqual(
            urlwall.niceHost("https://example.safelinks.protection.outlook.com"),
            "safelinks.outlook.com",
        )


class TestIsWebURL(unittest.TestCase):
    def test_http(self):
        self.assertTrue(urlwall.isWebURL("http://example.com"))

    def test_https(self):
        self.assertTrue(urlwall.isWebURL("https://example.com"))

    def test_ftp(self):
        self.assertTrue(urlwall.isWebURL("ftp://files.example.com"))

    def test_no_netloc(self):
        self.assertFalse(urlwall.isWebURL("mailto:test@example.com"))

    def test_empty(self):
        self.assertFalse(urlwall.isWebURL(""))


class TestUnwrap(unittest.TestCase):
    def test_no_redirect(self):
        self.assertEqual(urlwall.unwrap("https://example.com"), ["https://example.com"])

    def test_url_query_param(self):
        result = urlwall.unwrap("https://example.com/redirect?url=https://target.com")
        self.assertIn("https://target.com", result)
        self.assertIn("https://example.com/redirect", result[0])

    def test_target_query_param(self):
        result = urlwall.unwrap("https://example.com/go?target=https://target.com")
        self.assertIn("https://target.com", result)

    def test_rd_query_param(self):
        result = urlwall.unwrap("https://example.com/rd?url=https://target.com")
        self.assertIn("https://target.com", result)

    def test_cisco_proxy(self):
        url = "https://secure-web.cisco.com/abc123/https%3A%2F%2Ftarget.com"
        result = urlwall.unwrap(url)
        self.assertIn("https://target.com", result)

    def test_chain(self):
        url = "https://a.com/redirect?url=https://b.com/go?target=https://target.com"
        result = urlwall.unwrap(url)
        self.assertEqual(len(result), 3)
        self.assertIn("https://target.com", result)


class TestWriteWarningHTML(unittest.TestCase):
    def test_creates_file(self):
        urls = ["https://example.com"]
        fn = urlwall.writeWarningHTML(urls)
        self.assertTrue(fn.endswith(".html"))
        self.assertTrue(os.path.isfile(fn))
        with open(fn) as f:
            content = f.read()
        self.assertIn("example.com", content)
        # Cleanup
        os.unlink(fn)

    def test_contains_json(self):
        urls = ["https://example.com"]
        fn = urlwall.writeWarningHTML(urls)
        with open(fn) as f:
            content = f.read()
        self.assertIn("example.com", content)
        os.unlink(fn)


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Use a temp file for config
        self.tmpdir = tempfile.mkdtemp()
        self.cfg_fn = os.path.join(self.tmpdir, "setup.plist")
        # Reset singleton
        config._config = None
        self.cfg = config.getConfig(self.cfg_fn)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        config._config = None

    def test_default_browser(self):
        self.assertEqual(self.cfg.getBrowser(), "Safari.app")

    def test_set_browser(self):
        result = self.cfg.setBrowser("Chrome.app")
        self.assertEqual(result, "Chrome.app")
        self.assertEqual(self.cfg.getBrowser(), "Chrome.app")

    def test_set_browser_same(self):
        result = self.cfg.setBrowser("Safari.app")
        self.assertIsNone(result)

    def test_add_allowed_host(self):
        host = self.cfg.addAllowedHost("example.com")
        self.assertEqual(host, "example.com")
        self.assertIn("example.com", self.cfg.plist["hostsAllowed"])

    def test_remove_allowed_host(self):
        self.cfg.addAllowedHost("example.com")
        host = self.cfg.removeAllowedHost("example.com")
        self.assertEqual(host, "example.com")
        self.assertNotIn("example.com", self.cfg.plist["hostsAllowed"])

    def test_add_subdomain_host(self):
        host = self.cfg.addAllowedHostSubdomains("example.com")
        self.assertEqual(host, "example.com")
        self.assertIn("example.com", self.cfg.plist["hostWithSubdomainsAllowed"])

    def test_is_allowed_direct(self):
        self.cfg.addAllowedHost("example.com")
        self.assertTrue(self.cfg.isAllowed("https://example.com"))

    def test_is_allowed_subdomain(self):
        self.cfg.addAllowedHostSubdomains("example.com")
        self.assertTrue(self.cfg.isAllowed("https://sub.example.com"))
        self.assertTrue(self.cfg.isAllowed("https://a.b.example.com"))

    def test_is_not_allowed(self):
        self.assertFalse(self.cfg.isAllowed("https://unknown.com"))

    def test_log_file(self):
        log_fn = self.cfg.logFile
        self.assertTrue(log_fn.endswith(".log"))
        self.assertIn(config.CFG_ROOT, log_fn)


class TestIsUrlAllowed(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cfg_fn = os.path.join(self.tmpdir, "setup.plist")
        config._config = None
        self.cfg = config.getConfig(self.cfg_fn)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        config._config = None

    def test_allowed_host(self):
        self.cfg.addAllowedHost("example.com")
        self.assertTrue(urlwall.isUrlAllowed("https://example.com"))

    def test_not_allowed_host(self):
        self.assertFalse(urlwall.isUrlAllowed("https://unknown.com"))

    def test_unwraps_url_query(self):
        """isUrlAllowed should unwrap ?url= params."""
        self.cfg.addAllowedHost("target.com")
        self.assertTrue(
            urlwall.isUrlAllowed("https://redirect.com/?url=https://target.com")
        )


if __name__ == "__main__":
    unittest.main()
