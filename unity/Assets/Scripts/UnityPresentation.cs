using System;
using System.Collections.Generic;
using UnityEngine;
using Object=UnityEngine.Object;

namespace BrokenSkyscraper
{
    public partial class UnityPresentation
    {
        public readonly Color cyan=new Color(.32f,.85f,1), coral=new Color(1,.48f,.3f), lime=new Color(.77f,.94f,.42f);
        public Camera primary,secondary;
        Transform root,veil;Transform[] actors=new Transform[2],arms=new Transform[2],legs=new Transform[4],rings=new Transform[2];
        readonly List<GameObject> debug=new List<GameObject>();
        readonly Dictionary<Color,Material> materials=new Dictionary<Color,Material>();
        Material source;int farTicks,nearTicks;bool split;float shake,ambientClock;
        public UnityPresentation(Material material)
        {
            source=material;
            primary=NewCamera("Shared Camera");secondary=NewCamera("Player 2 Camera");secondary.enabled=false;
            primary.gameObject.AddComponent<AudioListener>();
        }
        Camera NewCamera(string name)
        {
            var c=new GameObject(name).AddComponent<Camera>();c.orthographic=true;c.orthographicSize=8;
            c.backgroundColor=new Color(.035f,.055f,.09f);c.clearFlags=CameraClearFlags.SolidColor;c.nearClipPlane=.1f;c.farClipPlane=180;
            c.transform.position=new Vector3(0,26,-40);c.rect=new Rect(0,.095f,1,.79f);return c;
        }
        Material Mat(Color color)
        {
            if(!materials.TryGetValue(color,out var m)){m=new Material(source){color=color};materials[color]=m;}return m;
        }
        Transform Shape(string name,Vector3 position,Vector3 size,Color color,Transform parent=null,PrimitiveType type=PrimitiveType.Cube)
        {
            var obj=GameObject.CreatePrimitive(type);obj.name=name;Object.Destroy(obj.GetComponent<Collider>());
            obj.transform.SetParent(parent??root,false);obj.transform.localPosition=position;obj.transform.localScale=size;obj.GetComponent<Renderer>().sharedMaterial=Mat(color);return obj.transform;
        }
        public void Build(Match match)
        {
            if(root!=null){root.gameObject.SetActive(false);Object.Destroy(root.gameObject);}root=new GameObject("Generated stage visuals").transform;
            debug.Clear();farTicks=nearTicks=0;split=false;secondary.enabled=false;shake=0;ambientClock=0;
            var random=new System.Random(1977);
            // Far silhouette and lit windows: decorative only, never colliders.
            for(int i=0;i<24;i++)
            {
                float x=-38+i*3.2f,height=18+(float)random.NextDouble()*32;
                Shape("Skyline",new Vector3(x,height/2-9,18+i%3),new Vector3(2.7f,height,2),new Color(.055f+i%3*.009f,.085f+i%3*.01f,.13f+i%3*.012f));
                for(int row=0;row<height/2;row++)for(int col=0;col<2;col++)
                    if(random.NextDouble()>.48)Shape("Window",new Vector3(x-.65f+col*1.3f,row*2-7,16),new Vector3(.18f,.52f,.1f),new Color(.12f,.21f,.28f));
            }
            for(int side=-1;side<=1;side+=2)
            {
                Shape("Tower edge",new Vector3(side*9.25f,17,3),new Vector3(.45f,44,2),new Color(.12f,.18f,.23f));
                Shape("Edge light",new Vector3(side*9.03f,17,1),new Vector3(.025f,44,.1f),new Color(.2f,.39f,.46f));
            }
            for(int y=-2;y<38;y+=4)
            {
                Shape("Rear structural beam",new Vector3(0,y,5),new Vector3(18,.12f,1),new Color(.07f,.115f,.16f));
                var brace=Shape("Cross bracing",new Vector3(y%8==0?-5:5,y+2,6),new Vector3(.09f,5.6f,.1f),new Color(.09f,.14f,.19f));brace.localRotation=Quaternion.Euler(0,0,y%8==0?45:-45);
            }
            foreach(var f in match.world.platforms)
            {
                Shape(f.id,new Vector3((float)f.x,(float)f.y-.19f,0),new Vector3((float)f.width,.38f,1.5f),new Color(.22f,.3f,.34f));
                Shape("Platform edge",new Vector3((float)f.x,(float)f.y-.035f,-.8f),new Vector3((float)f.width,.07f,.07f),new Color(.63f,.75f,.74f));
                Shape("Platform inset",new Vector3((float)f.x,(float)f.y-.23f,-.8f),new Vector3((float)f.width-.2f,.075f,.07f),new Color(.09f,.145f,.18f));
                for(float x=(float)(f.x-f.width/2)+.2f;x<f.x+f.width/2;x+=.8f)
                    Shape("Rivet",new Vector3(x,(float)f.y-.2f,-.85f),new Vector3(.04f,.04f,.03f),new Color(.42f,.53f,.55f));
            }
            Shape("Fall line",new Vector3(0,-2,-.5f),new Vector3(18,.04f,.1f),coral);
            veil=Shape("Descending veil",new Vector3(0,54,1),new Vector3(50,40,.1f),new Color(.21f,.26f,.3f));
            Shape("Veil boundary",new Vector3(0,-.5f,-.15f),new Vector3(1,.003f,1),new Color(.88f,.94f,.93f),veil);
            veil.gameObject.SetActive(match.world.hazardEnabled);
            for(int i=0;i<2;i++)
            {
                Color col=i==0?cyan:coral;
                actors[i]=new GameObject("P"+(i+1)).transform;actors[i].SetParent(root);
                Shape("Suit",new Vector3(0,.78f,-1),new Vector3(.61f,.83f,.5f),col,actors[i]);
                Shape("Helmet",new Vector3(0,1.36f,-1),new Vector3(.64f,.48f,.55f),col,actors[i]);
                Shape("Visor",new Vector3(.06f,1.4f,-1.31f),new Vector3(.46f,.16f,.07f),new Color(.025f,.055f,.085f),actors[i]);
                Shape("Visor glint",new Vector3(.17f,1.43f,-1.36f),new Vector3(.16f,.025f,.02f),Color.white,actors[i]);
                Shape("Belt",new Vector3(0,.5f,-1.29f),new Vector3(.63f,.09f,.04f),new Color(.07f,.12f,.16f),actors[i]);
                Shape("Chest lamp",new Vector3(-.16f,.95f,-1.28f),new Vector3(.08f,.13f,.06f),lime,actors[i]);
                arms[i]=Shape("Push arm",new Vector3(.4f,.9f,-1),new Vector3(.21f,.6f,.38f),col*.85f,actors[i]);
                for(int l=0;l<2;l++)legs[i*2+l]=Shape("Boot",new Vector3(l==0?-.19f:.19f,.2f,-1),new Vector3(.25f,.4f,.45f),new Color(.15f,.22f,.27f),actors[i]);
                rings[i]=new GameObject("Dodge outline").transform;rings[i].SetParent(actors[i],false);
                for(int part=0;part<16;part++)
                {
                    float angle=part*Mathf.PI/8;
                    var segment=Shape("Dodge arc",new Vector3(Mathf.Cos(angle)*.62f,.8f+Mathf.Sin(angle)*1.05f,-1.5f),new Vector3(.12f,.04f,.03f),col,rings[i]);
                    segment.localRotation=Quaternion.Euler(0,0,angle*Mathf.Rad2Deg+90);
                }
                rings[i].gameObject.SetActive(false);
                debug.Add(Shape("Hurtbox debug",Vector3.zero,new Vector3(.8f,1.6f,.015f),col*.3f).gameObject);debug[i].SetActive(false);
            }
            primary.orthographicSize=8;primary.transform.position=new Vector3(0,(float)match.players[0].y-2,-40);
            BuildImmersion();
        }
        public void Tick(Match m)
        {
            double gap=Math.Abs(m.players[0].y-m.players[1].y);
            farTicks=gap>12?farTicks+1:0;nearTicks=gap<8?nearTicks+1:0;
            if(!split&&farTicks>=30)split=true;if(split&&nearTicks>=60)split=false;
            if(m.events.Count>0)shake=.16f;
        }
        public bool Split=>split;
        public void Render(Match m,float dt,bool menu,bool shakeEnabled,bool showDebug)
        {
            if(m.paused)dt=0;
            ambientClock+=dt;secondary.enabled=split&&!menu;
            primary.rect=menu?new Rect(0,0,1,1):new Rect(0,.095f,split?.5f:1,.79f);
            secondary.rect=new Rect(.5f,.095f,.5f,.79f);
            for(int i=0;i<2;i++)
            {
                var p=m.players[i];var t=actors[i];
                t.position=new Vector3((float)p.x,(float)p.y,0);
                t.localScale=new Vector3(p.action.StartsWith("Attack")?p.attack_facing:p.facing,1,1);
                float walk=p.support!=null?(float)Math.Sin(ambientClock*14)*Mathf.Clamp01((float)Math.Abs(p.vx)/6)*.35f:0;
                for(int l=0;l<2;l++)legs[i*2+l].localRotation=Quaternion.Euler(0,0,walk*(l==0?1:-1)*40);
                float extension=p.action=="AttackActive"?.55f:p.action=="AttackStartup"?-.16f:0;
                arms[i].localPosition=new Vector3(.4f+extension,.9f,-1);
                arms[i].localRotation=Quaternion.Euler(0,0,p.action=="AttackActive"?-85:p.action=="AttackStartup"?30:walk*15);
                rings[i].gameObject.SetActive(p.action=="Dodge");rings[i].localScale=Vector3.one*(p.age<9?1:.86f);
                debug[i].SetActive(showDebug);debug[i].transform.position=new Vector3((float)p.x,(float)p.y+.8f,-.6f);
            }
            if(veil!=null)veil.position=new Vector3(0,(float)m.hazardY+20,1);
            if(menu)Follow(primary,new Vector2(3,(float)m.players[0].y-2),9,dt);
            else if(split){for(int i=0;i<2;i++)Follow(i==0?primary:secondary,new Vector2((float)m.players[i].x,(float)m.players[i].y-1.5f),6.2f,dt);}
            else
            {
                var a=m.players[0];var b=m.players[1];
                float low=(float)Math.Min(a.y,b.y)-5,high=(float)Math.Max(a.y,b.y)+3.6f;
                float size=Mathf.Max(5.6f,(high-low)/2,((float)Math.Abs(a.x-b.x)+4.8f)/(2*primary.aspect));
                Follow(primary,new Vector2((float)(a.x+b.x)/2,(low+high)/2),size,dt);
            }
            shake=Mathf.Max(0,shake-dt);
            if(shakeEnabled&&!ReducedMotion&&shake>0&&dt>0){primary.transform.position+=new Vector3(Mathf.Sin(ambientClock*130),Mathf.Cos(ambientClock*110),0)*shake*.4f*Intensity;}
            RenderImmersion(m,dt);
        }
        void Follow(Camera cam,Vector2 point,float size,float dt)
        {
            float factor=1-Mathf.Exp(-9*dt);cam.orthographicSize=Mathf.Lerp(cam.orthographicSize,size,factor);
            if(size>cam.orthographicSize+1)cam.orthographicSize=size;
            cam.transform.position=Vector3.Lerp(cam.transform.position,new Vector3(point.x,point.y,-40),factor);
            if(Math.Abs(cam.transform.position.y-point.y)>3)cam.transform.position=new Vector3(point.x,point.y,-40);
        }
    }
}
