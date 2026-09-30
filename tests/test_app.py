import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import tempfile
import unittest
from unittest.mock import patch
import pygame as pg
from src.app import App


class AppIntegrationTests(unittest.TestCase):
    def test_input_through_application_and_rematch(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{'LOCALAPPDATA':folder}):
            app=App(smoke=True)
            for _ in range(180):
                app.step()
            pg.event.post(pg.event.Event(pg.KEYDOWN,key=pg.K_f))
            pg.event.post(pg.event.Event(pg.KEYDOWN,key=pg.K_l))
            app.events()
            app.step()
            self.assertEqual([p.action for p in app.match.players],['AttackStartup','Dodge'])
            for _ in range(15):
                app.step()
            self.assertEqual(len([e for e in app.recorder.record['events'] if e['type']=='hit']),1)
            app.command('pause')
            before=app.match.snapshot()
            self.assertTrue(app.match.paused)
            app.renderer.draw(app)
            self.assertEqual(before,app.match.snapshot())
            app.command('restart')
            self.assertEqual(app.match.tick,0)
            self.assertEqual(len(app.recorder.record['frames']),0)
            self.assertFalse(app.devices.held)
            self.assertEqual(app.renderer.last_hit,-100)
            pg.quit()
