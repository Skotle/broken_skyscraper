import tempfile
import unittest
from pathlib import Path
from src.config import load_config
from src.simulation import Match, InputFrame as I
from src.replay import Recorder, verify, read


class ReplayTests(unittest.TestCase):
    def test_reports_first_divergent_tick_between_checkpoints(self):
        m=Match(*load_config(),countdown=False)
        recorder=Recorder(m)
        for _ in range(15):
            m.step()
            recorder.append([I(),I()],m)
        recorder.record['frames'][7][0]['move']=1
        result=verify(recorder.record)
        self.assertEqual(result,{'ok':False,'firstDivergentStep':7,'tick':8})

    def test_record_save_replay_and_corruption(self):
        m=Match(*load_config())
        recorder=Recorder(m)
        for t in range(360):
            inputs=[I(move=.5 if t%80<40 else -.5,attack=t%47==0),I(jump=t%61==0,dodge=t%70==0)]
            m.step(inputs)
            recorder.append(inputs,m)
        self.assertTrue(verify(recorder.record)['ok'])
        with tempfile.TemporaryDirectory() as folder:
            path=recorder.save(folder)
            self.assertTrue(verify(read(path))['ok'])
        recorder.record['checkpoints']['240']['players'][0]['x']+=1
        result=verify(recorder.record)
        self.assertFalse(result['ok'])
        self.assertEqual(result['firstDivergentCheckpoint'],240)

    def test_30_60_144_render_frames_do_not_change_simulation(self):
        snapshots=[]
        for fps in (30,60,144):
            m=Match(*load_config(),countdown=False)
            accumulator=0
            for _ in range(fps*4):
                accumulator+=1/fps
                while accumulator+1e-12>=1/60:
                    t=m.tick
                    m.step([I(move=1 if t<20 else -1 if t<40 else 0,attack=t%37==0),I(dodge=t%63==0)])
                    accumulator-=1/60
            snapshots.append(m.snapshot())
        self.assertEqual(snapshots[0],snapshots[1])
        self.assertEqual(snapshots[1],snapshots[2])

    def test_logs_are_bounded_without_touching_other_files(self):
        with tempfile.TemporaryDirectory() as folder:
            extra=Path(folder)/'user-notes.json'
            extra.write_text('{}')
            for _ in range(22):
                r=Recorder(Match(*load_config()))
                r.save(folder)
            self.assertTrue(extra.exists())
            self.assertEqual(len(list(Path(folder).glob('*.json'))),21)
