# 부서진 마천루 · 전투 실험실

개발지침 **0.2**의 A~C 단계용 Windows 로컬 2인 시제품입니다. 5개 발판에서 이동·점프·밀치기·회피·추락 후 재착지를 시험할 수 있습니다. 기준안 A대로 서로 통과하며, 실험실에서는 하얀 막이 꺼져 있습니다.

**현재 단계:** 전투 구현 및 자동 판정 검증 완료, 사람의 가장자리 압박 실험 대기. 전체 수직 맵·분할 카메라·온라인은 아직 구현하지 않았습니다. 시뮬레이션에는 막과 승패 규칙을 미리 분리 구현했고 자동 검증했지만, D 단계의 종반 플레이 검증을 완료했다는 뜻은 아닙니다.

## 실행

Windows 실행 빌드: `dist/BrokenSkyscraper/BrokenSkyscraper.exe`

배포할 때는 **BrokenSkyscraper 폴더 전체**를 복사하세요. `_internal` 폴더가 필요합니다. Python 설치 없이 실행할 수 있습니다.

소스 실행은 Python 3.12에서 다음 명령을 사용합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe main.py
```

처음 실행하면 3초 카운트다운 후 시작합니다. 같은 키보드의 동시 입력 제한은 장치마다 다릅니다. SDL에서 지원하는 표준 게임패드 2개를 연결하면 연결 순서대로 P1/P2에 배정합니다. 키보드와 게임패드는 같은 슬롯을 함께 제어할 수 있습니다.

## 기본 조작

| 행동 | P1 키보드 | P2 키보드 | 표준 게임패드 |
|---|---|---|---|
| 이동 | A / D | ← / → | 왼쪽 스틱 / 십자키 |
| 점프 | W | ↑ | A (아래쪽 버튼) |
| 발판 내려가기 | S + W | ↓ + ↑ | 아래 + A |
| 밀치기 | F | K | X (왼쪽 버튼) |
| 회피 | G | L | B (오른쪽 버튼) |
| 일시정지 | Esc | Esc | Start |

버튼 표기는 Xbox 배열 기준입니다. F2에서 두 플레이어의 키를 순서대로 변경할 수 있습니다. 창 포커스나 연결된 게임패드를 잃으면 일시정지합니다. 재연결 후 Esc/Start로 계속하세요. 실물 게임패드 2개 동시 입력은 아직 현장 검증하지 않았습니다.

## 실험 도구

| 키 | 기능 |
|---|---|
| R | 같은 조건으로 재경기 |
| F1 | 판정·좌표·속도·상태 나이·지지 발판 보기 |
| F2 | 키 재지정; Esc로 취소 |
| F3 | 좌우 반전 후 새 경기 |
| F4 | P2의 중앙 방향 초기 속도 6 설정 후 새 경기 |
| F5 | P2 사람 조작 / 정지 표적 / 밀치기 반복 / 중앙 복귀 순환 |
| F7 | 현재 입력·이벤트·스냅샷 기록 저장 |
| F8 | 최근 저장 기록 검증 후 화면 재생 |
| F10 | 효과음 켜기/끄기 |
| F11 | 화면 흔들림 켜기/끄기 |
| N | 디버그 + 일시정지 중 한 틱 진행 |
| 클릭 / Shift+클릭 | 디버그 + 일시정지 중 P1 / P2 위치 이동 |
| 1 / 2 | 디버그 + 일시정지 중 해당 체력 10 감소 |

설정과 기록은 `%LOCALAPPDATA%/BrokenSkyscraper`에 저장합니다. 재경기는 이전 입력·공격 기록을 초기화합니다. 디버그 위치·체력 변경은 그 상태부터 새 기록을 시작합니다. 기록은 최대 20개, 합계 약 40MB로 제한합니다. 기록은 사람이 자유 조작한 경기와 스크립트 탐침을 메타데이터로 구분합니다.

## 검증 및 빌드

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tools.combat_experiment
.\.venv\Scripts\python.exe main.py --smoke 240 --screenshot artifacts/combat-lab.png
.\.venv\Scripts\python.exe main.py --verify-replay path/to/record.json
powershell -ExecutionPolicy Bypass -File build.ps1
```

`--smoke`는 가상 디스플레이에서 렌더링·시뮬레이션·기록 재생을 확인합니다. 실물 화면, 컨트롤러, 1080p 성능 인증을 대신하지 않습니다.

## 개발 자료

- `docs/development-guideline-v0.2.md`: 제공된 지침 원본 사본
- `docs/development-status.md`: 브랜치 범위·작업 단계·미완료 조건
- `docs/validation.md`: 검증 결과와 한계
- `docs/scripted-pressure.md`: 자동 압박 탐침 결과
- `docs/playtest-sheet.md`: 사람 대상 실험 기록 양식
- `config/`: 고정 경기·캐릭터 수치
- `maps/combat_lab.json`: 지침 6.4절의 발판 5개
- `src/simulation/`: pygame을 사용하지 않는 판정·물리 코드
- `src/input/`, `src/presentation/`: 장치 입력과 화면 표시

## 알려진 한계

- 자동 탐침에서 중앙 무피격 복귀가 90~100%였습니다. 고정 공격 스크립트 결과이며 실제 대전의 방어 우위를 증명하지 않습니다. 자유 견제·회피 후 반격을 사람이 시험해야 합니다.
- 실험실에는 고정 공동 카메라를 사용합니다. 모든 발판이 화면에 들어오며 전체 수직 맵용 카메라는 다음 단계입니다.
- 사용자 설정 게임패드 버튼 재지정, 비표준 조이스틱, 플랫폼별 패키징은 아직 지원하지 않습니다.
- 새 빌드에서 옛 기록의 재현은 보장하지 않습니다. 설정·맵 해시와 매 틱 상태 해시로 차이를 탐지합니다.
- 이 빌드는 판매·배포용 완성 게임이 아닙니다. 3쌍·18경기의 사용자 검증, 최하층 실험, 기준 PC 성능 측정이 남아 있습니다.
