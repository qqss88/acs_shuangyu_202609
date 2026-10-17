# acs_shuangyu_202609
my chinese class in American Chinese School

## Chinese audio (Kokoro TTS)

The page plays pre-generated Mandarin clips from `audio/` and falls back to the browser's voice for any text without a clip.
After editing any Chinese text in `index.html`, regenerate the clips:

```bash
# one-time: download and unpack the Kokoro v1.1-zh model (~420 MB)
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_1.tar.bz2
tar xjf kokoro-multi-lang-v1_1.tar.bz2

uv run scripts/generate_audio.py --model-dir kokoro-multi-lang-v1_1 --voice zf_001
```

Tests: `uv run --with pytest pytest scripts`

## Chinese audio (iFlytek 科大讯飞 TTS) — `index-xfyun.html`

Same page as `index.html`, but it loads `audio/manifest.xfyun.js` (clips in `audio/xfyun/`).
Put your keys in the git-ignored `.env.local` (`XF_APPID=`, `XF_API_KEY=`, `XF_API_SECRET=`), then:

```bash
uv run scripts/tts_xfyun.py --vcn xiaoyan   # add --force to re-render everything
```

Note: keep `index-xfyun.html` in sync with `index.html` if you edit lesson text; the generator reads `index-xfyun.html`.
