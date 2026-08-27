#!/usr/bin/env python3
"""
Transcribe an audio file via Alibaba Cloud Bailian / DashScope non-realtime ASR
(qwen3-asr-flash-filetrans / qwen-audio-3.0-asr-flash-filetrans) and emit an SRT,
so an existing transcript builder can turn it into a mono/bilingual markdown.

Flow (async, per the official Model Studio doc):
  1) POST  <endpoint>/api/v1/services/audio/asr/transcription  (X-DashScope-Async: enable)
        body: {"model":..., "input":{"file_urls":["<public audio url>"]}, "parameters":{...}}
        -> {"output":{"task_id":"...","task_status":"PENDING"}}
  2) GET   <endpoint>/api/v1/tasks/{task_id}  poll until task_status == SUCCEEDED
        -> output.results[].transcription_url   (public JSON, valid ~24h)
  3) GET transcription_url  -> result JSON;  transcripts[].sentences[].{begin_time?,end_time?,text}  (ms)
  4) Write an .srt from those sentences.

The API accepts a PUBLIC audio URL (filetrans models take no local upload). For
xiaoyuzhou the public episode CDN mp3 URL works without login.

Usage:
  export DASHSCOPE_API_KEY=sk-...
  python dashscope_asr_transcribe.py \
      --url "https://media.xyzcdn.net/.../x.mp3" \
      --out-dir .cc-connect/_xyz_audio --title "fde_s10e27"
  # richer (per-word accuracy + speaker splitting) on qwen-audio-3.0-asr-flash-filetrans:
  python dashscope_asr_transcribe.py --model qwen-audio-3.0-asr-flash-filetrans \
      --url "https://media.xyzcdn.net/.../x.mp3" --out-dir OUT --title x \
      --diarization --lang zh \
      --vocabulary '{"声动活泼":5,"Palantir":5,"FDE":5,"RAG":4}'
  # hotwords pulled from a xiaoyuzhou episode page (extract_xyz_meta.py's auto_vocab.json),
  # merged with any extra manual ones (--vocabulary wins on a key clash):
  python extract_xyz_meta.py --page xyz_page.html --out-dir OUT
  python dashscope_asr_transcribe.py --model qwen-audio-3.0-asr-flash-filetrans \
      --url "..." --out-dir OUT --title x --diarization --lang zh \
      --vocabulary-file OUT/auto_vocab.json --vocabulary '{"雅贤":5,"雷鸟":5}'
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

# Public DashScope open endpoint; the Model Studio doc shows a per-region MaaS host
# ({WorkspaceId}.{region}.maas.aliyuncs.com) which also works -- override with --endpoint.
DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com"
DEFAULT_MODEL = "qwen3-asr-flash-filetrans"   # user-confirmed; sibling: qwen-audio-3.0-asr-flash-filetrans
POLL_INTERVAL_SEC = 5
TASK_TIMEOUT_SEC = 3600


def http_request(url, method="GET", data=None, headers=None):
    req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def submit_task(api_key, endpoint, model, audio_url, language_hints,
                diarization=False, vocabulary=None):
    # Model schema differs: qwen3-asr-*-filetrans takes a single "file_url" string,
    # while the older filetrans family (qwen-audio-3.0 / fun-asr / paraformer) takes
    # an array "file_urls". Sending the wrong key -> InvalidParameter.MalformedURL.
    # The richer features (diarization_enabled, instant hotwords vocabulary) live on
    # the older family (qwen-audio-3.0-asr-flash-filetrans), not on qwen3-asr.
    if "qwen3" in model.lower():
        audio_input = {"file_url": audio_url}
        parameters = {"channel_id": [0], "enable_itn": False, "enable_words": True}
    else:
        audio_input = {"file_urls": [audio_url]}
        parameters = {"channel_id": [0], "language_hints": language_hints}
        if diarization:
            parameters["diarization_enabled"] = True   # sentences gain "speaker_id"
        if vocabulary:
            parameters["vocabulary"] = vocabulary      # instant hotwords, {"word": weight}
    body = {"model": model, "input": audio_input, "parameters": parameters}
    url = endpoint.rstrip("/") + "/api/v1/services/audio/asr/transcription"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    raw = http_request(url, method="POST", data=json.dumps(body).encode("utf-8"), headers=headers)
    payload = json.loads(raw.decode("utf-8"))
    output = payload.get("output", {})
    task_id = output.get("task_id")
    if not task_id:
        raise SystemExit(f"No task_id in submit response: {payload}")
    print(f"[submit] task_id={task_id} status={output.get('task_status')}")
    return task_id


def poll_task(api_key, endpoint, task_id):
    url = endpoint.rstrip("/") + f"/api/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    deadline = time.time() + TASK_TIMEOUT_SEC
    while time.time() < deadline:
        raw = http_request(url, method="GET", headers=headers)
        payload = json.loads(raw.decode("utf-8"))
        output = payload.get("output", {})
        status = output.get("task_status")
        print(f"[poll] status={status} ...", flush=True)
        if status == "SUCCEEDED":
            return output
        if status in ("FAILED", "CANCELED"):
            raise SystemExit(f"Task {status}: {output}")
        time.sleep(POLL_INTERVAL_SEC)
    raise SystemExit("Task timed out.")


def extract_sentences(root):
    """Return the list of {begin_time, end_time, text} sentence dicts."""
    # Known shapes; try explicit paths first.
    for path in (("output", "transcripts"), ("transcripts",),
                 ("output", "sentences"), ("sentences",)):
        cur = root
        ok = True
        for p in path:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                ok = False
                break
        if ok and isinstance(cur, list) and cur and isinstance(cur[0], dict) \
                and "text" in cur[0] and "begin_time" in cur[0]:
            return cur

    # Fallback: any list under a key called 'sentences' (avoids word-level entries).
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "sentences" and isinstance(v, list) and v and isinstance(v[0], dict) \
                        and "text" in v[0] and "begin_time" in v[0]:
                    return v
                r = walk(v)
                if r:
                    return r
        elif isinstance(o, list):
            for it in o:
                r = walk(it)
                if r:
                    return r
        return None

    return walk(root)


def sentences_to_srt(sentences, out_path):
    def fmt(ms):
        s = int(ms) // 1000
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d},{int(ms) % 1000:03d}"

    lines = []
    for i, s in enumerate(sorted(sentences, key=lambda x: x.get("begin_time", 0)), start=1):
        text = (s.get("text") or "").strip().replace("\n", " ")
        sid = s.get("speaker_id")
        if sid is not None:
            text = f"[spk{sid}] {text}"
        begin = int(s.get("begin_time", 0))
        end = int(s.get("end_time", begin))
        lines += [str(i), f"{fmt(begin)} --> {fmt(end)}", text, ""]
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return len(sentences)


def main():
    ap = argparse.ArgumentParser(description="Transcribe public audio via DashScope filetrans ASR to SRT.")
    ap.add_argument("--url", required=True, help="publicly accessible audio URL")
    ap.add_argument("--out-dir", default=".", help="directory to write outputs")
    ap.add_argument("--title", default="transcript", help="output basename (no extension)")
    ap.add_argument("--model", default=os.environ.get("ASR_MODEL", DEFAULT_MODEL), help="DashScope ASR model id")
    ap.add_argument("--endpoint", default=os.environ.get("DASHSCOPE_ENDPOINT", DEFAULT_ENDPOINT))
    ap.add_argument("--lang", nargs="*", default=["zh", "en"], help="language_hints")
    ap.add_argument("--diarization", dest="diarization", action="store_true",
                    help="enable speaker diarization (sentences gain speaker_id / [spkN] in SRT). Needs qwen-audio-3.0-*-filetrans, not qwen3-asr.")
    ap.add_argument("--vocabulary", default=None,
                    help="instant hotwords JSON string, e.g. '{\"声动活泼\":5,\"Palantir\":5,\"FDE\":5}'. Pass a JSON object.")
    ap.add_argument("--vocabulary-file", default=None,
                    help="path to a JSON object file of instant hotwords (e.g. extract_xyz_meta.py's auto_vocab.json); merged with --vocabulary (--vocabulary wins on conflicts).")
    ap.add_argument("--raw", dest="dump_raw", action="store_true", help="also dump the raw result JSON")
    args = ap.parse_args()

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("ERROR: set DASHSCOPE_API_KEY (the Bailian/DashScope sk- key)", file=sys.stderr)
        return 2

    os.makedirs(args.out_dir, exist_ok=True)
    vocab = {}
    if args.vocabulary_file:
        with open(args.vocabulary_file, encoding="utf-8") as f:
            vocab.update(json.load(f))
    if args.vocabulary:
        vocab.update(json.loads(args.vocabulary))   # explicit --vocabulary wins
    vocab = vocab or None
    print(f"[model] {args.model}  [endpoint] {args.endpoint}  "
          f"[diar] {args.diarization}  [vocab] {bool(vocab)}")

    task_id = submit_task(api_key, args.endpoint, args.model, args.url, args.lang,
                          diarization=args.diarization, vocabulary=vocab)
    out = poll_task(api_key, args.endpoint, task_id)

    # The polled output points to the full result JSON (public, ~24h).
    # qwen3-asr-* exposes output.result.transcription_url (single object);
    # the older filetrans family exposes output.results[].transcription_url (array).
    transcription_url = ""
    single = out.get("result")
    if isinstance(single, dict) and single.get("transcription_url"):
        transcription_url = single["transcription_url"]
    if not transcription_url:
        for res in out.get("results", []) or []:
            if res.get("transcription_url"):
                transcription_url = res["transcription_url"]
                break
    if not transcription_url:
        # Some responses inline the result already.
        sentences = extract_sentences({"output": out, **out})
    else:
        print(f"[result] transcription_url -> {transcription_url}")
        raw = http_request(transcription_url, method="GET")
        if args.dump_raw:
            with open(os.path.join(args.out_dir, f"{args.title}.raw.json"), "wb") as f:
                f.write(raw)
        sentences = extract_sentences(json.loads(raw.decode("utf-8")))

    if not sentences:
        raise SystemExit("No sentences with begin_time/end_time found in the result. Dump raw and inspect.")

    srt_path = os.path.join(args.out_dir, f"{args.title}.srt")
    n = sentences_to_srt(sentences, srt_path)
    print(f"wrote {n} sentences -> {srt_path}")


if __name__ == "__main__":
    sys.exit(main())
