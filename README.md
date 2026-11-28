# seoro-audio2 — SEORO 음원 저장소 (2번째)

0505.co.kr(home2 저장소)의 교재 페이지가 쓰는 음원만 모아 둔 저장소. GitHub Pages로 공개되며,
(2026-11-06 seoro-audio가 1GB에 가까워져 만든 2번째 저장소. 이미 녹음이 붙은 쪽은 seoro-audio 주소를 그대로 쓰고, 새 녹음만 여기로 온다. home2 `_seoro_tools/audiorepo.py`의 REPO_NAME = seoro-audio2)
교재 HTML은 `https://nmyway77.github.io/seoro-audio2/audio/<파일>.mp3` 주소로 음원을 불러온다.
(home2 저장소의 1GB 한도와 별개로 이 저장소가 1GB를 따로 쓴다. 다 차면 `seoro-audio3`을 만들어 같은 방식으로 잇는다.)

## 폴더
- `audio/` — 교재 페이지가 실제로 재생하는 완성 음원 (48kbps 모노). 이름: `SEORO-CLASSICS_GR<레벨>_<제목>_p<쪽>_<fen|cen|ckr|...>.mp3`
  - `fen` 영어 문장 원어민 녹음, `cen` 영어 어구 더빙, `ckr` 한국어 어구 더빙
- `_tts_jobs/` — ElevenLabs 녹음 요청(JSON). 여기에 `*.json`이 푸시되면 Actions가 녹음한다.
  - `_tts_jobs/pending/` — 아직 녹음하지 않을 요청(크레딧 확인 뒤 상위 폴더로 옮기면 녹음 시작)
  - `_tts_jobs/done/` — 처리 끝난 요청
- `_tts_out/` — Actions가 받아 온 원본 mp3(128k) + 글자별 시각(json). home2의 `_seoro_tools/autotts.py attach`가 이걸 읽어 `audio/`에 완성 음원을 만든다.
- `tools/tts_gh.py` — Actions에서 실행되는 녹음 스크립트. 키는 저장소 Secrets `ELEVENLABS_API_KEY`.
- `_tts_jobs_free/` — **무료 음성** 녹음 요청(2026-11-22). 여기에 `*.json`이 푸시되면 `tts-free` Actions가 녹음한다(크레딧·키 없음). 처리 끝난 요청은 `_tts_jobs_free/done/`
- `tools/tts_free.py` — 무료 녹음 스크립트. 영어 = Kokoro-82M 목소리 Heart(af_heart). 결과는 ElevenLabs와 같은 모양으로 `_tts_out/`에 저장 → `autotts.py attach`가 그대로 붙인다.
  - 정한 것(2026-11-22): 새로 녹음하는 책의 영어 문장·영어 어구만 무료(Heart). 한국어 어구는 ElevenLabs Seulki 유지. home2: `autotts.py make <mod> '' KR_chunk free`(영어 2종 무료) + `autotts.py make <mod> '' EN_full,EN_chunk`(한국어만 ElevenLabs, 크레딧 보고·승인 후)

## 흐름
1. home2: `python3 _seoro_tools/autotts.py make <mod>` → 이 저장소 `_tts_jobs/<mod>.json` 생성
2. 이 저장소 커밋·푸시 → Actions 녹음 → `_tts_out/`에 결과 커밋 (https://github.com/nmyway77/seoro-audio2/actions)
3. home2: `python3 _seoro_tools/autotts.py attach <mod>` → 이 저장소 `audio/`에 완성 음원, home2 쪽 HTML에 주소·시각 반영
4. 두 저장소 모두 커밋·푸시

## 용량 관리 (2026-11-28)
- 사이트(Pages)는 main 가지를 그대로 공개한다. **main에는 `audio/`(사이트 음원)와 도구·요청 파일만** 둔다.
- 녹음 결과물(`_tts_out/`: 처음 만든 mp3 + 글자별 시각 json)은 **`tts-out` 가지**에만 저장된다(두 녹음 Actions가 자동으로). 사이트에는 안 올라간다.
- 쪽에 붙일 때(home2 `attach`) 결과물이 필요하면: `python3 _seoro_tools/audiorepo.py pull-out` (tts-out 가지의 `_tts_out`을 받아 이 폴더에 풀어 놓음, main에는 올라가지 않음 — `.gitignore`).
