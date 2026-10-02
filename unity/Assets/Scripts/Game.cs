using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace BrokenSkyscraper
{
    public partial class Game : MonoBehaviour
    {
        public Material worldMaterial;
        public Match match;public UnityPresentation visuals;public LocalInput devices;
        public string mode="tower",screen="menu",notice="",lastReplay="";
        public bool showHelp=true,debug,mirror,moving,shake=true,reducedMotion;
        public float effectIntensity=1;
        public readonly FeedbackDirector feedback=new FeedbackDirector();ReactiveAudio audioDirector;
        public int bot,healthPreset,backlog; public float volume=.35f,musicVolume=.12f;
        public int remap=-1;KeyCode[][] remapBackup;
        public Recording recording,playback;int replayIndex,smokeTicks;bool smoke,smokeCapture;
        double accumulator;float noticeUntil;
        string smokePath;int[] healthA={1000,1000,600,400},healthB={1000,600,600,1000};
        public static World LoadMap(string name)=>JsonUtility.FromJson<World>(Resources.Load<TextAsset>(name).text);
        public static PlayerConfig LoadConfig()=>JsonUtility.FromJson<PlayerConfig>(Resources.Load<TextAsset>("player").text);
        void Awake()
        {
            Application.targetFrameRate=120;QualitySettings.vSyncCount=1;Application.runInBackground=true;
            devices=new LocalInput();volume=PlayerPrefs.GetFloat("volume",.35f);musicVolume=PlayerPrefs.GetFloat("music",.12f);shake=PlayerPrefs.GetInt("shake",1)!=0;
            reducedMotion=PlayerPrefs.GetInt("reducedMotion",0)!=0;effectIntensity=PlayerPrefs.GetFloat("effectIntensity",1);
            visuals=new UnityPresentation(worldMaterial);
            visuals.Feedback=feedback;audioDirector=new ReactiveAudio(gameObject);
            StartMatch(false);
            var args=Environment.GetCommandLineArgs();
            for(int i=0;i<args.Length;i++)if(args[i]=="-smokeOutput"&&i+1<args.Length){smoke=true;smokePath=Path.GetFullPath(args[i+1]);}
            if(smoke){mode="tower";StartMatch(true);}
        }
        public void StartMatch(bool play=true)
        {
            string map=mode=="lab"?"combat_lab":mode=="final15"?"final15":"tower";
            match=new Match(LoadMap(map),LoadConfig(),true,mode=="lab"&&mirror,mode=="lab"&&moving,mode=="final15"?6300:0,mode=="final15"?healthA[healthPreset]:1000,mode=="final15"?healthB[healthPreset]:1000);
            recording=RecordIO.Begin(match,mode);playback=null;replayIndex=0;accumulator=0;
            feedback.Reset(match);audioDirector.Reset();
            devices.Clear();visuals.Build(match);screen=play?"game":"menu";
        }
        void Update()
        {
            visuals.ReducedMotion=reducedMotion;visuals.Intensity=effectIntensity;
            audioDirector.Update(feedback.Tension,musicVolume,match.paused,Time.unscaledDeltaTime);
            bool lost=devices.Poll();
            if(lost&&screen=="game"){Pause();Notify("Controller disconnected. Reconnect and resume.");}
            if(remap>=0){devices.Clear();return;}
            if(Input.GetKeyDown(KeyCode.Escape)||devices.pauseRequested)
            {
                if(screen=="game")Pause();else if(screen=="pause")Resume();else if(screen=="settings")screen=match.paused?"pause":"menu";
            }
            if(Input.GetKeyDown(KeyCode.Tab))showHelp=!showHelp;
            if(Input.GetKeyDown(KeyCode.F1))debug=!debug;
            if(Input.GetKeyDown(KeyCode.F7))SaveReplay();
            if(Input.GetKeyDown(KeyCode.F8))PlayReplay();
            if(Input.GetKeyDown(KeyCode.R)&&screen!="menu"&&screen!="settings")StartMatch();
            if(screen=="game"&&match.phase!="Result")
            {
                accumulator+=smoke?1.0/60:Time.unscaledDeltaTime;int steps=0;
                while(accumulator+1e-12>=1.0/60&&steps<240){Step();accumulator-=1.0/60;steps++;if(screen!="game")break;}
                backlog=(int)(accumulator*60);
            }
            else{accumulator=0;devices.Clear();if(debug&&screen=="pause"&&Input.GetKeyDown(KeyCode.N)){match.paused=false;Step();match.paused=true;}}
            if(smoke&&!smokeCapture&&++smokeTicks>=420){smokeCapture=true;StartCoroutine(CaptureSmoke());}
        }
        void LateUpdate(){if(match!=null)visuals.Render(match,Mathf.Min(Time.unscaledDeltaTime,.1f),screen=="menu",shake,debug);}
        void OnApplicationFocus(bool focus){if(!focus&&!smoke&&screen=="game")Pause();devices?.Clear();}
        public void Pause(){match.paused=true;screen="pause";devices.Clear();accumulator=0;}
        public void Resume(){match.paused=false;screen="game";devices.Clear();accumulator=0;}
        public void Notify(string message){notice=message;noticeUntil=Time.unscaledTime+5;}
        void Step()
        {
            var commands=devices.Consume();
            if(playback!=null)
            {
                if(replayIndex>=playback.frames.Count){Pause();Notify("Replay finished. Restart to play.");return;}
                var f=playback.frames[replayIndex];commands=new[]{f.a,f.b};
            }
            else if(bot!=0)
            {
                var p=match.players[1];commands[1]=new Command(bot==3?(p.x>.3?-1:p.x<-.3?1:0):0,a:bot==2&&match.tick%40==0);
            }
            match.Step(commands[0],commands[1]);PresentStep();
            if(playback!=null)
            {
                if(RecordIO.Hash(RecordIO.State(match))!=playback.frames[replayIndex].hash){Pause();Notify("Replay diverged at step "+replayIndex);return;}replayIndex++;
            }
            else RecordIO.Append(recording,match,commands[0],commands[1]);
            if(match.result!=null&&playback==null&&!smoke)SaveReplay();
        }
        void PresentStep(){feedback.Observe(match);visuals.Tick(match);visuals.FeedbackTick(feedback.cues);audioDirector.Play(feedback.cues,volume);}
        void OnDestroy(){audioDirector?.Dispose();}
        public void SaveReplay()
        {
            try{lastReplay=RecordIO.Save(recording);PlayerPrefs.SetString("lastReplay",lastReplay);PlayerPrefs.Save();Notify("Replay saved to local recordings.");}
            catch(Exception e){Notify("Could not save replay: "+e.Message);Debug.LogException(e);}
        }
        public void PlayReplay()
        {
            try
            {
                string path=string.IsNullOrEmpty(lastReplay)?PlayerPrefs.GetString("lastReplay",""):lastReplay;
                if(!File.Exists(path)){Notify("No recording yet. Press F7 to save one.");return;}
                playback=JsonUtility.FromJson<Recording>(File.ReadAllText(path));match=RecordIO.Restore(playback);mode=playback.mode;
                feedback.Reset(match);audioDirector.Reset();visuals.Build(match);replayIndex=0;screen="game";accumulator=0;devices.Clear();Notify("Playing input recording.");
            }
            catch(Exception e){Notify("Could not load replay: "+e.Message);playback=null;}
        }
        IEnumerator CaptureSmoke()
        {
            Directory.CreateDirectory(smokePath);yield return new WaitForEndOfFrame();
            CaptureCamera("unity-world.png");
            File.WriteAllText(Path.Combine(smokePath,"state.json"),JsonUtility.ToJson(match,true));
            var restored=RecordIO.Restore(recording);bool ok=true;
            foreach(var f in recording.frames){restored.Step(f.a,f.b);if(RecordIO.Hash(RecordIO.State(restored))!=f.hash){ok=false;break;}}
            int replayTick=match.tick;
            mode="final15";StartMatch();match.countdown=0;match.phase="Playing";
            for(int i=0;i<900;i++){match.Step();PresentStep();}
            ok&=match.players[0].health==532&&match.players[1].health==532&&match.phase=="Result";
            yield return null;CaptureCamera("unity-final15-world.png");
            mode="lab";StartMatch();match.countdown=0;match.phase="Playing";
            for(int i=0;i<9;i++){match.Step(new Command(a:i==0));PresentStep();}
            ok&=match.players[1].action=="Hitstun";
            CaptureCamera("unity-impact-world.png");
            mode="tower";StartMatch();match.players[1].y=10;match.players[1].support=null;
            for(int i=0;i<30;i++)visuals.Tick(match);
            yield return null;ok&=visuals.Split;CaptureCamera("unity-split-p1-world.png");
            File.WriteAllText(Path.Combine(smokePath,"smoke.txt"),"Frames: "+smokeTicks+"\nReplay and endgame and split camera: "+ok+"\nReplay tick: "+replayTick+"\nOffscreen camera captures exclude IMGUI overlays.");
            yield return null;Application.Quit(ok?0:2);
        }
        void CaptureCamera(string filename)
        {
            visuals.Render(match,1f/60,false,false,debug);
            var camera=visuals.primary;var target=new RenderTexture(1600,900,24);var previous=RenderTexture.active;
            camera.targetTexture=target;camera.Render();RenderTexture.active=target;
            var image=new Texture2D(1600,900,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,1600,900),0,0);image.Apply();
            File.WriteAllBytes(Path.Combine(smokePath,filename),image.EncodeToPNG());
            camera.targetTexture=null;RenderTexture.active=previous;target.Release();Destroy(target);Destroy(image);
        }
    }
}
