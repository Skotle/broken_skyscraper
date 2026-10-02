using System;
using System.Collections.Generic;

namespace BrokenSkyscraper
{
    public enum CueKind { Step, Jump, Land, Windup, Swing, Dodge, Impact, Warning, Count, Start, Result }
    public struct FeedbackCue
    {
        public CueKind kind; public int player; public float x,y,strength;
        public FeedbackCue(CueKind k,int p,double px,double py,float s=1){kind=k;player=p;x=(float)px;y=(float)py;strength=s;}
    }
    // Observes completed simulation steps only. No presentation state is serialized into Match.
    public sealed class FeedbackDirector
    {
        public readonly List<FeedbackCue> cues=new List<FeedbackCue>(16);
        public float Tension {get;private set;}
        public readonly float[] landing=new float[2];
        public readonly string[] tags={"",""};
        readonly int[] tagTicks=new int[2],stepTicks=new int[2];
        readonly Snapshot[] previous=new Snapshot[2];
        int tick,countdown,warningTick; string phase;
        struct Snapshot {public double vy;public bool grounded;public string action;public int attacks,dodges;}
        static Snapshot Take(Player p)=>new Snapshot{vy=p.vy,grounded=p.support!=null,action=p.action,attacks=p.attack_sequence,dodges=p.dodges};
        public void Reset(Match m)
        {
            cues.Clear();Tension=0;tick=m.tick;countdown=m.countdown;phase=m.phase;warningTick=m.tick-60;
            for(int i=0;i<2;i++){previous[i]=Take(m.players[i]);landing[i]=0;tags[i]="";tagTicks[i]=stepTicks[i]=0;}
        }
        public void Observe(Match m)
        {
            cues.Clear();if(m.paused||m.tick==tick&&m.countdown==countdown&&m.phase==phase)return;
            if(m.phase=="Countdown"&&(m.countdown+59)/60!=(countdown+59)/60)Emit(CueKind.Count,m.players[0]);
            if(phase=="Countdown"&&m.phase=="Playing")Emit(CueKind.Start,m.players[0]);
            if(m.phase=="Result"&&phase!="Result")Emit(CueKind.Result,m.players[0]);
            float target=0;
            for(int i=0;i<2;i++)
            {
                var p=m.players[i];var old=previous[i];landing[i]=Math.Max(0,landing[i]-.075f);
                if(tagTicks[i]>0&&--tagTicks[i]==0)tags[i]="";
                if(m.tick!=tick)
                {
                    if(p.vy>5&&old.vy<=0&&p.action!="Hitstun")Emit(CueKind.Jump,p);
                    if(p.support!=null&&!old.grounded&&old.vy<0)
                    {
                        float force=Clamp((float)(-old.vy/18));landing[i]=force;Emit(CueKind.Land,p,force);
                        if(force>.65f)Tag(i,"HARD LANDING");
                    }
                    if(p.attack_sequence!=old.attacks)Emit(CueKind.Windup,p);
                    if(p.action=="AttackActive"&&old.action!="AttackActive")Emit(CueKind.Swing,p);
                    if(p.dodges!=old.dodges){Emit(CueKind.Dodge,p);Tag(i,"EVADE");}
                    if(p.support!=null&&Math.Abs(p.vx)>1&&p.action=="Neutral")
                    {if(++stepTicks[i]>=Math.Max(9,21-Math.Abs(p.vx)*2)){Emit(CueKind.Step,p,.45f);stepTicks[i]=0;}}
                    else stepTicks[i]=0;
                }
                float veil=m.world.hazardEnabled?Clamp((float)(1-(m.hazardY-p.y)/6)):0;
                target=Math.Max(target,Math.Max(veil,Clamp((650-p.health)/650f)));
                previous[i]=Take(p);
            }
            foreach(var hit in m.events)
            {
                cues.Add(new FeedbackCue(CueKind.Impact,hit.target,hit.x,hit.y,1));Tag(hit.target-1,"OFF BALANCE");
                target=Math.Max(target,.8f);
            }
            if(m.phase=="Playing")
            {
                target=Math.Max(target,Clamp(1-m.remaining/1800f)*.85f);
                Tension+= (target-Tension)*.045f;
                if(target>.8f&&m.tick-warningTick>=120){Emit(CueKind.Warning,m.players[0]);warningTick=m.tick;}
            }
            else Tension*=.96f;
            tick=m.tick;countdown=m.countdown;phase=m.phase;
        }
        void Tag(int i,string text){tags[i]=text;tagTicks[i]=42;}
        void Emit(CueKind kind,Player p,float strength=1)=>cues.Add(new FeedbackCue(kind,p.id,p.x,p.y,strength));
        static float Clamp(float v)=>Math.Max(0,Math.Min(1,v));
    }
}
