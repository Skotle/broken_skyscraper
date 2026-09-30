import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pygame as pg
from src.input.devices import Devices


class InputTests(unittest.TestCase):
    def setUp(self):
        pg.init()
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'LOCALAPPDATA':self.temp.name})
        self.env.start()
        self.controllers=patch('src.input.devices.controller.get_count',return_value=0)
        self.controllers.start()
        self.d=Devices()

    def tearDown(self):
        self.controllers.stop()
        self.env.stop()
        self.temp.cleanup()
        pg.quit()

    def key(self,key,down=True):
        self.d.event(pg.event.Event(pg.KEYDOWN if down else pg.KEYUP,key=key))

    def test_two_keyboard_slots_and_single_press_edges(self):
        for key in (pg.K_a,pg.K_f,pg.K_RIGHT,pg.K_l):
            self.key(key)
        a,b=self.d.consume()
        self.assertEqual((a.move,a.attack,b.move,b.dodge),(-1,True,1,True))
        self.key(pg.K_f)  # OS auto-repeat is not another press.
        a,b=self.d.consume()
        self.assertEqual((a.attack,b.dodge),(False,False))
        self.assertEqual((a.move,b.move),(-1,1))

    def test_down_jump_normalizes_to_drop_only(self):
        self.key(pg.K_s)
        self.key(pg.K_w)
        a,_=self.d.consume()
        self.assertTrue(a.drop)
        self.assertFalse(a.jump)

    def test_focus_loss_clears_held_inputs(self):
        self.key(pg.K_a)
        self.d.event(pg.event.Event(pg.WINDOWFOCUSLOST))
        self.assertEqual(self.d.consume()[0].move,0)

    def test_keyboard_bindings_round_trip_and_corruption_recovery(self):
        self.d.bindings[0]['attack']='q'
        self.d.save()
        loaded=Devices()
        self.assertEqual(loaded.bindings[0]['attack'],'q')
        loaded.settings_path.write_text('{',encoding='utf-8')
        restored=Devices()
        self.assertTrue(restored.notice)
        self.assertEqual(restored.bindings[0]['attack'],'f')

    def test_controller_axes_buttons_and_stable_slots_on_disconnect(self):
        pad=MagicMock()
        pad.attached.return_value=True
        pad.get_axis.side_effect=lambda axis: 32767 if axis==pg.CONTROLLER_AXIS_LEFTX else 0
        pad.get_button.side_effect=lambda button: button==pg.CONTROLLER_BUTTON_A
        self.d.pads[1]=pad
        self.d.poll()
        a,b=self.d.consume()
        self.assertEqual((a.move,b.move,b.jump),(0,1,True))
        self.d.poll()
        self.assertFalse(self.d.consume()[1].jump)
        pad.attached.return_value=False
        self.assertTrue(self.d.refresh())
        self.assertIsNone(self.d.pads[1])
        self.assertFalse(self.d.consume()[1].jump)

    def test_first_controller_disconnect_does_not_reassign_second(self):
        first,second=MagicMock(),MagicMock()
        first.attached.return_value=False
        second.attached.return_value=True
        self.d.pads=[first,second]
        self.assertTrue(self.d.refresh())
        self.assertIsNone(self.d.pads[0])
        self.assertIs(self.d.pads[1],second)


if __name__=='__main__':
    unittest.main()
