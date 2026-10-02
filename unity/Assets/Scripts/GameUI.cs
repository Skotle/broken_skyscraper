using System;
using UnityEngine;

namespace BrokenSkyscraper
{
    public partial class Game
    {
        readonly Color ink=new Color(.04f,.065f,.1f,.97f),panel=new Color(.075f,.105f,.15f,.96f),muted=new Color(.56f,.65f,.72f),white=new Color(.9f,.94f,.96f),accent=new Color(.77f,.94f,.42f);
        GUIStyle label,button;Texture2D whiteTexture;Font uiFont;
        void InitGUI()
        {
            if(label!=null)return;whiteTexture=Texture2D.whiteTexture;uiFont=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            label=new GUIStyle(GUI.skin.label){font=uiFont,wordWrap=true};button=new GUIStyle(GUI.skin.button){font=uiFont,fontSize=18,alignment=TextAnchor.MiddleLeft,padding=new RectOffset(22,12,0,0)};
            button.normal.background=whiteTexture;button.hover.background=whiteTexture;button.active.background=whiteTexture;
        }
        void Box(float x,float y,float w,float h,Color color){var old=GUI.color;GUI.color=color;GUI.DrawTexture(new Rect(x,y,w,h),whiteTexture);GUI.color=old;}
        void Text(string text,float x,float y,float w=500,float h=32,int size=18,Color? color=null)
        {
            label.fontSize=size;label.normal.textColor=color??white;GUI.Label(new Rect(x,y,w,h),text,label);
        }
        bool Button(string text,float x,float y,float w=430,float h=50,bool bright=false)
        {
            GUI.backgroundColor=bright?accent:new Color(.16f,.22f,.28f);button.normal.textColor=bright?ink:white;button.hover.textColor=bright?ink:accent;button.active.textColor=ink;
            bool click=GUI.Button(new Rect(x,y,w,h),text,button);GUI.backgroundColor=Color.white;return click;
        }
        void OnGUI()
        {
            InitGUI();GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1600f,Screen.height/900f,1));
            if(screen=="menu")Menu();else HUD();
            if(screen=="pause")PausePanel();if(screen=="settings")Settings();
            if(match.result!=null&&screen=="game")ResultPanel();
            if(Time.unscaledTime<noticeUntil){Box(410,810,780,42,panel);Text(notice,430,820,740,28,16,accent);}
            if(remap>=0)RemapPanel();
        }
        void Menu()
        {
            Box(0,0,760,900,new Color(.025f,.045f,.07f,.97f));Box(66,70,44,4,accent);
            Text("LOCAL VERSUS  /  UNITY EDITION",66,91,650,30,17,accent);
            Text("BROKEN\nSKYSCRAPER",60,146,710,175,66);
            Text("Hold your ground. Know when to fall.",66,347,630,40,24,muted);
            Text("Push your rival off balance, recover on the floors below, and stay ahead of the descending veil.",66,402,590,78,20,white);
            if(Button("01   DESCENT  /  FULL TOWER",66,516,610,62,true)){mode="tower";StartMatch();}
            if(Button("02   COMBAT LAB  /  FIVE PLATFORMS",66,591,610,56)){mode="lab";StartMatch();}
            if(Button("03   FINAL 15 SECONDS  /  ENDGAME LAB",66,660,610,56)){mode="final15";StartMatch();}
            if(Button("Settings & controls",66,743,292,48))screen="settings";
            if(Button("Quit",375,743,301,48))Application.Quit();
            Text("2 local players  ·  Keyboard or 2 controllers",66,823,650,26,16,muted);
            Box(1040,690,470,142,panel);Text("IMMERSION UPDATE  0.3",1065,711,430,28,17,accent);
            Text("Full tower and camera are experimental.\nCombat balance still needs human playtesting.",1065,749,420,67,18,muted);
        }
        void HUD()
        {
            Box(0,0,1600,105,ink);Box(0,816,1600,84,ink);
            for(int i=0;i<2;i++)
            {
                var p=match.players[i];float x=i==0?38:1062;Color color=i==0?visuals.cyan:visuals.coral;
                Text("P"+(i+1),x,20,70,50,30,color);Text("HEALTH  "+Math.Ceiling(p.health/10.0),x+74,20,220,28,17);
                bool ready=match.tick>=p.dodge_ready;Text(ready?"DODGE READY":"DODGE  "+((p.dodge_ready-match.tick)/60f).ToString("0.0")+"s",x+300,22,220,30,16,ready?accent:muted);
                Box(x+74,63,414,7,new Color(.15f,.2f,.25f));Box(x+74,63,414*p.health/1000f,7,color);
                string status=match.world.hazardEnabled&&p.y>match.hazardY?"! EXPOSED - DESCEND":match.world.hazardEnabled&&match.hazardY-p.y<=3?"VEIL APPROACHING":p.action=="Neutral"?"READY":p.action.ToUpperInvariant();
                Text(status,x+74,77,430,23,12,status.StartsWith("!")?visuals.coral:muted);
            }
            int seconds=(int)Math.Ceiling(match.remaining/60.0);Text($"{seconds/60:00}:{seconds%60:00}",736,14,165,55,36,accent);
            Text(mode=="lab"?"COMBAT LAB":mode=="final15"?"ENDGAME LAB":"DESCENT",726,65,220,28,14,muted);
            if(visuals.Split){Box(798,105,4,711,ink);Text("P1 VIEW",24,124,160,30,14,visuals.cyan);Text("P2 VIEW",830,124,160,30,14,visuals.coral);}
            double gap=match.players[0].y-match.players[1].y;
            Text(Math.Abs(gap)<=.1?"HEIGHT TIED":$"P{(gap>0?1:2)} HIGHER  +{Math.Abs(gap):0.0}",683,120,290,30,16,white);
            Text("PRESSURE",713,154,150,24,11,muted);Box(713,178,175,3,panel);Box(713,178,175*feedback.Tension,3,visuals.coral);
            if(playback!=null)Text("REPLAY  /  "+replayIndex,38,125,360,32,17,accent);
            for(int i=0;i<2;i++)
            {
                var p=match.players[i];Camera cam=visuals.Split&&i==1?visuals.secondary:visuals.primary;
                Vector3 v=cam.WorldToScreenPoint(new Vector3((float)p.x,(float)p.y+1.95f,0));
                Text("P"+(i+1),v.x/Screen.width*1600-17,900-v.y/Screen.height*900,70,30,16,i==0?visuals.cyan:visuals.coral);
                if(screen=="game"&&feedback.tags[i]!="")Text(feedback.tags[i],v.x/Screen.width*1600-85,925-v.y/Screen.height*900,190,24,12,accent);
            }
            if(showHelp)
            {
                for(int i=0;i<2;i++){var k=devices.keys[i];Text($"P{i+1}   {k[0]}/{k[1]} move   {k[3]} jump   {k[2]}+{k[3]} drop   {k[4]} push   {k[5]} dodge",38,828+i*27,1100,26,15,i==0?visuals.cyan:visuals.coral);}
            }
            else Text("TAB  show controls",38,846,600,30,16,muted);
            Text("ESC  pause   TAB  help   R  restart",1240,831,350,30,14,muted);Text("F1  debug   F7/F8  replay",1240,861,350,26,14,muted);
            if(match.phase=="Countdown"&&screen=="game")
            {
                Box(650,350,300,190,panel);Text(Math.Ceiling(match.countdown/60.0).ToString(),775,365,100,90,68,accent);Text("GET READY",730,475,240,32,23);
            }
            if(debug)
            {
                Box(28,178,445,164,panel);Text($"TICK {match.tick}  /  backlog {backlog}  /  {(1/Math.Max(.001f,Time.unscaledDeltaTime)):0} FPS",43,190,420,28,14,accent);
                for(int i=0;i<2;i++){var p=match.players[i];Text($"P{p.id} ({p.x:0.00}, {p.y:0.00}) v({p.vx:0.0}, {p.vy:0.0})\n{p.action} [{p.age}] support {p.support??"-"}",43,225+i*48,420,47,14);}
            }
        }
        void PausePanel()
        {
            Box(480,198,640,550,ink);Text("PAUSED",520,226,550,60,40,accent);
            if(Button("Resume",520,308,560,50,true))Resume();
            if(Button("Restart match",520,371,560,48))StartMatch();
            if(Button("Settings & controls",520,432,560,48))screen="settings";
            if(Button("Save replay",520,493,270,48))SaveReplay();
            if(Button("Play last replay",807,493,273,48))PlayReplay();
            if(Button("Return to menu",520,554,560,48)){if(recording.frames.Count>0&&playback==null)SaveReplay();StartMatch(false);}
            if(Button("Quit",520,615,560,48))Application.Quit();
            Text(debug?"N advances one simulation tick while paused.":"Your match is frozen, including the veil and cooldowns.",520,687,550,35,16,muted);
        }
        void Settings()
        {
            Box(290,75,1020,735,ink);Text("SETTINGS & CONTROLS",330,101,940,54,36,accent);
            Text("Sound effects",330,180,210,30);volume=GUI.HorizontalSlider(new Rect(555,192,270,20),volume,0,1);
            Text("Adaptive ambience",330,228,210,30);musicVolume=GUI.HorizontalSlider(new Rect(555,240,270,20),musicVolume,0,.5f);
            Text("Effect intensity",330,277,210,30);effectIntensity=GUI.HorizontalSlider(new Rect(555,289,270,20),effectIntensity,0,1);
            if(Button("Screen shake: "+(shake?"ON":"OFF"),870,178,390,42))shake=!shake;
            if(Button("Reduced motion: "+(reducedMotion?"ON":"OFF"),870,230,390,42))reducedMotion=!reducedMotion;
            if(Button("Window: "+(Screen.fullScreen?"FULLSCREEN":"WINDOWED"),870,282,390,42))Screen.fullScreen=!Screen.fullScreen;
            Text("Reduced motion disables camera shake, trails and drifting particles.",330,329,940,27,14,muted);
            Text("KEYBOARD",330,370,260,27,15,muted);Text("Move / Down / Jump / Push / Dodge",330,400,620,28,17);
            for(int i=0;i<2;i++){var k=devices.keys[i];Text($"P{i+1}   {k[0]}, {k[1]} / {k[2]} / {k[3]} / {k[4]} / {k[5]}",330,435+i*32,790,35,17,i==0?visuals.cyan:visuals.coral);}
            if(Button("Remap keys",1010,405,250,48)){remap=0;remapBackup=new[]{(KeyCode[])devices.keys[0].Clone(),(KeyCode[])devices.keys[1].Clone()};devices.Clear();}
            Text("CONTROLLERS  "+devices.connected+" connected",330,515,860,27,15,muted);
            Text("Left stick: move  /  A: jump  /  Down+A: drop  /  X: push  /  B: dodge  /  Start: pause",330,550,880,38,17);
            string[] bots={"Human","Stationary target","Repeated push","Return to center"};
            if(Button("P2: "+bots[bot],330,616,440,44))bot=(bot+1)%4;
            if(Button("Lab mirror: "+(mirror?"ON":"OFF"),790,616,220,44))mirror=!mirror;
            if(Button("Moving: "+(moving?"ON":"OFF"),1030,616,230,44))moving=!moving;
            if(Button($"Endgame health: {healthA[healthPreset]/10} / {healthB[healthPreset]/10}",330,686,440,48))healthPreset=(healthPreset+1)%4;
            if(Button("Save & back",790,686,470,48,true)){PlayerPrefs.SetFloat("volume",volume);PlayerPrefs.SetFloat("music",musicVolume);PlayerPrefs.SetInt("shake",shake?1:0);PlayerPrefs.SetInt("reducedMotion",reducedMotion?1:0);PlayerPrefs.SetFloat("effectIntensity",effectIntensity);PlayerPrefs.Save();screen=match.paused?"pause":"menu";}
        }
        void RemapPanel()
        {
            string[] names={"MOVE LEFT","MOVE RIGHT","DOWN","JUMP","PUSH","DODGE"};
            Box(470,290,660,300,panel);Text($"P{remap/6+1}  /  {names[remap%6]}",510,330,580,60,30,accent);
            Text("Press a key. Esc cancels all changes.\nMenu and debug shortcuts are reserved.",510,410,560,80,20);
            var e=Event.current;
            if(e.type!=EventType.KeyDown)return;
            if(e.keyCode==KeyCode.Escape){devices.keys=remapBackup;remap=-1;e.Use();return;}
            var key=e.keyCode;
            if(key==KeyCode.None||key==KeyCode.R||key==KeyCode.N||key==KeyCode.Tab||key>=KeyCode.F1&&key<=KeyCode.F15)return;
            for(int i=0;i<remap;i++)if(devices.keys[i/6][i%6]==key){Notify("That key is already assigned.");return;}
            devices.keys[remap/6][remap%6]=key;remap++;if(remap==12){devices.Save();remap=-1;Notify("Key bindings saved.");}devices.Clear();e.Use();
        }
        void ResultPanel()
        {
            var r=match.result;Box(470,208,660,520,ink);Text(r.winner==0?"DRAW":"PLAYER "+r.winner+" WINS",510,244,580,72,44,accent);
            string reason=r.reason=="height"?"Time up. Higher position wins.":r.reason=="health"?"Height tied. More health wins.":r.reason=="fall"?"Opponent fell below the tower.":r.reason=="hazard"?"Opponent lost all health to the veil.":r.reason=="simultaneous"?"Both players were eliminated on the same tick.":r.reason=="tie"?"Height and health are tied.":"Fall and health depletion.";
            Text(reason,510,334,580,60,20,muted);
            for(int i=0;i<2;i++){var p=match.players[i];Text($"P{i+1}   height {p.y:0.00}   health {p.health/10f:0.0}\nPushes {p.pushes}   Hits {p.hits}   Dodges {p.dodges}",510,416+i*70,590,65,18,i==0?visuals.cyan:visuals.coral);}
            if(Button("Rematch",510,594,280,55,true))StartMatch();
            if(Button("Main menu",810,594,280,55))StartMatch(false);
            Text("Recorded locally. F8 to replay.",510,677,580,30,16,muted);
        }
    }
}
