import unittest
from copy import deepcopy

from src.config import load_config, validate
from src.simulation import Match, InputFrame as I
from src.simulation.actions import begin_actions, collect_hits, apply_hits, advance_action
from src.simulation.model import Player
from src.simulation.motor import landing_candidate, move_player
from src.simulation.match import evaluate_result, hazard_at


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.r,self.c,self.w = load_config()
        self.m = Match(self.r,self.c,self.w,countdown=False)
        self.a,self.b = self.m.players

    def active(self,p):
        p.action,p.age = 'AttackActive',8
        p.attack_sequence += 1
        p.attack_facing = p.facing

    def pair(self):
        self.a.x,self.b.x = -.5,.5
        self.a.facing,self.b.facing = 1,-1

    def test_R01_one_hit_per_attack(self):
        self.pair()
        self.active(self.a)
        hits = []
        for _ in range(3):
            candidates = collect_hits(self.m.players,self.c)
            hits.extend(apply_hits(self.m.players,candidates,0,self.c))
        self.assertEqual(len(hits),1)

    def test_R02_trade_is_independent_of_slot_order(self):
        self.pair()
        for p in self.m.players:
            self.active(p)
        players = deepcopy(self.m.players)
        self.m.step()
        self.assertEqual(len(self.m.events),2)
        self.assertEqual([p.vx for p in self.m.players],[-9,9])
        reverse = players[::-1]
        apply_hits(reverse,collect_hits(reverse,self.c),0,self.c)
        self.assertEqual([(p.id,p.vx,p.hitstun_until) for p in self.m.players],[(p.id,p.vx,p.hitstun_until) for p in reverse[::-1]])

    def test_R03_R04_invulnerability_boundary(self):
        self.pair()
        self.active(self.a)
        self.b.action = 'Dodge'
        for age,count in ((8,0),(9,1)):
            with self.subTest(age=age):
                self.b.age = age
                self.assertEqual(len(collect_hits(self.m.players,self.c)),count)
        self.assertEqual(self.a.hit_targets,[])

    def expose(self):
        self.m.world['hazardEnabled'] = True
        self.m.rules['hazardKeyframes'] = [[0,0],[7200,0]]

    def test_R05_dodge_does_not_block_hazard(self):
        self.expose()
        self.m.step([I(dodge=True),I()])
        self.assertEqual(self.a.health,998)

    def test_R06_simultaneous_fall(self):
        for p in self.m.players:
            p.y,p.support = -2,None
        self.m.step()
        self.assertEqual(self.m.result['reason'],'simultaneous')

    def test_R07_mixed_eliminations_same_tick(self):
        self.expose()
        self.a.health = 2
        self.b.y,self.b.support = -2,None
        self.m.step()
        self.assertIsNone(self.m.result['winner'])
        self.assertEqual(self.m.result['reasons'],[['hazard'],['fall']])

    def test_R08_elimination_beats_timeout(self):
        self.m.remaining,self.m.tick = 1,7199
        self.a.y,self.a.support = -2,None
        self.m.step()
        self.assertEqual(self.m.result['winner'],2)
        self.assertEqual(self.m.result['reason'],'fall')

    def test_R09_R10_height_tolerance(self):
        self.a.health,self.b.health = 900,1000
        for gap,winner,reason in ((.09,2,'health'),(.1,2,'health'),(.11,1,'height')):
            with self.subTest(gap=gap):
                self.a.y,self.b.y = 8+gap,8
                self.assertEqual(evaluate_result(self.m.players,0,.1),{'winner':winner,'reason':reason})

    def test_R11_equal_hazard_height_is_safe(self):
        self.m.world['hazardEnabled'] = True
        self.m.rules['hazardKeyframes'] = [[0,8],[7200,8]]
        self.m.step()
        self.assertEqual(self.a.health,1000)

    def test_R12_exposure_accumulates_without_reset(self):
        self.m.world['hazardEnabled'] = True
        for t in range(20):
            h = 7 if t%2==0 else 9
            self.m.rules['hazardKeyframes'] = [[0,h],[7200,h]]
            self.m.step()
        self.assertEqual(self.a.health,980)

    def test_R13_result_is_terminal(self):
        self.m.remaining = 1
        self.m.step()
        before = self.m.snapshot()
        self.m.step([I(attack=True),I(jump=True)])
        self.assertEqual(before,self.m.snapshot())

    def test_R14_fresh_match_resets_all_state(self):
        baseline = Match(self.r,self.c,self.w).snapshot()
        for _ in range(80):
            self.m.step([I(attack=True),I(dodge=True)])
        fresh = Match(self.r,self.c,self.w)
        self.assertEqual(fresh.snapshot(),baseline)
        self.assertEqual(fresh.events,[])

    def test_R15_dodge_cooldown(self):
        begin_actions(self.a,I(dodge=True),0,self.c)
        self.a.action='Neutral'
        begin_actions(self.a,I(dodge=True),59,self.c)
        self.assertEqual(self.a.action,'Neutral')
        begin_actions(self.a,I(dodge=True),60,self.c)
        self.assertEqual(self.a.action,'Dodge')

    def test_R16_exact_14_tick_knockback(self):
        self.m.world.update(left=-100,right=100,bottom=-100)
        self.a.x,self.a.y,self.a.support = 0,50,None
        self.b.x = -80
        apply_hits(self.m.players,[(2,1,1,1)],0,self.c)
        self.m.tick=1
        for _ in range(14):
            self.m.step([I(move=-1),I()])
        self.assertAlmostEqual(self.a.x,2.1,places=10)
        self.assertEqual(self.a.vx,9)
        self.m.step([I(move=-1),I()])
        self.assertAlmostEqual(self.a.vx,8.6)

    def test_R17_landing_does_not_cancel_stun(self):
        self.a.x,self.a.y,self.a.vx,self.a.vy = 0,8.01,9,-5
        self.a.support=None
        self.a.action='Hitstun'
        self.a.hitstun_until=15
        move_player(self.a,I(move=-1),self.w,self.c,1e-5,1)
        self.assertEqual((self.a.support,self.a.vx,self.a.vy,self.a.action),('T0',9,0,'Hitstun'))

    def test_R18_wall_cancels_outward_velocity_only(self):
        self.a.x,self.a.y,self.a.vx,self.a.vy = 8.59,10,9,0
        self.a.support,self.a.action = None,'Hitstun'
        move_player(self.a,I(move=-1),self.w,self.c,1e-5,1)
        self.assertAlmostEqual(self.a.x,8.6)
        self.assertEqual((self.a.vx,self.a.action),(0,'Hitstun'))
        move_player(self.a,I(move=-1),self.w,self.c,1e-5,2)
        self.assertEqual(self.a.vx,0)

    def test_R19_recovery_uses_starting_support(self):
        for grounded,expected in ((True,7.75),(False,8.6)):
            with self.subTest(grounded=grounded):
                p = Player(1,0,8 if grounded else 12,1,vx=9,support='T0' if grounded else None,action='Hitstun',hitstun_until=15)
                begin_actions(p,I(),15,self.c)
                move_player(p,I(),self.w,self.c,1e-5,15)
                self.assertAlmostEqual(p.vx,expected)

    def test_R20_jump_dodge_only_dodges(self):
        self.a.buffer_expires=6
        begin_actions(self.a,I(jump=True,dodge=True),0,self.c)
        self.assertEqual((self.a.action,self.a.vy,self.a.buffer_expires),('Dodge',0,0))

    def test_R21_drop_attack_only_drops(self):
        begin_actions(self.a,I(drop=True,attack=True),0,self.c)
        self.assertEqual((self.a.action,self.a.support,self.a.ignored),('Neutral',None,'T0'))

    def test_R22_drop_dodge_priority(self):
        for ready,state,support in ((0,'Dodge','T0'),(60,'Neutral',None)):
            p=deepcopy(self.a)
            p.dodge_ready=ready
            begin_actions(p,I(drop=True,dodge=True),0,self.c)
            self.assertEqual((p.action,p.support),(state,support))

    def test_R23_final_action_tick_does_not_buffer(self):
        for action,age in (('AttackRecovery',29),('Dodge',14)):
            p=deepcopy(self.a)
            p.action,p.age=action,age
            begin_actions(p,I(jump=True),0,self.c)
            advance_action(p,self.c)
            begin_actions(p,I(),1,self.c)
            self.assertEqual((p.action,p.vy,p.buffer_expires),('Neutral',0,0))

    def test_R24_buffer_landing_boundary_integrated(self):
        for initial_y,expected_jump in ((8.12,True),(8.17,False)):
            m=Match(self.r,self.c,self.w,countdown=False)
            p=m.players[0]
            p.x,p.y,p.support=0,initial_y,None
            m.step([I(jump=True),I()])
            for _ in range(6):
                m.step()
            self.assertEqual(p.vy>0,expected_jump)

    def test_R25_coyote_exact_expiry(self):
        for jump_tick,success in ((6,True),(7,False)):
            m=Match(self.r,self.c,self.w,countdown=False)
            p=m.players[0]
            p.x,p.vx=1.88,6
            m.step([I(move=1),I()])
            self.assertEqual(p.coyote_expires,7)
            while m.tick<jump_tick:
                m.step()
            m.step([I(jump=True),I()])
            self.assertEqual(p.vy>0,success)

    def test_R26_air_jump_attack_clears_buffer(self):
        self.a.support=None
        begin_actions(self.a,I(jump=True,attack=True),0,self.c)
        self.assertEqual((self.a.action,self.a.buffer_expires,self.a.vy),('AttackStartup',0,0))

    def test_R27_unavailable_dodge_allows_jump_attack(self):
        self.a.dodge_ready=1
        begin_actions(self.a,I(jump=True,attack=True,dodge=True),0,self.c)
        self.assertEqual((self.a.action,self.a.vy),('AttackStartup',11))

    def test_R28_endgame_stationary_damage(self):
        w=deepcopy(self.w)
        w['hazardEnabled']=True
        w['platforms']=[{'id':'B','x':0,'y':2,'width':8}]
        w['spawns']=[{'x':-1,'y':2,'facing':1},{'x':1,'y':2,'facing':-1}]
        m=Match(self.r,self.c,w,countdown=False)
        m.tick,m.remaining=6300,900
        m.hazard_y=hazard_at(6300,self.r['hazardKeyframes'])
        self.assertAlmostEqual(m.hazard_y,34/7)
        for _ in range(900):
            m.step()
        self.assertEqual([p.health for p in m.players],[532,532])
        self.assertEqual(m.hazard_y,1)
        self.assertEqual(m.phase,'Result')

    def test_attack_phases_have_exact_duration(self):
        begin_actions(self.a,I(attack=True),0,self.c)
        states=[]
        for _ in range(30):
            states.append(self.a.action)
            advance_action(self.a,self.c)
        self.assertEqual([states.count(s) for s in ('AttackStartup','AttackActive','AttackRecovery')],[8,3,19])
        self.assertEqual(self.a.action,'Neutral')

    def test_attack_direction_locked(self):
        begin_actions(self.a,I(attack=True),0,self.c)
        for tick in range(10):
            begin_actions(self.a,I(move=-1),tick,self.c)
            move_player(self.a,I(move=-1),self.w,self.c,1e-5,tick)
            advance_action(self.a,self.c)
        self.assertEqual(self.a.attack_facing,1)

    def test_drop_ignores_only_support_and_lands_below(self):
        self.a.x=0
        self.m.step([I(drop=True),I()])
        for _ in range(50):
            self.m.step()
        self.assertEqual(self.a.support,'T3')
        self.assertIsNone(self.a.ignored)

    def test_upward_motion_passes_platform(self):
        p=Player(1,0,7.99,1,vy=11)
        move_player(p,I(),self.w,self.c,1e-5,0)
        self.assertGreater(p.y,8)
        self.assertIsNone(p.support)

    def test_pause_freezes_everything(self):
        self.m.step([I(dodge=True),I(attack=True)])
        self.m.paused=True
        before=self.m.snapshot()
        for _ in range(100):
            self.m.step([I(jump=True),I()])
        self.assertEqual(self.m.snapshot(),before)

    def test_countdown_consumes_actions(self):
        m=Match(self.r,self.c,self.w)
        for _ in range(180):
            m.step([I(jump=True,attack=True),I(dodge=True)])
        self.assertEqual(m.phase,'Playing')
        m.step()
        self.assertEqual([p.action for p in m.players],['Neutral','Neutral'])
        self.assertEqual(m.tick,1)


class CollisionTests(unittest.TestCase):
    def setUp(self):
        self.f={'id':'a','x':.5,'y':0,'width':1}

    def test_C01_crossing_overlap_not_final_overlap(self):
        self.assertEqual(landing_candidate((-.5,1),(1.5,-1),self.f),(.5,.5))

    def test_C02_final_overlap_does_not_create_landing(self):
        self.assertIsNone(landing_candidate((-2,1),(.5,-1),self.f))

    def test_C03_exact_corner_is_not_support(self):
        self.assertIsNone(landing_candidate((-.4,1),(-.4,-1),self.f))

    def test_C04_earliest_platform_and_id_tie(self):
        r,c,w=load_config()
        w['platforms']=[self.f,{'id':'z','x':.5,'y':.1,'width':1},{'id':'b','x':.5,'y':.1,'width':1}]
        p=Player(1,.5,.2,1,vy=-18)
        move_player(p,I(),w,c,1e-5,0)
        self.assertEqual((p.y,p.support),(.1,'b'))

    def test_C05_residual_motion_leaves_platform(self):
        r,c,w=load_config()
        c.update(gravity=30,terminalFallSpeed=200)
        w['platforms']=[self.f]
        p=Player(1,-.5,1,1,vx=180,vy=-120,action='Hitstun')
        move_player(p,I(),w,c,1e-5,0)
        self.assertGreater(p.x,1.4)
        self.assertLess(p.y,0)
        self.assertIsNone(p.support)

    def test_wall_before_landing_splits_path(self):
        r,c,w=load_config()
        w['platforms']=[{'id':'edge','x':8.5,'y':8,'width':1}]
        p=Player(1,8.59,8.2,1,vx=9,vy=-18,action='Hitstun')
        move_player(p,I(),w,c,1e-5,0)
        self.assertEqual(p.support,'edge')
        self.assertAlmostEqual(p.x,8.6)
        self.assertEqual(p.vx,0)


class ConfigTests(unittest.TestCase):
    def test_rejects_invalid_data(self):
        cases=[lambda r,c,w: w['platforms'].append(deepcopy(w['platforms'][0])),
               lambda r,c,w: w['platforms'][0].update(width=-1),
               lambda r,c,w: w['spawns'][0].update(y=100),
               lambda r,c,w: r.update(matchTicks=0),
               lambda r,c,w: r['hazardKeyframes'].__setitem__(1,[0,35]),
               lambda r,c,w: c.update(attackTotal=31)]
        for index,change in enumerate(cases):
            with self.subTest(case=index):
                r,c,w=load_config()
                change(r,c,w)
                with self.assertRaises(ValueError):
                    validate(r,c,w)


if __name__=='__main__':
    unittest.main()
