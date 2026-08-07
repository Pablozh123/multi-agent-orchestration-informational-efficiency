"""Abbildung 19 neu: Feldtest-Bot, fünf Anforderungen (Terminologie-Update)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle, Arc

NAVY='#16324f'; RED='#e8452c'; BLUE='#2467a6'; GREY='#5f6b76'; LGREY='#eef1f5'; BORD='#c9d2dc'
fig,ax=plt.subplots(figsize=(16,9),dpi=200)
ax.set_xlim(0,32); ax.set_ylim(0,18); ax.axis('off'); fig.patch.set_facecolor('white')

def rbox(x,y,w,h,ec,fc='white',lw=2.2,r=0.18):
    b=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.02,rounding_size={r}',ec=ec,fc=fc,lw=lw,zorder=2)
    ax.add_patch(b); return b
def arrow(x1,y1,x2,y2,c='#2c3e50',lw=2.0):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',color=c,lw=lw,mutation_scale=16),zorder=3)
def dotline(xc,y,w,c):
    ax.plot([xc-w/2,xc+w/2],[y,y],color=c,lw=2.2,zorder=3)
    ax.plot([xc-w/2,xc+w/2],[y,y],ls='none',marker='o',ms=4.5,color=c,zorder=3)

# Titel
ax.text(0.8,16.85,'Feldtest-Bot auf Mentions-Märkten: fünf Anforderungen',fontsize=27,fontweight='bold',color=NAVY,va='center')
ax.text(0.8,16.0,'separates, deterministisches Modul mit kleinem Realeinsatz, acht Läufe bis zum 22. Juli 2026',fontsize=15,color='#46617a',va='center')

# rotes Band
band_y,bh=14.75,0.85
pts=[(11.7,band_y),(31.2,band_y),(31.85,band_y+bh/2),(31.2,band_y+bh),(11.7,band_y+bh),(12.35,band_y+bh/2)]
ax.add_patch(Polygon(pts,fc=RED,ec='none',zorder=2))
for tx,lab in [(14.1,'Deterministisch'),(18.75,'Keine LLM-Entscheidung'),(23.6,'Kleiner Realeinsatz'),(28.6,'Wallet-Abgleich')]:
    ax.text(tx,band_y+bh/2,lab,fontsize=12.3,fontweight='bold',color='white',ha='center',va='center',zorder=3)

# Eingangsboxen links
rbox(0.9,12.35,5.1,1.25,RED)
ax.text(1.85,13.25,'Neue Episode',fontsize=13.5,fontweight='bold',color=NAVY,va='center')
ax.text(1.85,12.75,'RSS, YouTube, X-Feed',fontsize=11.5,color=GREY,va='center')
# RSS-Icon
for r_ in (0.28,0.17):
    ax.add_patch(Arc((1.25,12.72),2*r_,2*r_,theta1=0,theta2=90,color=RED,lw=2.2,zorder=3))
ax.add_patch(Circle((1.25,12.72),0.05,color=RED,zorder=3))

rbox(0.9,8.35,5.1,1.25,RED)
ax.text(1.85,9.25,'Orderbücher',fontsize=13.5,fontweight='bold',color=NAVY,va='center')
ax.text(1.85,8.75,'Recorder alle 120 Sekunden',fontsize=11.5,color=GREY,va='center')
ax.add_patch(Rectangle((1.12,8.72),0.42,0.55,ec=BLUE,fc='none',lw=2.0,zorder=3))
for yy in (8.86,9.0,9.14): ax.plot([1.2,1.46],[yy,yy],color=BLUE,lw=1.6,zorder=3)

# Icon-Zeichner
def icon_doc(x,y):
    ax.add_patch(Rectangle((x-0.28,y-0.36),0.56,0.72,ec=BLUE,fc='white',lw=2.4,zorder=3))
    for i,yy in enumerate((y+0.16,y+0.02,y-0.12)):
        ax.plot([x-0.16,x+0.16],[yy,yy],color=BLUE,lw=1.7,zorder=4)
def icon_radar(x,y):
    ax.add_patch(Circle((x,y),0.36,ec=BLUE,fc='white',lw=2.4,zorder=3))
    ax.add_patch(Circle((x,y),0.19,ec=BLUE,fc='white',lw=1.8,zorder=3))
    ax.add_patch(Circle((x+0.07,y+0.07),0.055,color=BLUE,zorder=4))
    ax.plot([x+0.07,x+0.30],[y+0.07,y+0.30],color=BLUE,lw=1.8,zorder=4)
def icon_slider(x,y):
    for dy,dx in ((0.22,-0.10),(0.0,0.12),(-0.22,-0.04)):
        ax.plot([x-0.34,x+0.34],[y+dy,y+dy],color=BLUE,lw=2.0,zorder=3)
        ax.add_patch(Circle((x+dx,y+dy),0.07,color=BLUE,zorder=4))
def icon_lock(x,y):
    ax.add_patch(FancyBboxPatch((x-0.30,y-0.38),0.60,0.48,boxstyle='round,pad=0.01,rounding_size=0.06',fc=BLUE,ec='none',zorder=3))
    ax.add_patch(Arc((x,y+0.10),0.40,0.44,theta1=0,theta2=180,color=BLUE,lw=2.6,zorder=3))
    ax.add_patch(Circle((x,y-0.13),0.065,color='white',zorder=4))
def icon_clip(x,y):
    ax.add_patch(Rectangle((x-0.27,y-0.38),0.54,0.72,ec=BLUE,fc='white',lw=2.4,zorder=3))
    ax.add_patch(Rectangle((x-0.12,y+0.26),0.24,0.14,ec=BLUE,fc='white',lw=2.0,zorder=4))
    for yy in (y+0.08,y-0.06,y-0.20): ax.plot([x-0.15,x+0.15],[yy,yy],color=BLUE,lw=1.6,zorder=4)

def node(x,icon,num,name,l1,l2,extra=None,ul=BLUE,ytop=13.0):
    icon(x,ytop)
    ax.text(x,ytop-0.85,f'{num} {name}',fontsize=14,fontweight='bold',color=NAVY,ha='center',va='center')
    ax.text(x,ytop-1.28,l1,fontsize=10.7,color=GREY,ha='center',va='center')
    ax.text(x,ytop-1.62,l2,fontsize=10.7,color=GREY,ha='center',va='center')
    dotline(x,ytop-2.0,2.3,ul)
    if extra: ax.text(x,ytop-2.42,extra,fontsize=11.3,fontweight='bold',color=RED,ha='center',va='center')

N1,N2,N3=8.2,14.4,20.7
node(N1,icon_doc,'1','Regelverständnis','Komposita und Akronyme kodiert,','Homophone ab Konfidenz 0.8',extra='Stimmprofil-Abgleich, Schwelle 0.40',ul=RED)
node(N2,icon_radar,'2','Erkennung','CDN-Abfrage vor RSS vor YouTube,','X-Feed, GPU-Blöcke à 20 s')
node(N3,icon_slider,'3','Ausführung','FAK-Clips bis Deckel 0.90,','Nein-Deckel 0.80 nach Episodenende')
arrow(6.15,13.0,N1-0.75,13.0); arrow(N1+0.75,13.0,N2-0.75,13.0); arrow(N2+0.75,13.0,N3-0.75,13.0)

Y2=9.0
node(N2,icon_clip,'5','Auswertung','Run-Logs nur lesend, Trade-Tape,','Wallet-Abgleich durchgehend',ytop=Y2+0.35)
node(N3,icon_lock,'4','Risiko-Disziplin','Budget je Profil, Stop-Datei, Watchdog','im 5-Min-Takt, Nachlauf-Fenster 45 Min',ul=RED,ytop=Y2+0.35)
arrow(N3,10.85,N3,Y2+0.85)              # 3 -> 4
arrow(N3-1.35,Y2+0.35,N2+0.75,Y2+0.35)  # 4 -> 5
arrow(6.15,9.0,N2-0.85,9.0)             # Orderbücher -> 5

# Ergebnisboxen rechts
def resbox(y,t1,t2,ec=RED):
    rbox(25.7,y,5.4,1.25,ec)
    ax.text(25.95,y+0.86,t1,fontsize=11.6,fontweight='bold',color=NAVY,va='center')
    ax.text(25.95,y+0.38,t2,fontsize=10.4,color=GREY,va='center')
resbox(12.55,'8 Läufe, 15 Wetten, 12 Märkte','14 gewonnen, 1 verloren')
resbox(10.75,'Erstkäufer bei 11 von 15 Wetten','E281: 6 von 6, Verfolger +18 Min')
resbox(8.95,'+175 USD netto (Wallet)','Einsatz 67% der sichtbaren Tiefe')
b=rbox(25.7,6.95,5.4,1.35,BORD,fc=LGREY,lw=1.6)
ax.text(25.95,7.95,'Prozess- und Latenzevidenz,',fontsize=12,fontweight='bold',color=NAVY,va='center')
ax.text(25.95,7.55,'kein Strategie- und kein',fontsize=11.3,color=GREY,va='center')
ax.text(25.95,7.18,'Renditenachweis',fontsize=11.3,color=GREY,va='center')
# Sammel-Verbinder
trunk_x=25.05
ax.plot([N2,N2],[6.9,6.35],color='#2c3e50',lw=2.0,zorder=1)
ax.plot([N2,trunk_x],[6.35,6.35],color='#2c3e50',lw=2.0,zorder=1)
ax.plot([trunk_x,trunk_x],[6.35,13.15],color='#2c3e50',lw=2.0,zorder=1)
for yy in (13.15,11.35,9.55): arrow(trunk_x,yy,25.62,yy)

# Vorfalls-Leiste
b=rbox(0.9,4.55,19.3,1.35,BORD,fc=LGREY,lw=1.6)
ax.text(1.25,5.55,'Aus Vorfällen nachgerüstet (kuratierte Vorfall-Liste):',fontsize=12.5,fontweight='bold',color=NAVY,va='center')
ax.text(1.25,5.05,'Playlist-Prüfung, 45-Min-Nachlauf, Watchdog, Budget-Sync, Wallet-Abgleich. Jeder Fix verifiziert und datiert.',fontsize=11.6,color=GREY,va='center')

# Chevrons unten
labels=['Regeln','Erkennen','Ausführen','Absichern','Auswerten']
cw,gap,x0,cy,ch=5.55,0.35,0.9,1.7,1.15
for i,lab in enumerate(labels):
    x=x0+i*(cw+gap); notch=0.55
    pts=[(x,cy),(x+cw-notch,cy),(x+cw,cy+ch/2),(x+cw-notch,cy+ch),(x,cy+ch)]
    if i>0: pts.append((x+notch,cy+ch/2))
    ax.add_patch(Polygon(pts,fc='white',ec=BLUE,lw=2.4,zorder=2))
    ax.text(x+cw/2+(0.12 if i>0 else 0),cy+ch/2,lab,fontsize=15,fontweight='bold',color=NAVY,ha='center',va='center',zorder=3)

plt.tight_layout(pad=0.4)
fig.savefig('/tmp/work/abb19_neu.png',dpi=200,facecolor='white',bbox_inches=None)
print('ok')
