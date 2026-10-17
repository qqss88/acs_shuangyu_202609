"""Run with: uv run --with pytest pytest scripts"""
from generate_audio import HTML_PATH, clip_id, extract_spoken_texts

SAMPLE = """
  tokens: [
    { char: '熊', py: 'xióng', en: 'bear' },
    { char: '，', py: '', en: 'comma', isPunct: true }
  ],
  rawText: '熊猫很可爱。'
  { hanzi: '熊猫', pinyin: 'xióng māo', example: '熊猫很可爱。' },
  titleZh: '胖的反义词是哪个',
  fullZh: '猴子瘦，跑得快。'
"""


def test_extracts_every_spoken_field_once_in_order() -> None:
    assert extract_spoken_texts(SAMPLE) == [
        "熊猫很可爱。",
        "熊猫",
        "胖的反义词是哪个",
        "猴子瘦，跑得快。",
        "熊",
    ]


def test_skips_punctuation_tokens() -> None:
    assert "，" not in extract_spoken_texts(SAMPLE)


def test_returns_empty_list_when_no_data() -> None:
    assert extract_spoken_texts("<html></html>") == []


def test_clip_id_is_stable_and_voice_specific() -> None:
    assert clip_id("zf_001|熊猫") == clip_id("zf_001|熊猫")
    assert clip_id("zf_001|熊猫") != clip_id("zm_010|熊猫")
    assert len(clip_id("x")) == 12


def test_real_page_covers_all_spoken_sources() -> None:
    texts = extract_spoken_texts(HTML_PATH.read_text(encoding="utf-8"))
    for expected in ["星期天你想去哪儿？", "香蕉", "我给猴子吃香蕉。", "胖的反义词是哪个", "得"]:
        assert expected in texts
    assert not any(t in {"？", "，", "。"} for t in texts)
