import streamlit as st
import os
import datetime
import warnings
from yt_dlp import YoutubeDL
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip
import moviepy.video.fx as vfx
import moviepy.audio.fx as afx

warnings.filterwarnings("ignore")

st.set_page_config(page_title="AI 영상 편집기 (Cloud)", page_icon="🎬", layout="wide")
st.title("🎬 스마트 영상 편집기 (Cloud Edition)")

def to_seconds(t_str):
    try:
        t_str = t_str.strip()
        if ':' in t_str:
            p = t_str.split(':')
            if len(p) == 2: return int(p[0]) * 60 + int(p[1])
            elif len(p) == 3: return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])
        return int(t_str)
    except: return 0

with st.sidebar:
    st.header("⚙️ 편집 설정")
    source = st.radio("영상 소스", ["유튜브 URL", "파일 업로드"])
    edit_mode = st.radio("작업 종류", ["선택 구간 추출 (Keep)", "선택 구간 삭제 (Cut)"])

col1, col2 = st.columns(2)
with col1:
    v_in = st.text_input("YouTube 링크") if source == "유튜브 URL" else st.file_uploader("영상 파일", type=["mp4", "mov"])
with col2:
    bgm = st.file_uploader("BGM (MP3)", type=["mp3"])
    vol = st.slider("BGM 볼륨", 0.0, 1.0, 0.3)

if edit_mode == "선택 구간 추출 (Keep)":
    iv_raw = st.text_input("✨ 추출구간설정 (남길 부분)", placeholder="예: 10-20 40-50")
else:
    iv_raw = st.text_input("✂️ 삭제구간설정 (버릴 부분)", placeholder="예: 0-10 1:00-1:10")

if st.button("🚀 편집 시작", use_container_width=True):
    if v_in and iv_raw:
        try:
            with st.spinner("처리 중..."):
                tmp_v = "temp_in.mp4"
                if source == "유튜브 URL":
                    with YoutubeDL({'format':'best[ext=mp4]','outtmpl':tmp_v,'overwrites':True}) as ydl:
                        ydl.download([v_in])
                else:
                    with open(tmp_v, "wb") as f: f.write(v_in.read())
                
                video = VideoFileClip(tmp_v)
                dur = video.duration
                ivs = [tuple(map(to_seconds, p.split('-'))) for p in iv_raw.split() if '-' in p]
                f_ivs = sorted(ivs) if edit_mode == "선택 구간 추출 (Keep)" else []
                if edit_mode == "선택 구간 삭제 (Cut)":
                    curr = 0
                    for s, e in sorted(ivs):
                        if s > curr: f_ivs.append((curr, s))
                        curr = max(curr, e)
                    if curr < dur: f_ivs.append((curr, dur))
                
                clips = [video.subclipped(s, min(e, dur)) for s, e in f_ivs if s < dur]
                if clips:
                    final = concatenate_videoclips(clips, method="compose")
                    if bgm:
                        with open("temp_a.mp3", "wb") as f: f.write(bgm.read())
                        audio = AudioFileClip("temp_a.mp3").multiply_volume(vol)
                        audio = audio.fx(afx.audio_loop, duration=final.duration) if audio.duration < final.duration else audio.subclipped(0, final.duration)
                        final = final.without_audio().with_audio(audio)
                    
                    out = f"result_{datetime.datetime.now().strftime('%H%M%S')}.mp4"
                    final.write_videofile(out, codec="libx264", audio_codec="aac")
                    st.video(out)
                    with open(out, "rb") as f: st.download_button("📥 다운로드", f, file_name=out)
                video.close()
        except Exception as e: st.error(f"오류: {e}")