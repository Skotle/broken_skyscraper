using System;
using System.Collections.Generic;
using UnityEngine;

namespace BrokenSkyscraper
{
    // Deterministic, original PCM synthesis. Short fades prevent clicks; each cue has its own timbre.
    public static class SoundDesign
    {
        public const int Rate=22050;
        public static float[] Cue(CueKind kind)
        {
            float duration=kind==CueKind.Result?1.5f:kind==CueKind.Start?.65f:kind==CueKind.Warning?.45f:kind==CueKind.Land?.32f:.22f;
            var data=new float[(int)(Rate*duration)];var random=new System.Random(173+(int)kind);float phase=0,low=0;
            for(int i=0;i<data.Length;i++)
            {
                float t=i/(float)Rate,u=t/duration,noise=(float)random.NextDouble()*2-1;low+=.15f*(noise-low);
                float env=Mathf.Min(1,t/.008f)*Mathf.Pow(1-u,2),hz=180,sample=0;
                switch(kind)
                {
                    case CueKind.Step: hz=130-70*u;sample=low*.7f+noise*.12f;break;
                    case CueKind.Jump: hz=260+680*u;sample=low*.2f;break;
                    case CueKind.Land: hz=95-48*u;sample=low*.8f+noise*.13f;break;
                    case CueKind.Windup: hz=110+180*u;sample=low*.2f;break;
                    case CueKind.Swing: hz=500-350*u;sample=noise*.6f*(float)Math.Sin(Math.PI*u);break;
                    case CueKind.Dodge: hz=1100-850*u;sample=noise*.26f;break;
                    case CueKind.Impact: hz=150-100*u;sample=noise*.48f+low*.5f;break;
                    case CueKind.Warning: hz=660;env*=.55f+.45f*Mathf.Sin(t*40);break;
                    case CueKind.Count: hz=440;break;
                    case CueKind.Start: hz=u<.25f?523:u<.5f?659:784;break;
                    case CueKind.Result: hz=u<.25f?392:u<.5f?523:u<.75f?659:784;break;
                }
                phase+=2*Mathf.PI*hz/Rate;
                sample+=Mathf.Sin(phase)*(kind==CueKind.Swing?.08f:.42f);
                data[i]=Mathf.Clamp(sample*env*.58f,-.8f,.8f);
            }
            return data;
        }
        public static float[] Bed(bool tension)
        {
            // Integer-cycle components and periodic modulation create seamless eight-second loops.
            var data=new float[Rate*8];
            for(int i=0;i<data.Length;i++)
            {
                float t=i/(float)Rate;
                if(tension)data[i]=(.11f*Mathf.Sin(2*Mathf.PI*82.5f*t)+.055f*Mathf.Sin(2*Mathf.PI*165*t))*(.6f+.4f*Mathf.Cos(2*Mathf.PI*2*t));
                else data[i]=.08f*Mathf.Sin(2*Mathf.PI*55*t)+.025f*Mathf.Sin(2*Mathf.PI*110*t)+.018f*Mathf.Sin(2*Mathf.PI*293.625f*t)*Mathf.Sin(2*Mathf.PI*.125f*t);
            }
            return data;
        }
    }
    public sealed class ReactiveAudio
    {
        const int VoiceLimit=12;
        readonly AudioSource[] voices=new AudioSource[VoiceLimit];readonly int[] priority=new int[VoiceLimit];
        readonly Dictionary<CueKind,AudioClip> clips=new Dictionary<CueKind,AudioClip>();
        readonly AudioSource baseBed,tensionBed;readonly List<AudioClip> owned=new List<AudioClip>();
        bool paused;float tension;
        public ReactiveAudio(GameObject owner)
        {
            for(int i=0;i<VoiceLimit;i++)voices[i]=Source(owner);
            foreach(CueKind kind in Enum.GetValues(typeof(CueKind)))clips[kind]=Clip(kind.ToString(),SoundDesign.Cue(kind));
            baseBed=Source(owner);tensionBed=Source(owner);baseBed.clip=Clip("Tower resonance",SoundDesign.Bed(false));tensionBed.clip=Clip("Pressure pulse",SoundDesign.Bed(true));
            baseBed.loop=tensionBed.loop=true;baseBed.Play();tensionBed.Play();
        }
        static AudioSource Source(GameObject owner){var s=owner.AddComponent<AudioSource>();s.playOnAwake=false;s.spatialBlend=0;return s;}
        AudioClip Clip(string name,float[] samples){var c=AudioClip.Create(name,samples.Length,1,SoundDesign.Rate,false);c.SetData(samples,0);owned.Add(c);return c;}
        public void Reset(){foreach(var s in voices)s.Stop();tension=0;}
        public void Play(IList<FeedbackCue> cues,float volume)
        {
            if(paused)return;
            foreach(var cue in cues)
            {
                int rank=cue.kind==CueKind.Step?0:cue.kind==CueKind.Result||cue.kind==CueKind.Impact?3:2,slot=-1;
                for(int i=0;i<VoiceLimit;i++)if(!voices[i].isPlaying){slot=i;break;}
                if(slot<0)for(int i=0;i<VoiceLimit;i++)if(priority[i]<rank){slot=i;break;}
                if(slot<0)continue;
                var s=voices[slot];s.Stop();s.clip=clips[cue.kind];s.panStereo=cue.kind>=CueKind.Warning?0:cue.player==1?-.28f:.28f;
                s.pitch=cue.kind==CueKind.Step?1+(cue.player==1?-.08f:.08f):1;
                s.volume=volume*Mathf.Lerp(.25f,.65f,cue.strength);priority[slot]=rank;s.Play();
            }
        }
        public void Update(float target,float ambience,bool freeze,float dt)
        {
            if(freeze!=paused)
            {
                paused=freeze;
                foreach(var s in voices)if(paused)s.Pause();else s.UnPause();
                if(paused){baseBed.Pause();tensionBed.Pause();}else{baseBed.UnPause();tensionBed.UnPause();}
            }
            if(!paused)tension=Mathf.MoveTowards(tension,target,dt*.7f);
            baseBed.volume=ambience*(1-.25f*tension);tensionBed.volume=ambience*tension;
        }
        public void Dispose(){foreach(var c in owned)UnityEngine.Object.Destroy(c);}
    }
}
