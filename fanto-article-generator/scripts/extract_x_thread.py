"""
Extract X/Twitter thread text and media through a CDP browser.

Why this exists:
  X/Twitter images are often loaded into the DOM lazily. Plain text fetchers can
  return useful text while silently losing images. This helper opens the URL in
  Chrome, scrolls to trigger lazy loading, extracts text/media context, downloads
  pbs.twimg.com/media images, downloads MP4 videos and converts them to GIFs, and
  writes a JSON manifest for article layout.

L4 editorial strength additions (Fix C, 2026-06-10):
  In addition to text + media, this script now captures:
    - links: external content <a href> entries inside the article body, so
      main agent can preserve inline source links (e.g., blog post references
      in author's posts). X-internal nav links are filtered out.
    - author: post author profile (name, handle, avatar_url, verified, bio)
      so the translated article can place author bio at TOP for editorial
      credibility. Without these, the L4 editorial-strength layer (黑话密度 /
      KOL 引用密度 / 视觉锚) cannot be fully implemented downstream.

Depends on:
  - Python stdlib + websocket-client (`pip install websocket-client`)
  - Optional for GIF conversion: opencv-python + Pillow (`pip install opencv-python Pillow`)
  - Chrome must be available locally or already running with:
      --remote-debugging-port=9222 --remote-allow-origins=*

If opencv-python/Pillow are not installed, MP4 files are still downloaded but
the GIF conversion step is skipped (with a warning in the manifest). Static
image extraction is unaffected.

Usage:
  python scripts/extract_x_thread.py <x_url> --out images_topic --json x_thread.json
"""

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

from cdp_utils import CDP, ensure_cdp, stop_chrome


def open_tab(cdp_base, url):
    req = urllib.request.Request(
        f"{cdp_base}/json/new?url=about:blank", method="PUT"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        tab = json.loads(r.read())
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    wait_for_load(cdp)
    return tab["id"], cdp


def wait_for_load(cdp, timeout_s=30):
    deadline = time.time() + timeout_s
    state_ready = False
    while time.time() < deadline:
        state = eval_js(cdp, "document.readyState")
        if state in ("interactive", "complete"):
            state_ready = True
        if state_ready:
            # X is a JS SPA — readyState can hit "complete" before tweets render.
            # Wait until at least one article element appears in the DOM.
            article_count = eval_js(cdp, "document.querySelectorAll('article').length") or 0
            if article_count > 0:
                return
        time.sleep(0.5)
    raise RuntimeError("Page did not reach interactive/complete state with tweet articles")


def eval_js(cdp, expression, timeout=20):
    result = cdp.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        timeout=timeout,
    )
    value = result.get("result", {})
    if "value" in value:
        return value["value"]
    return None


def scroll_page(cdp, rounds=8, delay=1.5):
    for _ in range(rounds):
        eval_js(cdp, "window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay)

def wait_for_images(cdp, timeout_s=15):
    """Wait for pbs.twimg.com images (including video_thumb thumbnails) to finish loading after scrolling."""
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        result = eval_js(cdp, """
          (() => {
            const imgs = document.querySelectorAll(
              'img[src*="pbs.twimg.com/media"], img[src*="pbs.twimg.com/tweet_video_thumb"]'
            );
            if (imgs.length === 0) return {ready: false, total: 0, loaded: 0};
            const loaded = Array.from(imgs).filter(i => i.complete && i.naturalWidth > 0).length;
            return {ready: loaded === imgs.length, total: imgs.length, loaded};
          })()
        """)
        last = result
        if result and result.get("ready"):
            return result
        time.sleep(0.5)
    # Don't raise — proceed with whatever we have
    return last or {"ready": False, "total": 0, "loaded": 0}


def extract_payload(cdp):
    script = r"""
(() => {
  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();

  // ---- Unicode-safe text extraction (Gap 2 fix) ----
  // Greek letters and other non-ASCII chars in X tweet DOM can degrade to U+FFFD
  // replacement chars at the CDP transport layer. Try multiple extraction methods
  // and pick the one with the fewest replacement chars. Records confidence so the
  // Python side can warn when text is unreliable.
  const REPLACEMENT = "�";
  const countReplacements = (s) => (s.match(new RegExp(REPLACEMENT, "g")) || []).length;

  function extractCleanText(el) {
    if (!el) return { text: "", confidence: 1.0, replacement_count: 0 };
    const methods = [
      () => el.textContent || "",     // Most Unicode-preserving (preserves τ, σ, α...)
      () => el.innerText || "",       // Layout-aware (may drop some Unicode in rare cases)
      () => {                          // Fallback: re-parse innerHTML through a fresh div
        const div = document.createElement("div");
        div.innerHTML = el.innerHTML || "";
        return div.textContent || "";
      }
    ];
    const results = methods.map(fn => {
      try { return fn(); } catch (e) { return ""; }
    });
    const scored = results.map(s => ({ s, score: countReplacements(s) }));
    scored.sort((a, b) => a.score - b.score);
    const best = scored[0];
    const allCorrupted = scored.every(s => s.score > 0);
    const confidence = best.score === 0 ? 1.0 : (allCorrupted ? 0.3 : 0.7);
    return { text: clean(best.s), confidence, replacement_count: best.score };
  }

  // ---- Character offset within an article for an image/video element (Gap 1 fix) ----
  // Range.toString() from article start to just before the target element gives
  // the count of characters that come before the element in document order.
  // This is the position where the image "breaks" the text flow.
  function charOffsetWithinArticle(articleEl, targetEl) {
    if (!articleEl || !targetEl) return -1;
    try {
      const range = document.createRange();
      range.setStart(articleEl, 0);
      range.setEndBefore(targetEl);
      return range.toString().length;
    } catch (e) {
      return -1;
    }
  }

  // Build article-indexed text map (using clean extraction)
  const articles = Array.from(document.querySelectorAll('article'));
  const articleTextMeta = articles.map((article) => {
    const tweetText = article.querySelector('[data-testid="tweetText"], div[lang]');
    return extractCleanText(tweetText || article);
  });
  const articleTexts = articleTextMeta.map(m => m.text);
  // Min confidence across all articles — used to flag overall text reliability.
  const minConfidence = articleTextMeta.reduce(
    (acc, m) => Math.min(acc, m.confidence), 1.0
  );
  const totalReplacements = articleTextMeta.reduce(
    (acc, m) => acc + m.replacement_count, 0
  );

  // Collect tweet text blocks in document order for position mapping
  // Try the specific [data-testid="tweetText"] selector first (works even when login wall is present,
  // because the actual tweet element still renders in the DOM)
  const textBlocks = Array.from(document.querySelectorAll('[data-testid="tweetText"], article div[lang]'))
    .map((el) => extractCleanText(el).text)
    .filter(Boolean);

  // FIX 1 (text pollution from login wall): do NOT fall back to document.body.innerText.
  // Fall back to per-article text instead, which only contains tweet content (not login modal text).
  const pageText = clean(
    textBlocks.join("\n\n")
    || articleTexts.filter(Boolean).join("\n\n")
  );

  // Detect login wall presence (used by build_warnings for nuanced reporting)
  const loginWallText = document.body.innerText || "";
  const hasLoginWall = (
    loginWallText.includes("登录")
    || loginWallText.includes("注册")
    || loginWallText.includes("登入")
    || loginWallText.toLowerCase().includes("sign in to x")
  );

  // ---- Greek letter detection (Gap 2) ----
  // Common in benchmark names (τ-bench / σ-bench / α-bench...). Flag presence so
  // Python side can warn if extraction was lossy around these characters.
  const GREEK_LETTERS = ["τ", "σ", "α", "β", "γ", "δ", "μ", "π", "θ", "λ", "ω", "φ"];
  const greekLettersDetected = GREEK_LETTERS.filter(g => pageText.includes(g));

  // ---- Static images (pbs.twimg.com/media) ----
  const seen = new Set();
  const images = [];
  const allMediaImgs = Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media"]'));

  allMediaImgs.forEach((img) => {
    const url = img.src;
    if (seen.has(url)) return;
    seen.add(url);

    const article = img.closest("article");
    const articleIdx = article ? articles.indexOf(article) : -1;
    const tweetText = articleIdx >= 0 ? articleTexts[articleIdx] || "" : "";
    const localOffset = charOffsetWithinArticle(article, img);
    // Global offset = sum of preceding articles' text + separator count + local offset
    let globalOffset = localOffset;
    if (articleIdx > 0) {
      for (let i = 0; i < articleIdx; i++) {
        globalOffset += (articleTexts[i] || "").length;
      }
      globalOffset += 2; // "\n\n" separator
    }

    const imgsInArticle = article
      ? Array.from(article.querySelectorAll('img[src*="pbs.twimg.com/media"]'))
      : [];
    const imgIdxInTweet = imgsInArticle.indexOf(img);

    images.push({
      url: url,
      alt: img.alt || "",
      tweet_index: articleIdx,
      img_index_in_tweet: imgIdxInTweet,
      total_imgs_in_tweet: imgsInArticle.length,
      // Gap 1: char_offset fields
      char_offset_in_article: localOffset,
      char_offset_global: globalOffset,
      // Gap 2: text confidence inherited from the containing article
      text_confidence: articleIdx >= 0 ? articleTextMeta[articleIdx].confidence : 1.0,
      tweet_text: tweetText.slice(0, 5000)
    });
  });

  // ---- Video thumbnails (pbs.twimg.com/tweet_video_thumb) — G3 ----
  const videoThumbnails = [];
  const seenThumbs = new Set();
  const allThumbs = Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/tweet_video_thumb"]'));
  allThumbs.forEach((img) => {
    const url = img.src;
    if (seenThumbs.has(url)) return;
    seenThumbs.add(url);

    const article = img.closest("article");
    const articleIdx = article ? articles.indexOf(article) : -1;
    const tweetText = articleIdx >= 0 ? articleTexts[articleIdx] || "" : "";
    const localOffset = charOffsetWithinArticle(article, img);
    let globalOffset = localOffset;
    if (articleIdx > 0) {
      for (let i = 0; i < articleIdx; i++) {
        globalOffset += (articleTexts[i] || "").length;
      }
      globalOffset += 2;
    }

    const thumbsInArticle = article
      ? Array.from(article.querySelectorAll('img[src*="pbs.twimg.com/tweet_video_thumb"]'))
      : [];
    const thumbIdxInTweet = thumbsInArticle.indexOf(img);

    videoThumbnails.push({
      url: url,
      tweet_index: articleIdx,
      img_index_in_tweet: thumbIdxInTweet,
      total_thumbs_in_tweet: thumbsInArticle.length,
      char_offset_in_article: localOffset,
      char_offset_global: globalOffset,
      text_confidence: articleIdx >= 0 ? articleTextMeta[articleIdx].confidence : 1.0,
      tweet_text: tweetText.slice(0, 5000)
    });
  });

  // ---- Videos (MP4 from <video> source or videoHint HTML) — G1 ----
  const seenVideos = new Set();
  const videos = [];
  // Strategy 1: <video> elements with src attribute
  document.querySelectorAll('video').forEach((video) => {
    const src = video.currentSrc || video.src || "";
    if (!src || !src.includes("video.twimg.com") || !src.endsWith(".mp4")) return;
    if (seenVideos.has(src)) return;
    seenVideos.add(src);

    const article = video.closest("article");
    const articleIdx = article ? articles.indexOf(article) : -1;
    const tweetText = articleIdx >= 0 ? articleTexts[articleIdx] || "" : "";
    const localOffset = charOffsetWithinArticle(article, video);
    let globalOffset = localOffset;
    if (articleIdx > 0) {
      for (let i = 0; i < articleIdx; i++) {
        globalOffset += (articleTexts[i] || "").length;
      }
      globalOffset += 2;
    }
    const videosInArticle = article
      ? Array.from(article.querySelectorAll('video'))
      : [];
    const vidIdx = videosInArticle.indexOf(video);

    videos.push({
      url: src,
      tweet_index: articleIdx,
      video_index_in_tweet: vidIdx,
      total_videos_in_tweet: videosInArticle.length,
      char_offset_in_article: localOffset,
      char_offset_global: globalOffset,
      text_confidence: articleIdx >= 0 ? articleTextMeta[articleIdx].confidence : 1.0,
      tweet_text: tweetText.slice(0, 5000)
    });
  });
  // Strategy 2: MP4 src inside any data-testid*="video" container
  document.querySelectorAll('[data-testid*="video"]').forEach((container) => {
    const html = container.outerHTML || "";
    const match = html.match(/src="(https:\/\/video\.twimg\.com\/tweet_video\/[^"]+\.mp4)"/);
    if (!match) return;
    const src = match[1];
    if (seenVideos.has(src)) return;
    seenVideos.add(src);

    const article = container.closest("article");
    const articleIdx = article ? articles.indexOf(article) : -1;
    const tweetText = articleIdx >= 0 ? articleTexts[articleIdx] || "" : "";
    const localOffset = charOffsetWithinArticle(article, container);
    let globalOffset = localOffset;
    if (articleIdx > 0) {
      for (let i = 0; i < articleIdx; i++) {
        globalOffset += (articleTexts[i] || "").length;
      }
      globalOffset += 2;
    }
    const videosInArticle = article
      ? Array.from(article.querySelectorAll('[data-testid*="video"]'))
          .map((c) => {
            const m = (c.outerHTML || "").match(/src="(https:\/\/video\.twimg\.com\/tweet_video\/[^"]+\.mp4)"/);
            return m ? m[1] : null;
          })
          .filter(Boolean)
      : [];
    const vidIdx = videosInArticle.indexOf(src);

    videos.push({
      url: src,
      tweet_index: articleIdx,
      video_index_in_tweet: vidIdx,
      total_videos_in_tweet: videosInArticle.length,
      char_offset_in_article: localOffset,
      char_offset_global: globalOffset,
      text_confidence: articleIdx >= 0 ? articleTextMeta[articleIdx].confidence : 1.0,
      tweet_text: tweetText.slice(0, 5000)
    });
  });

  // ---- External content links (Fix C, L4 editorial strength, 2026-06-10) ----
  // Preserve <a href> entries inside the article body so main agent can keep inline
  // source links (e.g., Addy Osmani's blog post references) in the translated article.
  // X-internal nav links (profile, /home, hashtag, status) are filtered out — only
  // external content links (other domains) are kept as payload.links.
  const links = (function() {
    const result = [];
    try {
      articles.forEach((article) => {
        const anchors = Array.from(article.querySelectorAll('a[href]'));
        anchors.forEach(a => {
          try {
            const href = a.href;
            const text = (a.textContent || '').trim();
            if (!href || !text) return;
            if (href.startsWith('javascript:')) return;
            // Skip X-internal navigation (profile / status / hashtag / search / home)
            if (/^https?:\/\/(www\.)?(x|twitter)\.com\//.test(href)) return;
            const localOffset = charOffsetWithinArticle(article, a);
            result.push({ href, text, char_offset_in_article: localOffset });
          } catch (e) {
            // per-link error shouldn't break whole extraction
          }
        });
      });
    } catch (e) {
      // whole-link-section failure → return whatever was collected so far
    }
    return result;
  })();

  // ---- Author bio (Fix C, L4 editorial strength, 2026-06-10) ----
  // Capture post author profile so translated articles can place bio at TOP for
  // editorial credibility (e.g., "Addy Osmani, Chrome Engineering Lead, O'Reilly
  // author"). Without this, the bio is lost and only the username tag is preserved.
  const author = (function() {
    try {
      const nameEl = document.querySelector('[data-testid="User-Name"]');
      if (!nameEl) return null;
      const avatarEl = document.querySelector(
        'article img[alt*="avatar"], [data-testid="UserAvatar-Container"] img, article img[src*="profile_images"]'
      );
      let avatarUrl = null;
      if (avatarEl && avatarEl.src) {
        // Request 200x200 for decent inline display size (not original 1024+ which is overkill)
        try {
          avatarUrl = avatarEl.src.replace(/name=\w+/, 'name=200_200');
        } catch (e) {
          avatarUrl = null;
        }
      }
      return {
        name: (nameEl.textContent || '').trim() || null,
        handle: (() => {
          try {
            const a = nameEl.closest('a');
            if (!a) return null;
            const href = a.getAttribute('href') || '';
            // Convert /user_handle → @user_handle for 公众号-friendly display
            const m = href.match(/^\/(.+)$/);
            return m ? '@' + m[1] : null;
          } catch (e) {
            return null;
          }
        })(),
        avatar_url: avatarUrl,
        verified: !!nameEl.querySelector(
          'svg[aria-label*="Verified"], svg[data-testid*="verification"]'
        ),
        bio: (document.querySelector('[data-testid="UserDescription"]')?.textContent || '').trim() || null
      };
    } catch (e) {
      return null; // author extraction failure → null, not crash
    }
  })();

  // ---- Video hints (raw HTML for diagnostics; not used for download anymore) ----
  const videoHints = Array.from(document.querySelectorAll('[data-testid*="video"], video, img[src*="tweet_video_thumb"], a[href*="/video/"]'))
    .map((el) => clean(el.outerHTML).slice(0, 500));

  // ---- media_container_count — G4 fix: separate static + thumbnail counts to avoid double counting ----
  const staticMediaCount = document.querySelectorAll('img[src*="pbs.twimg.com/media"]').length;
  const thumbCount = document.querySelectorAll('img[src*="pbs.twimg.com/tweet_video_thumb"]').length;
  const videoCount = videos.length;
  const mediaContainerCount = staticMediaCount + thumbCount + videoCount;

  return {
    text: pageText,
    text_blocks: textBlocks,
    images,
    videos,
    video_thumbnails: videoThumbnails,
    video_hints: videoHints,
    url: location.href,
    title: document.title || "",
    article_count: articles.length,
    text_block_count: textBlocks.length,
    media_container_count: mediaContainerCount,
    media_breakdown: {
      static: staticMediaCount,
      thumbnails: thumbCount,
      videos: videoCount
    },
    has_login_wall: hasLoginWall,
    // ---- Fix C (L4 editorial strength, 2026-06-10) ----
    // Links: external content <a href> entries inside the article body. Main agent
    // can preserve these in the translated article as inline markdown links, giving
    // readers deeper entry points (e.g., Addy Osmani's referenced blog posts).
    links: links,
    // Author: post author profile. Main agent can place at TOP of 公众号 article
    // for editorial credibility (e.g., "Addy Osmani, Chrome Engineering Lead, O'Reilly author").
    author: author,
    // ---- Gap 2: overall text reliability metadata ----
    text_stats: {
      min_confidence: minConfidence,
      total_replacement_chars: totalReplacements,
      greek_letters_detected: greekLettersDetected,
      benchmark_name_patterns_detected: [
        // Flag benchmark names that use Greek letters — if confidence < 0.7,
        // the Greek letter may have been corrupted. Downstream translation
        // should verify against the original source.
        ...greekLettersDetected.map(g => `${g}-bench`)
      ]
    }
  };
})()
"""
    return eval_js(cdp, script, timeout=30)


def build_warnings(payload):
    warnings = []
    text = payload.get("text", "")
    title = payload.get("title", "")
    combined = f"{title}\n{text}".lower()
    # FIX 3 (login wall false positive): prefer the JS-detected has_login_wall flag over text pattern matching.
    # Pattern matching is unreliable (Chinese login CTAs like "登录"/"注册" can appear in actual tweet text).
    has_login_wall = bool(payload.get("has_login_wall", False))

    # Count successful media extractions to decide if the warning is meaningful
    media_extracted = (
        len(payload.get("images", []))
        + len(payload.get("videos", []))
        + len(payload.get("video_thumbnails", []))
    )
    if has_login_wall and media_extracted > 0:
        # Login wall present BUT media was still successfully extracted (CDP/JS can read the DOM
        # even when the user-facing UI shows a modal). Downgrade to informational note.
        warnings.append(
            f"Login wall detected in UI, but {media_extracted} media item(s) were "
            f"still extracted from the DOM. Text may be partial."
        )
    elif has_login_wall and media_extracted == 0:
        # Login wall AND nothing extracted — this is a real failure.
        warnings.append(
            "Page appears to be a login/interstitial/unsupported page; extraction may be incomplete."
        )

    current_url = payload.get("url", "")
    if "/i/flow/login" in current_url or "login" in current_url.lower():
        warnings.append(f"Browser ended on a login URL: {current_url}")

    if payload.get("article_count", 0) == 0:
        warnings.append("No tweet article nodes found in DOM.")

    if len(text.strip()) < 80:
        warnings.append("Extracted text is very short; check whether the page fully loaded.")

    if not payload.get("images") and payload.get("media_container_count", 0) > 0:
        warnings.append(
            "Media containers were detected but no pbs.twimg.com/media images were extracted."
        )

    # G1: video hint warning removed — videos are now downloaded automatically;
    # only flag actual download failures below.

    failed_images = [
        item for item in payload.get("images", []) if item.get("download_error")
    ]
    if failed_images:
        warnings.append(f"{len(failed_images)} image(s) failed to download.")

    failed_videos = [
        item for item in payload.get("videos", []) if item.get("download_error")
    ]
    if failed_videos:
        warnings.append(f"{len(failed_videos)} video(s) failed to download.")

    failed_gifs = [
        item for item in payload.get("videos", []) if item.get("gif_error")
    ]
    if failed_gifs:
        warnings.append(
            f"{len(failed_gifs)} video(s) downloaded but GIF conversion failed: "
            "install opencv-python + Pillow or check MP4 integrity."
        )

    # ---- Gap 2: text_stats-based warnings (Greek letter / Unicode corruption) ----
    text_stats = payload.get("text_stats") or {}
    min_conf = text_stats.get("min_confidence", 1.0)
    rep_count = text_stats.get("total_replacement_chars", 0)
    greek_letters = text_stats.get("greek_letters_detected", [])
    bench_patterns = text_stats.get("benchmark_name_patterns_detected", [])

    if min_conf < 1.0 and rep_count > 0:
        warnings.append(
            f"Text extraction has {rep_count} replacement char(s) "
            f"(U+FFFD); confidence={min_conf:.1f}. "
            f"Recheck the source for any Unicode chars (Greek letters, math symbols)."
        )
    if min_conf < 0.5:
        warnings.append(
            f"Text confidence is low ({min_conf:.1f}); "
            f"downstream translation should cross-reference the original URL."
        )
    if bench_patterns:
        warnings.append(
            f"Greek-letter benchmark names detected: {bench_patterns}. "
            f"Verify spelling against source — common corruption: τ→'笔', σ→'西格玛'."
        )

    return warnings


def normalize_image_url(url):
    """Force original-quality image URL. Overrides any existing name/format params."""
    parsed = urllib.parse.urlparse(url)
    qs = dict(urllib.parse.parse_qsl(parsed.query))
    qs["name"] = "orig"
    qs.setdefault("format", "jpg")
    query = urllib.parse.urlencode(qs)
    return urllib.parse.urlunparse(parsed._replace(query=query))


def image_extension(url, content_type):
    qs = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
    fmt = qs.get("format")
    if fmt:
        return "." + re.sub(r"[^a-z0-9]", "", fmt.lower())
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    return ".jpg"


def download_images(images, out_dir, max_retries=4, base_delay=1.0, backoff=2.0):
    """Download pbs.twimg.com images with exponential-backoff retry (G5).

    max_retries=4 → up to 4 attempts (intervals 1s, 2s, 4s, 8s before each retry).
    """
    os.makedirs(out_dir, exist_ok=True)
    downloaded = []
    for index, image in enumerate(images, start=1):
        url = normalize_image_url(image["url"])
        item = dict(image)
        item["download_url"] = url

        success = False
        last_exc = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://x.com/",
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    ext = image_extension(url, resp.headers.get("content-type", ""))
                if len(data) < 100:
                    raise ValueError(f"Downloaded image too small ({len(data)} bytes), likely a placeholder")
                filename = f"x_media_{index:02d}{ext}"
                path = os.path.join(out_dir, filename)
                with open(path, "wb") as f:
                    f.write(data)
                item["local_path"] = path.replace("\\", "/")
                item["bytes"] = len(data)
                item.pop("download_error", None)
                success = True
                break
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (backoff ** attempt))
        if not success:
            item["download_error"] = str(last_exc) if last_exc else "unknown download error"
        downloaded.append(item)
    return downloaded


def download_videos(videos, out_dir, max_retries=4, base_delay=1.0, backoff=2.0):
    """Download MP4 videos from video.twimg.com with exponential-backoff retry (G1, G5)."""
    os.makedirs(out_dir, exist_ok=True)
    downloaded = []
    for index, video in enumerate(videos, start=1):
        url = video["url"]
        item = dict(video)
        item["download_url"] = url

        success = False
        last_exc = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://x.com/",
                    },
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                if len(data) < 1000:
                    raise ValueError(f"Downloaded MP4 too small ({len(data)} bytes), likely a placeholder")
                filename = f"x_video_{index:02d}.mp4"
                path = os.path.join(out_dir, filename)
                with open(path, "wb") as f:
                    f.write(data)
                item["mp4_path"] = path.replace("\\", "/")
                item["bytes"] = len(data)
                item.pop("download_error", None)
                success = True
                break
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (backoff ** attempt))
        if not success:
            item["download_error"] = str(last_exc) if last_exc else "unknown download error"
        downloaded.append(item)
    return downloaded


def convert_mp4_to_gif(mp4_path, gif_path, max_frames=20, width=900,
                      frame_duration_ms=100, max_size_mb=5):
    """Convert an MP4 to a GIF using OpenCV + PIL (G1).

    Returns a dict with success status, frame count, file size, and any error.
    If cv2/PIL are unavailable, returns success=False with a clear error.
    """
    try:
        import cv2  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError as exc:
        return {
            "success": False,
            "frames": 0,
            "bytes": 0,
            "error": f"cv2/PIL not available: {exc}. Run: pip install opencv-python Pillow",
        }

    if not os.path.exists(mp4_path):
        return {"success": False, "frames": 0, "bytes": 0, "error": f"MP4 not found: {mp4_path}"}

    try:
        cap = cv2.VideoCapture(mp4_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            cap.release()
            return {"success": False, "frames": 0, "bytes": 0, "error": "MP4 has 0 frames"}

        # Sample frames evenly across the video
        step = max(1, total // max_frames)
        sampled_indices = list(range(0, total, step))[:max_frames]
        frames = []
        for idx in sampled_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            # BGR → RGB → PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            # Resize to width=900, preserving aspect ratio
            if img.width != width:
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.LANCZOS)
            frames.append(img)
        cap.release()

        if not frames:
            return {"success": False, "frames": 0, "bytes": 0, "error": "No frames decoded"}

        # Save as GIF
        duration_per_frame = frame_duration_ms
        frames[0].save(
            gif_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration_per_frame,
            loop=0,
            optimize=True,
        )

        # Check output size
        size_bytes = os.path.getsize(gif_path)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > max_size_mb:
            return {
                "success": False,
                "frames": len(frames),
                "bytes": size_bytes,
                "error": f"GIF {size_mb:.1f}MB exceeds {max_size_mb}MB limit. Reduce max_frames or width.",
            }

        return {
            "success": True,
            "frames": len(frames),
            "bytes": size_bytes,
            "error": None,
        }
    except Exception as exc:
        return {"success": False, "frames": 0, "bytes": 0, "error": str(exc)}


def download_video_thumbnails(thumbnails, out_dir, max_retries=4, base_delay=1.0, backoff=2.0):
    """Download pbs.twimg.com/tweet_video_thumb images (G3)."""
    os.makedirs(out_dir, exist_ok=True)
    downloaded = []
    for index, thumb in enumerate(thumbnails, start=1):
        url = normalize_image_url(thumb["url"])
        item = dict(thumb)
        item["download_url"] = url

        success = False
        last_exc = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://x.com/",
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    ext = image_extension(url, resp.headers.get("content-type", ""))
                if len(data) < 100:
                    raise ValueError(f"Thumbnail too small ({len(data)} bytes)")
                filename = f"x_thumb_{index:02d}{ext}"
                path = os.path.join(out_dir, filename)
                with open(path, "wb") as f:
                    f.write(data)
                item["local_path"] = path.replace("\\", "/")
                item["bytes"] = len(data)
                item.pop("download_error", None)
                success = True
                break
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (backoff ** attempt))
        if not success:
            item["download_error"] = str(last_exc) if last_exc else "unknown download error"
        downloaded.append(item)
    return downloaded


def _page_signature(cdp):
    """Scroll progress signal: [article count, media img count, scrollHeight].

    X Article pages keep the article count constant (the whole article is one
    tweet subtree) while inline images mount lazily during scrolling — article
    count alone stabilizes after 1-2 rounds and scroll_until_stable breaks
    before the images exist (2026-08-11). Images appear only after the
    paragraphs holding them stream in, so the signature also tracks
    scrollHeight: it keeps rising while content is still streaming, and a
    stable height means rendering is complete.
    """
    sig = eval_js(
        cdp,
        "(() => [document.querySelectorAll('article').length,"
        " document.querySelectorAll('img[src*=\"pbs.twimg.com/media\"]').length,"
        " document.body.scrollHeight])()",
    )
    return list(sig) if sig else [0, 0, 0]


def scroll_until_stable(cdp, max_rounds=20, delay=1.5, stable_threshold=2):
    """Scroll page until (article, media-img) signature stabilizes (G2).

    Returns the number of rounds actually performed.
    """
    prev_sig = _page_signature(cdp)
    stable_rounds = 0
    rounds_done = 0
    for i in range(max_rounds):
        # One scroll per iteration (reuse the simple scroll_page helper)
        eval_js(cdp, "window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay)
        rounds_done += 1
        current_sig = _page_signature(cdp)
        if tuple(current_sig) == tuple(prev_sig) and current_sig[0] > 0:
            stable_rounds += 1
            if stable_rounds >= stable_threshold:
                break
        else:
            stable_rounds = 0
        prev_sig = current_sig
    return rounds_done


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="X/Twitter URL to open in Chrome")
    parser.add_argument("--out", default="images_x_thread", help="directory for images")
    parser.add_argument("--json", default="x_thread_manifest.json", help="JSON output path")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--scroll-rounds", type=int, default=8,
                        help="Max scroll rounds for G2 scroll_until_stable (default 8 for backwards compat; recommend 20 for long threads)")
    parser.add_argument("--keep-chrome", action="store_true")
    args = parser.parse_args()

    chrome_proc = None
    tab_id = None
    cdp = None

    try:
        chrome_proc, host = ensure_cdp(args.port, window_size="1280,1600")
        cdp_base = f"http://{host}:{args.port}"
        tab_id, cdp = open_tab(cdp_base, args.url)

        # G2: scroll until article count stabilizes (was: fixed 8 rounds)
        rounds_done = scroll_until_stable(cdp, max_rounds=args.scroll_rounds)
        print(f"Scroll: {rounds_done} rounds (max {args.scroll_rounds})")

        img_status = wait_for_images(cdp)
        print(f"Image load: {img_status.get('loaded', 0)}/{img_status.get('total', 0)} ready")

        payload = extract_payload(cdp)

        # Static images (with G5 exponential-backoff retry)
        payload["images"] = download_images(payload.get("images", []), args.out)

        # G3: video thumbnails
        payload["video_thumbnails"] = download_video_thumbnails(
            payload.get("video_thumbnails", []), args.out
        )

        # G1: videos — download MP4, then convert to GIF
        videos = payload.get("videos", [])
        if videos:
            print(f"Downloading {len(videos)} video(s)...")
            videos = download_videos(videos, args.out)
            for v in videos:
                if v.get("mp4_path") and not v.get("download_error"):
                    gif_path = v["mp4_path"].replace(".mp4", ".gif")
                    result = convert_mp4_to_gif(v["mp4_path"], gif_path)
                    v["gif_path"] = gif_path if result.get("success") else None
                    v["gif_frames"] = result.get("frames", 0)
                    v["gif_bytes"] = result.get("bytes", 0)
                    if not result.get("success"):
                        v["gif_error"] = result.get("error", "unknown conversion error")
                    if result.get("success"):
                        msg = "GIF " + os.path.basename(gif_path) + f" ({result.get('frames', 0)} frames)"
                    else:
                        msg = "GIF conversion failed: " + str(result.get("error"))
                    print(f"  Video: {os.path.basename(v['mp4_path'])} -> {msg}")
        payload["videos"] = videos

        payload["has_video_hint"] = bool(payload.get("video_hints"))
        payload["warnings"] = build_warnings(payload)

        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        gif_count = sum(1 for v in videos if v.get("gif_path"))
        print(
            "Extracted: "
            f"{len(payload.get('text', ''))} text chars, "
            f"{len(payload.get('images', []))} images, "
            f"{len(videos)} videos ({gif_count} GIFs converted), "
            f"{len(payload.get('video_thumbnails', []))} video thumbnails. "
            f"Manifest: {args.json}"
        )
        if payload["warnings"]:
            print("Warnings:")
            for warning in payload["warnings"]:
                print(f"- {warning}")
    finally:
        if cdp is not None:
            cdp.close()
        if tab_id:
            try:
                with urllib.request.urlopen(f"{cdp_base}/json/close/{tab_id}", timeout=5):
                    pass
            except Exception:
                pass
        if chrome_proc is not None and not args.keep_chrome:
            stop_chrome(chrome_proc)


if __name__ == "__main__":
    main()
