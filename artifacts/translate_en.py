from pathlib import Path

pairs = [
('부서진 마천루 · 전투 실험실','Broken Skyscraper - Combat Lab'),
('창을 벗어나 일시정지했습니다 · ESC 계속하기','Focus lost - ESC to resume'),
('게임패드 연결 해제 · 재연결 후 ESC / START','Controller disconnected - reconnect, then ESC / START'),
('입력 기록 저장 완료 · F8 재생','Replay saved - F8 to play'),
('기록 검증 통과 · 재생 시작','Replay verified - playback started'),
('기록 불일치: ','Replay mismatch: '),
('효과음 켜짐','Sound on'),('음소거','Mute'),
('화면 흔들림 ','Screen shake '),('켜짐','on'),('꺼짐','off'),
('디버그 상태에서 새 기록 시작 · 1/2: 해당 체력 -10','New debug recording - 1/2: reduce player health by 10'),
('메뉴·디버그용 키는 사용할 수 없습니다.','This key is reserved for menus or debug controls.'),
('앞에서 지정한 키와 겹칩니다. 다른 키를 선택하세요.','Key already assigned. Choose another key.'),
('두 플레이어의 키 설정을 저장했습니다.','Key bindings saved for both players.'),
('재생 완료 · R 새 경기','Replay finished - R for a new match'),
('경기 결과와 입력 기록을 자동 저장했습니다.','Match result and replay saved automatically.'),
('실행 중 오류가 발생했습니다.','An error occurred. See the log:'),
('설정 파일을 읽을 수 없어 기본 조작으로 복구했습니다.','Could not read settings. Default controls restored.'),
('전투 실험실 · 기준안 A','Combat Lab - Baseline A'),
('공격 준비','Windup'),('공격 후딜','Recovery'),('피격 경직','Hitstun'),
('최하단 추락','Fell below the tower'),('하얀 막 · 체력 소진','Health depleted by the veil'),
('추락 및 체력 소진','Fall and health depleted'),('시간 종료 · 높이 우위','Time up - higher position'),
('높이 동률 · 체력 우위','Height tied - more health'),('동시 탈락','Both players eliminated'),('높이와 체력 동률','Height and health tied'),
('추락 판정선','FALL BOUNDARY'),('부서진 마천루','Broken Skyscraper'),
('5개 발판 · 통과 실험 A','5 platforms · Baseline A'),('회피 준비','Dodge ready'),
('전투 실험','Combat Lab'),('막 비활성 · 120초','Veil disabled · 120 seconds'),
('재시작  R','Restart  R'),('계속하기  ESC','Resume  ESC'),('일시정지  ESC','Pause  ESC'),
('좌우 반전  F3','Mirror  F3'),('P2 이동 시작  F4','P2 moving start  F4'),
('사람 조작','Human'),('정지 표적','Target'),('밀치기 반복','Repeat push'),('중앙 복귀','Return to center'),
('게임패드 {app.devices.connected_count}/2 연결','Controllers: {app.devices.connected_count}/2'),
('A 점프 · X 밀치기 · B 회피','A Jump · X Push · B Dodge'),('↓ + A 발판 내려가기','Down + A: drop through'),
('F1 판정 보기 · F2 키 변경','F1 Debug · F2 Remap keys'),
('F7 기록 저장   F8 기록 재생','F7 Save replay   F8 Play replay'),('F10 Mute   F11 흔들림','F10 Mute   F11 Screen shake'),
('적체 {app.backlog}','Backlog {app.backlog}'),("지지 {p.support","Support {p.support"),
('정지 중 N: 1틱 / 클릭: P1 이동 / Shift+클릭: P2','Paused: N step / Click P1 / Shift+click P2'),
('이동 · 점프 · 밀치기 · 회피','Move · Jump · Push · Dodge'),
('무승부','Draw'),('} 승리','} wins'),('R 재경기','R rematch'),
('ESC 계속하기 · R 재시작','ESC resume · R restart'),('일시정지','Paused'),
('입력 기록 재생 중','Replay playback'),('새 키를 누르세요 · ESC 취소 (총 12개 행동)','Press a key · ESC cancel (12 bindings)'),
('} 이동   ','} Move   '),('} 점프   ','} Jump   '),('}+점프 하강   ','}+Jump Drop   '),
('준비','Ready'),('밀치기','Push'),('회피','Dodge'),('탈락','Eliminated'),('체력','Health'),
('malgungothic,malgun gothic,notosanscjkkr,arial','segoeui,arial'),
]
for filename in ['src/app.py','src/input/devices.py','src/presentation/screen.py','maps/combat_lab.json']:
    p=Path(filename)
    text=p.read_text(encoding='utf-8')
    for before,after in pairs:
        text=text.replace(before,after)
    p.write_text(text,encoding='utf-8')
