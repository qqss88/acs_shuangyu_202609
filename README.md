# acs_shuangyu_202609
my chinese class in American Chinese School

## Site layout

| Path | What it is |
|------|------------|
| `index.html` | Landing page linking every lesson and poem |
| `lessons/lessonN.html` | Interactive textbook lessons (第三课 – 第六课) |
| `poems/*.html` | Classic poem reading apps (咏鹅, 静夜思, 悯农) |
| `index-xfyun.html` | Lesson 3 variant using pre-generated iFlytek audio |

Every lesson and poem page has a fixed "← 返回首页" link back to `index.html`.

**Adding a page:** drop the file into `lessons/` or `poems/`, add a card for it in `index.html`
(and bump the 课 / 首 count), and copy the `home-backlink` anchor right after its `<body>` tag.

The pages in `lessons/` and `poems/` speak with the browser's Web Speech API.

Do not commit `clsmember.csv` (class roster with parent contact info); it is git-ignored.

## Chinese audio (Kokoro TTS) — needs updating

`scripts/generate_audio.py` reads `lessons/lesson3.html` (it used to read the old Lesson 3 `index.html`).
Note that `lessons/lesson3.html` currently does not load the clips: to use them again, add
`<script src="../audio/manifest.js"></script>` plus the clip-playback code back to that page, and
change the manifest `dir` to `../audio/kokoro` since the page now lives one folder down.

```bash
# one-time: download and unpack the Kokoro v1.1-zh model (~420 MB)
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_1.tar.bz2
tar xjf kokoro-multi-lang-v1_1.tar.bz2

uv run scripts/generate_audio.py --model-dir kokoro-multi-lang-v1_1 --voice zf_001
```

Tests: `uv run --with pytest pytest scripts`

## Chinese audio (iFlytek 科大讯飞 TTS) — `index-xfyun.html`

`index-xfyun.html` loads `audio/manifest.xfyun.js` (clips in `audio/xfyun/`) and is what the generator reads.
Put your keys in the git-ignored `.env.local` (`XF_APPID=`, `XF_API_KEY=`, `XF_API_SECRET=`), then:

```bash
uv run scripts/tts_xfyun.py --vcn xiaoyan   # add --force to re-render everything
```
