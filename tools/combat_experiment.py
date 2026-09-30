"""Scripted probes, explicitly not a human pressure/fun validation."""
import argparse
from copy import deepcopy
from pathlib import Path
from src.config import load_config
from src.simulation import Match, InputFrame as I
from src.replay import Recorder, verify
from src.storage import atomic_json


def trial(mirror, moving, swapped, attack_delay, save_folder=None):
    m=Match(*load_config(),countdown=False,mirror=mirror,moving=moving)
    if swapped:
        m.players.reverse()
        for index,p in enumerate(m.players):
            p.id=index+1
    attacker=1 if swapped else 0
    defender=1-attacker
    rec=Recorder(m,{'experiment':'scripted-pressure-probe','humanValidated':False,'mirror':mirror,'moving':moving,'swapped':swapped,'attackDelay':attack_delay})
    escaped_at=None
    hit_before_escape=False
    hit_count=0
    for t in range(120):
        p=m.players[defender]
        inputs=[I(),I()]
        inputs[attacker]=I(attack=t==attack_delay)
        inputs[defender]=I(move=-1 if p.x>.3 else 1 if p.x<-.3 else 0)
        m.step(inputs)
        rec.append(inputs,m)
        incoming=[e for e in m.events if e['type']=='hit' and e['target']==p.id]
        hit_count+=len(incoming)
        if escaped_at is None:
            hit_before_escape |= bool(incoming)
            if abs(p.x)<=.3:
                escaped_at=t
        if m.result:
            break
    if not verify(rec.record)['ok']:
        raise RuntimeError('Probe input replay diverged')
    if save_folder and attack_delay in (0,8):
        rec.save(save_folder)
    return {'mirror':mirror,'moving':moving,'swapped':swapped,'attackDelay':attack_delay,
            'escapeTick':escaped_at,'escapedUnhit':escaped_at is not None and not hit_before_escape,
            'hits':hit_count,'defenderHeight':p.y,'defenderEliminated':p.eliminated}


def run(output):
    results=[trial(mirror,moving,swapped,delay,output/'replays')
             for mirror in (False,True) for moving in (False,True) for swapped in (False,True) for delay in range(0,20,2)]
    groups=[]
    for mirror in (False,True):
        for moving in (False,True):
            for swapped in (False,True):
                rows=[r for r in results if (r['mirror'],r['moving'],r['swapped'])==(mirror,moving,swapped)]
                rate=sum(r['escapedUnhit'] for r in rows)/len(rows)
                groups.append({'mirror':mirror,'moving':moving,'swapped':swapped,'trials':len(rows),'unhitEscapeRate':rate,'reviewFlag':rate>=.8})
    report={'humanValidated':False,'method':'Defender moves toward center only. Attacker stays still and presses attack once at ticks 0,2,...18. These are deterministic timing probes, not independent human trials.','groups':groups,'trials':results}
    atomic_json(output/'scripted-pressure.json',report)
    lines=['# 전투 실험 A — 스크립트 탐침','',
           '사람의 자유 대응이나 재미 검증 결과가 아니다. 공격자는 정지한 채 0~18틱의 서로 다른 시점에 한 번 공격한다. 방어자는 중앙으로 이동만 한다. 같은 입력 재생도 각 실행에서 검증했다.', '',
           '| 좌우 반전 | 초기 속도 | 슬롯 교대 | 무피격 중앙 복귀 / 10 | 80% 탐지 |','|---|---|---|---|---|']
    for g in groups:
        lines.append(f"| {g['mirror']} | {'6' if g['moving'] else '0'} | {g['swapped']} | {g['unhitEscapeRate']*10:.0f} | {'재검토 후보' if g['reviewFlag'] else '-'} |")
    lines += ['', '## 해석 한계','', '이 결과만으로 공격 범위·준비 시간·몸체 통과 규칙을 변경하지 않는다. 고정된 공격 스크립트는 공격자의 자유로운 견제와 반격을 대표하지 않는다. 0.2 지침 6.4절의 역할 교대, 자유 대응, 회피 후 반격 영상은 아직 필요하다. 전체 수직 맵 확장 조건은 미충족이다.']
    (output/'scripted-pressure.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return groups


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='artifacts/experiments')
    args=parser.parse_args()
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    print(run(out))
