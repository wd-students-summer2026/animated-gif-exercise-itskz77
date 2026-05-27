"""
Tests for the Animated GIF assignment.

The student must:
  - publish an `animated_gif.html` page that displays their animated GIF
  - link to that page from their personal site's home page (index.html)

Requires Selenium 4.6+ (uses Selenium Manager to auto-manage chromedriver)
and a recent installation of Google Chrome.
"""

import json
import pytest
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


PAGE = "animated_gif.html"


def _build_url(site_url, page=""):
  base = site_url.rstrip("/")
  if not page:
    return base + "/"
  return base + "/" + page.lstrip("/")


def _is_gif(url):
  """HEAD-style check that a URL serves an image and the bytes start with GIF magic."""
  try:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=10) as resp:
      # only read the first 6 bytes (GIF87a / GIF89a)
      head = resp.read(6)
      content_type = resp.headers.get("Content-Type", "").lower()
      return head[:6] in (b"GIF87a", b"GIF89a") or "gif" in content_type
  except Exception:
    return False


class Tests:

  @pytest.fixture(scope="class")
  def settings(self):
    with open('./settings.json', 'r') as f:
      yield json.load(f)

  @pytest.fixture(scope="class")
  def page_url(self, settings):
    return _build_url(settings["site_url"], PAGE)

  @pytest.fixture(scope="class")
  def driver(self, page_url):
    options = Options()
    options.add_argument("--window-size=1400,1000")
    driver = webdriver.Chrome(options=options)
    driver.get(page_url)
    yield driver
    driver.quit()

  def test_page_loads(self, driver):
    """animated_gif.html must load and have a <body>."""
    assert driver.find_element(By.TAG_NAME, "body")

  def test_page_has_gif_image(self, driver, page_url):
    """
    The page must include an <img> whose src points to an actual GIF file.
    We download the first few bytes to confirm it really is a GIF.
    """
    imgs = driver.find_elements(By.TAG_NAME, "img")
    assert imgs, "No <img> elements on animated_gif.html."

    gif_found = None
    for img in imgs:
      src = img.get_attribute("src") or ""
      if not src:
        continue
      abs_src = urljoin(page_url, src)
      if _is_gif(abs_src):
        gif_found = abs_src
        break

    assert gif_found, (
      "None of the <img> elements on animated_gif.html point to an actual "
      "GIF file. Found srcs: {}".format(
        [i.get_attribute('src') for i in imgs]
      )
    )

  def test_images_have_alt(self, driver):
    """Every <img> must have a non-empty alt attribute."""
    for img in driver.find_elements(By.TAG_NAME, "img"):
      alt = img.get_attribute("alt")
      assert alt is not None and alt.strip() != "", (
        "An <img> on animated_gif.html is missing an alt attribute: {}"
        .format(img.get_attribute("src"))
      )

  def test_linked_from_home(self, settings):
    """The home page (index.html) must link to animated_gif.html."""
    home = _build_url(settings["site_url"])
    options = Options()
    options.add_argument("--window-size=1400,1000")
    driver = webdriver.Chrome(options=options)
    try:
      driver.get(home)
      try:
        elem = driver.find_element(
          By.CSS_SELECTOR,
          "a[href='{0}'], a[href$='/{0}']".format(PAGE),
        )
      except NoSuchElementException:
        elem = None
      assert elem, (
        "The home page has no link to animated_gif.html."
      )
    finally:
      driver.quit()
