# -*- coding: utf-8 -*-
"""깃허브 Actions 에서 실행: _tts_jobs_free/*.json 의 녹음 작업을 **무료 음성**으로 처리해 _tts_out/ 에 저장한다. (2026-11-22)
  영어  → Kokoro-82M (Apache 2.0) 목소리 Heart(af_heart)
  한국어 → MeloTTS Korean (MIT) 여자 목소리 하나
작업 파일 형식은 ElevenLabs 용(tools/tts_gh.py)과 똑같다: {"items":[{"out":"이름","voice":"...","text":"줄 <break time=\"0.8s\" /> 줄 ..."}]}
  voice 가 ElevenLabs 한국어 목소리(Seulki)·"melo:KR" 이면 한국어, 그 밖(Marcus·"kokoro:af_heart" 등)은 영어.
결과도 똑같은 모양: _tts_out/<이름>.mp3 + <이름>.json(text·글자별 시각 alignment) → home2 의 autotts.py attach 가 그대로 붙인다.
줄마다 따로 만들어 쉼(break)으로 이어 붙이므로 줄 시작·끝 시각을 정확히 안다. 크레딧·키 필요 없음."""
import os,re,json,glob,shutil,subprocess,urllib.request
import numpy as np, soundfile as sf
OUT='_tts_out'; JOBS='_tts_jobs_free'; os.makedirs(OUT,exist_ok=True); os.makedirs(JOBS+'/done',exist_ok=True)
KR_VOICES={'ksaI0TCD9BstzEzlxj4q','melo:KR'}
EN_DEFAULT='af_heart'
KDIR=os.path.expanduser('~/.cache/kokoro'); KURL='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
KFILES=['kokoro-v1.0.int8.onnx','voices-v1.0.bin']
BR_RE=re.compile(r'\s*<break time="([\d.]+)s"\s*/>\s*')
_E={}

def kokoro():
    if 'k' not in _E:
        os.makedirs(KDIR,exist_ok=True)
        for f in KFILES:
            p=os.path.join(KDIR,f)
            if not os.path.exists(p): print('  모델 받기',f); urllib.request.urlretrieve(KURL+f,p+'.part'); os.replace(p+'.part',p)
        from kokoro_onnx import Kokoro; _E['k']=Kokoro(*[os.path.join(KDIR,f) for f in KFILES])
    return _E['k']

def melo():
    if 'm' not in _E:
        from melo.api import TTS; m=TTS(language='KR',device='cpu'); _E['m']=(m,m.hps.data.spk2id['KR'])
    return _E['m']

def synth(line,voice,speed):
    if voice in KR_VOICES:
        m,spk=melo(); a=m.tts_to_file(line,spk,None,speed=speed,quiet=True); return np.asarray(a,dtype=np.float32),m.hps.data.sampling_rate
    v=voice.split(':',1)[1] if voice.startswith('kokoro:') else EN_DEFAULT
    a,sr=kokoro().create(line,voice=v,speed=speed,lang='en-gb' if v[:1]=='b' else 'en-us'); return np.asarray(a,dtype=np.float32),sr

def trim(a,sr):
    nz=np.flatnonzero(np.abs(a)>0.01)
    return a[max(0,nz[0]-int(.03*sr)):min(len(a),nz[-1]+int(.06*sr))] if len(nz) else a

def record(it):
    text=it['text']; voice=it.get('voice',''); speed=float(it.get('speed',1.0))
    pieces=BR_RE.split(text)                       # [줄, 쉼초, 줄, 쉼초, 줄 ...]
    lines=pieces[0::2]; gaps=[float(g) for g in pieces[1::2]]
    seps=[m.group(0) for m in BR_RE.finditer(text)]
    sr=None; parts=[]; spans=[]; t=0.0
    for i,ln in enumerate(lines):
        a,r=synth(ln.strip(),voice,speed); a=trim(a,r)
        # 빈 소리 막기(2026-11-22: onnxruntime 1.23에서 줄 대부분이 0초로 나왔는데 그대로 올라감) — 글자 수에 비해 너무 짧으면 멈춤
        nch=len(re.sub(r'[^0-9A-Za-z가-힣]','',ln))
        if nch>=3 and len(a)/r < max(0.25, nch/40): raise SystemExit(f"!! 소리가 너무 짧음 {len(a)/r:.2f}초 · {nch}글자: {ln[:60]} — 설치된 onnxruntime 판 확인")
        if sr is None: sr=r
        if i: g=np.zeros(int(gaps[i-1]*sr),dtype=np.float32); parts.append(g); t+=len(g)/sr
        spans.append((t,t+len(a)/sr)); parts.append(a); t+=len(a)/sr
    # 글자별 시각 (ElevenLabs 모양). 줄 안은 고르게 나누고, 쉼 표시 글자는 쉼 구간
    st=[]; en=[]
    for i,ln in enumerate(lines):
        if i:
            for _ in seps[i-1]: st.append(round(spans[i-1][1],3)); en.append(round(spans[i][0],3))
        a,b=spans[i]; n=max(1,len(ln))
        for j in range(len(ln)): st.append(round(a+(b-a)*j/n,3)); en.append(round(a+(b-a)*(j+1)/n,3))
    # autotts.cues_of 는 첫 글자(공백 아닌) 시작-0.06, 끝 글자 끝+0.12 를 쓰므로 미리 맞춰 둠
    pos=0
    for i,ln in enumerate(lines):
        if i: pos+=len(seps[i-1])
        a=pos
        while a<pos+len(ln)-1 and text[a]==' ': a+=1
        st[a]=round(spans[i][0]+.06,3); en[pos+len(ln)-1]=round(max(spans[i][0],spans[i][1]-.12),3); pos+=len(ln)
    assert len(st)==len(text),(len(st),len(text))
    wav=f"{OUT}/{it['out']}.wav"; sf.write(wav,np.concatenate(parts),sr)
    subprocess.run(['ffmpeg','-v','error','-y','-i',wav,'-ac','1','-b:a','128k',f"{OUT}/{it['out']}.mp3"],check=True); os.remove(wav)
    json.dump(dict(text=text,alignment=dict(characters=list(text),character_start_times_seconds=st,character_end_times_seconds=en),
                   headers={'engine':'melo-KR' if voice in KR_VOICES else 'kokoro-82M','voice':voice,'character-cost':0}),
              open(f"{OUT}/{it['out']}.json",'w',encoding='utf-8'),ensure_ascii=False)
    return t,len(lines)

if __name__=='__main__':
    for jf in sorted(glob.glob(JOBS+'/*.json')):
        J=json.load(open(jf,encoding='utf-8')); print('job',jf)
        for it in J.get('items',[]):
            if os.path.exists(f"{OUT}/{it['out']}.mp3") or os.path.exists(f"{OUT}/{it['out']}.json"): print('  skip',it['out']); continue
            sec,n=record(it); print(f"  ok {it['out']} {n}줄 {sec:.1f}초")
        shutil.move(jf,JOBS+'/done/'+os.path.basename(jf))
