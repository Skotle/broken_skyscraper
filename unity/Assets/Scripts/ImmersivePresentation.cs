using System.Collections.Generic;
using UnityEngine;

namespace BrokenSkyscraper
{
    public partial class UnityPresentation
    {
        public const int EffectCapacity=160;
        public bool ReducedMotion;public float Intensity=1;
        public FeedbackDirector Feedback;
        readonly Particle[] particles=new Particle[EffectCapacity];
        readonly Transform[] wind=new Transform[36],beacons=new Transform[20];
        readonly Renderer[] beaconRenderers=new Renderer[20],suits=new Renderer[2];
        readonly MaterialPropertyBlock propertyBlock=new MaterialPropertyBlock();
        int cursor;float trailClock;
        class Particle{public Transform t;public Vector3 velocity,size;public float life,total,gravity,spin;}
        public int ActiveEffects {get{int n=0;foreach(var p in particles)if(p!=null&&p.life>0)n++;return n;}}
        void BuildImmersion()
        {
            cursor=0;trailClock=0;
            for(int i=0;i<EffectCapacity;i++)
            {
                var t=Shape("Pooled feedback",Vector3.zero,Vector3.one,Color.white);t.gameObject.SetActive(false);
                particles[i]=new Particle{t=t};
            }
            for(int i=0;i<wind.Length;i++)wind[i]=Shape("Wind mote",Vector3.zero,new Vector3(.12f,.018f,.015f),new Color(.25f,.39f,.44f));
            for(int i=0;i<beacons.Length;i++)
            {
                beacons[i]=Shape("Warning beacon",new Vector3(i%2==0?-8.97f:8.97f,-1+(i/2)*4,-.1f),new Vector3(.08f,.35f,.08f),lime);
                beaconRenderers[i]=beacons[i].GetComponent<Renderer>();
            }
            for(int i=0;i<2;i++)suits[i]=actors[i].Find("Suit").GetComponent<Renderer>();
        }
        void Emit(Vector3 position,Vector3 velocity,Vector3 size,Color color,float life,float gravity=0,float spin=0)
        {
            if(Intensity<=0)return;
            var p=particles[cursor++%EffectCapacity];p.velocity=velocity;p.size=size;p.life=p.total=life;p.gravity=gravity;p.spin=spin;
            p.t.position=position;p.t.localScale=size;p.t.localRotation=Quaternion.identity;p.t.GetComponent<Renderer>().sharedMaterial=Mat(color);p.t.gameObject.SetActive(true);
        }
        public void FeedbackTick(IList<FeedbackCue> cues)
        {
            foreach(var cue in cues)
            {
                Vector3 origin=new Vector3(cue.x,cue.y,-2);Color col=cue.player==1?cyan:coral;
                if(cue.kind==CueKind.Impact)
                {
                    for(int j=0;j<(ReducedMotion?5:18)*Intensity;j++)
                    {
                        float a=j*2.4f;Emit(origin+Vector3.up*.8f,new Vector3(Mathf.Cos(a),Mathf.Sin(a),0)*(2+j%4),new Vector3(.12f,.045f,.04f),j%3==0?Color.white:lime,.28f+j%3*.08f,5,180);
                    }
                }
                if(cue.kind==CueKind.Land||cue.kind==CueKind.Jump||cue.kind==CueKind.Step)
                {
                    int count=cue.kind==CueKind.Step?2:ReducedMotion?4:12;
                    for(int j=0;j<count*Intensity;j++)
                        Emit(origin,new Vector3((j%2==0?-1:1)*(.8f+j*.2f),.2f+(j%3)*.25f,0),new Vector3(.15f,.035f,.03f),new Color(.49f,.61f,.63f),.2f+cue.strength*.18f,1);
                    if(cue.kind==CueKind.Land&&cue.strength>.65f)shake=Mathf.Max(shake,.1f*cue.strength);
                }
                if(cue.kind==CueKind.Swing)
                {
                    // Short arc follows the same fixed facing as the attack.
                    int facing=actors[cue.player-1].localScale.x<0?-1:1;
                    for(int j=0;j<7;j++)
                    {
                        float a=(j-3)*.2f;Emit(origin+new Vector3(facing*(.45f+Mathf.Cos(a)*.55f),.8f+Mathf.Sin(a)*.9f,0),Vector3.right*facing*.9f,new Vector3(.07f,.14f,.03f),col,.13f);
                    }
                }
            }
        }
        void RenderImmersion(Match m,float dt)
        {
            float motion=ReducedMotion?.2f:Intensity,tension=Feedback==null?0:Feedback.Tension;
            trailClock+=dt;bool trail=trailClock>=.045f;if(trail)trailClock=0;
            for(int i=0;i<2;i++)
            {
                var p=m.players[i];var actor=actors[i];float land=Feedback==null?0:Feedback.landing[i];
                float squash=land*.17f*motion;
                actor.localScale=new Vector3(actor.localScale.x*(1+squash),1-squash,1);
                float lean=p.action=="Hitstun"?(float)-p.vx*1.7f:p.action=="Dodge"?p.facing*13:-(float)p.vx*.8f;
                actor.localRotation=Quaternion.Euler(0,0,lean*motion);
                if(p.support==null)
                    for(int l=0;l<2;l++)legs[i*2+l].localRotation=Quaternion.Euler(0,0,(l==0?-1:1)*(p.vy>0?30:15)*motion);
                if(p.action=="Neutral"&&p.support!=null)actor.position+=Vector3.up*Mathf.Sin(ambientClock*3+i)*.018f*motion;
                propertyBlock.SetColor("_Color",p.action=="Hitstun"?Color.Lerp(i==0?cyan:coral,Color.white,.65f):i==0?cyan:coral);suits[i].SetPropertyBlock(propertyBlock);
                if(trail&&dt>0&&!ReducedMotion&&!m.paused&&m.phase=="Playing")
                {
                    if(p.action=="Dodge")
                    {
                        // Silhouette fragments disappear quickly; the real hurtbox never moves with them.
                        Emit(new Vector3((float)p.x,(float)p.y+.75f,-.7f),new Vector3(-p.facing*.7f,0,0),new Vector3(.55f,1.3f,.02f),(i==0?cyan:coral)*.45f,.2f);
                    }
                    if(p.vy<-8)for(int j=0;j<2;j++)Emit(new Vector3((float)p.x+(j==0?-.55f:.55f),(float)p.y+1,-1.5f),Vector3.up*2,new Vector3(.022f,.45f,.02f),new Color(.47f,.62f,.68f),.18f);
                }
            }
            for(int i=0;i<wind.Length;i++)
            {
                wind[i].gameObject.SetActive(!ReducedMotion&&Intensity>0);
                float speed=.5f+tension*2;
                // Position from one clock avoids discontinuities when the danger value changes.
                wind[i].position=new Vector3(Mathf.Repeat(i*7.13f+ambientClock*.8f,22)-11,Mathf.Repeat(i*3.37f-ambientClock*.42f,44)-3,2);
                wind[i].localScale=new Vector3(.12f*speed*Intensity,.015f,.015f);
            }
            for(int i=0;i<beacons.Length;i++)
            {
                float danger=m.world.hazardEnabled?Mathf.Clamp01(1-((float)m.hazardY-beacons[i].position.y)/4):0;
                float pulse=ReducedMotion?1:.8f+.2f*Mathf.Sin(ambientClock*4+i*.15f);
                propertyBlock.SetColor("_Color",Color.Lerp(new Color(.16f,.36f,.39f),coral,danger)*pulse);beaconRenderers[i].SetPropertyBlock(propertyBlock);
            }
            foreach(var p in particles)
            {
                if(p.life<=0)continue;p.life-=dt;
                if(p.life<=0||Intensity<=0){p.life=0;p.t.gameObject.SetActive(false);continue;}
                p.t.position+=p.velocity*dt;p.velocity+=Vector3.down*p.gravity*dt;p.t.Rotate(0,0,p.spin*dt);
                p.t.localScale=p.size*Mathf.Clamp01(p.life/p.total*2);
            }
        }
    }
}
