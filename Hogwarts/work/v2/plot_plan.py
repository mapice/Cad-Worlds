"""Tavola originale della disposizione studiata per il modello Blender HBP.
Nessuna immagine di riferimento incorporata; coordinate lette dalla pianta EE2109.
"""
from pathlib import Path
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
ROOT=Path('/Users/mattiaapicella/Documents/Codex/2026-10-26/il-ca')
OUT=ROOT/'outputs'
BG='#F6F2E9'; INK='#273A3D'; EDGE='#655D50'
C={'sud':'#B78D61','nord':'#99ACA0','ovest':'#AD939E','torri':'#827E9C','ponti':'#CAB58C','serre':'#B9D5D0','roccia':'#E4DECE','terra':'#E1E5D4','acqua':'#D9E9E8','cortile':'#FAF7EF'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':INK})
fig=plt.figure(figsize=(12.5,10),dpi=160,facecolor=BG)
ax=fig.add_axes([.035,.12,.705,.745]);ax.set_facecolor(BG)
def xy(u,v):return((u-.5)*600,(.55-v)*382)
def poly(uv,fc,ec=EDGE,lw=.8,z=2,alpha=1):
 p=Polygon([xy(*a) for a in uv],closed=True,facecolor=fc,edgecolor=ec,lw=lw,zorder=z,alpha=alpha);ax.add_patch(p);return p
def rect(u,v,L,W,fc,angle=0,ec=EDGE,lw=.8,z=6):
 x,y=xy(u,v);c=math.cos(angle);s=math.sin(angle)
 pts=[(x+a*c-b*s,y+a*s+b*c) for a,b in [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]]
 p=Polygon(pts,closed=True,facecolor=fc,edgecolor=ec,lw=lw,zorder=z);ax.add_patch(p);return pts
def circle(u,v,r,fc,ec=EDGE,lw=.8,z=7):
 ax.add_patch(Circle(xy(u,v),r,facecolor=fc,edgecolor=ec,lw=lw,zorder=z))
def line(a,b,color,width=1,z=9,style='-'):
 a=xy(*a);b=xy(*b);ax.plot([a[0],b[0]],[a[1],b[1]],color=color,lw=width,zorder=z,ls=style,solid_capstyle='round')
def bridge(a,b,width=4.7):
 aa=xy(*a);bb=xy(*b);L=math.dist(aa,bb);u=(a[0]+b[0])/2;v=(a[1]+b[1])/2
 rect(u,v,L,width,C['ponti'],math.atan2(bb[1]-aa[1],bb[0]-aa[0]),z=12)
def roofline(u,v,L,W,ang=0):
 x,y=xy(u,v);dx=math.cos(ang)*L/2;dy=math.sin(ang)*L/2
 ax.plot([x-dx,x+dx],[y-dy,y+dy],color='#746A57',lw=.5,zorder=8,alpha=.55)
def building(u,v,L,W,color,ang=0):rect(u,v,L,W,color,ang);roofline(u,v,L,W,ang)
# Terreno e acqua: masse leggibili e due promontori separati da una gola.
lake=[(.40,.60),(.50,.50),(.63,.42),(.81,.43),(.88,.60),(.89,.94),(.82,1.02),(.48,1.03),(.43,.91)]
poly(lake,C['acqua'],ec='#B8D4D3',lw=1,z=0)
west=[(.045,.66),(.095,.85),(.25,.96),(.399,.948),(.41,.80),(.41,.64),(.465,.56),(.468,.45),(.49,.30),(.505,.10),(.455,.015),(.38,.018),(.30,.16),(.17,.32),(.10,.48)]
south=[(.421,.604),(.495,.601),(.552,.623),(.563,.738),(.608,.766),(.647,.816),(.657,.872),(.602,.928),(.565,.979),(.487,.993),(.461,.954),(.478,.848),(.421,.826),(.413,.771),(.414,.651)]
north=[(.483,.535),(.491,.296),(.518,.174),(.612,.159),(.720,.179),(.723,.437),(.787,.491),(.748,.628),(.673,.652),(.575,.637),(.557,.548)]
poly(west,C['terra'],ec='#BFC7B2',lw=1,z=1)
poly(south,C['roccia'],ec='#C4B9A5',lw=1.1,z=2);poly(north,C['roccia'],ec='#C4B9A5',lw=1.1,z=2)
# Quad: quattro ali, cortile centrale volutamente vuoto.
rect(.487,.718,75,74,C['roccia'],ec='#D2C7B3',lw=.5,z=3)
rect(.487,.718,36,39,C['cortile'],ec='#DDD5C6',lw=.5,z=4)
for u,v,L,W,a in [(.481,.640,61,13,0),(.438,.714,65,14,math.pi/2),(.481,.788,54,14,0),(.532,.706,59,14,math.pi/2)]:building(u,v,L,W,C['sud'],a)
for u,v,r in [(.428,.620,8.5),(.540,.632,7.2),(.429,.799,5.7)]:circle(u,v,r,C['sud'])
circle(.536,.804,16.8,C['torri'])
a=math.atan2(.072*382,.066*600)
building(.525,.922,50,17,C['sud'],a);building(.548,.868,25,13,C['sud'],math.pi/2)
# Cortile del viadotto con tre ali basse e centro chiaro.
rect(.596,.852,45,33,C['ponti'],a,z=5);rect(.596,.852,38,26,C['cortile'],a,ec='#CCBFA9',lw=.5,z=6)
# Orologio e cortile: medesima disposizione dei moduli Blender.
building(.382,.7105,.101*382,.036*600,C['ovest'],math.pi/2)
rect(.332,.7135,.066*600,.085*382,C['ovest'],z=5)
rect(.332,.7135,.066*600-7,.085*382-7,C['cortile'],ec='#D8CBD0',lw=.5,z=6)
circle(.332,.7135,2.8,C['acqua'],ec='#9EAFA8',z=8)
bridge((.399,.710),(.430,.710),6.3)
bridge((.174,.713),(.300,.713),5.1)
for i in range(10):
 u=.174+.126*i/9;line((u,.708),(u,.718),'#A48D6D',.55,13)
circle(.182,.354,7.5,C['ovest'])
for i in range(9):
 t=2*math.pi*i/9;x,y=xy(.145,.713);ax.add_patch(Circle((x+7.8*math.cos(t),y+7.8*math.sin(t)),1.25,facecolor='#8F9784',edgecolor=EDGE,lw=.5,zorder=7))
line((.155,.713),(.174,.713),'#CABFA5',3.5,6)
# Ala Durham con cortile interno e ali edificate.
building(.626,.385,.15*382,28,C['nord'],math.pi/2)
building(.550,.317,60,10,C['nord'])
building(.503,.391,57,9,C['nord'],math.pi/2)
building(.595,.388,44,6.5,C['nord'],math.pi/2)
rect(.553,.394,.068*600,.104*382,C['cortile'],ec='#C9D0C6',lw=.7,z=4)
# Chiostri sottili lungo i tre lati; il bordo sud lascia il posto all'Astronomia.
for aa,bb in [((.522,.351),(.584,.351)),((.522,.351),(.522,.437)),((.584,.351),(.584,.437))]:
 bridge(aa,bb,3.7)
for u,v,L,W,ang in [(.626,.523,.046*382,21,math.pi/2),(.603,.515,21,9,0),(.507,.483,15,10,math.pi/2),(.521,.523,31,9,0)]:building(u,v,L,W,C['nord'],ang)
# Astronomia: corpo a D e belvedere laterale.
rect(.552,.457,21,17,C['torri'],z=7)
circle(.552,.446,10.5,C['torri'],z=7)
circle(.573,.457,4.0,C['torri'],z=7)
rect(.626,.484,20.4,20.4,C['torri'],z=9)
for u in [.604,.649]:rect(u,.288,14.4,14.4,C['torri'],z=9)
# Ingresso del viadotto, portale indicato da un taglio centrale chiaro.
rect(.6265,.571,.097*600,.050*382,C['nord'],z=7)
rect(.6265,.571,7.2,.050*382+1,C['cortile'],ec='none',z=8)
for u,v in [(.578,.546),(.675,.546),(.578,.596),(.675,.596)]:circle(u,v,5,C['torri'],z=9)
# Serre: pannelli distinti e nervature suggerite in pianta.
for u,v,L,W,ang in [(u,v,.061*600,.019*382,0) for u,v in [(.578,.220),(.578,.250),(.672,.220),(.672,.250)]]+[(u,v,.086*382,.013*600,math.pi/2) for u,v in [(.679,.313),(.699,.313),(.679,.407),(.699,.407)]]+[(.568,.276,.046*600,.012*382,0)]:
 rect(u,v,L,W,C['serre'],ang,ec='#66908D',lw=.7,z=7)
 x,y=xy(u,v);c=math.cos(ang);s=math.sin(ang)
 for j in range(1,7):
  q=-L/2+j*L/7;aa=(x+q*c-W/2*s,y+q*s+W/2*c);bb=(x+q*c+W/2*s,y+q*s-W/2*c)
  ax.plot([aa[0],bb[0]],[aa[1],bb[1]],color='#7BA49F',lw=.45,zorder=8)
circle(.625,.198,6.2,C['serre'],ec='#66908D',z=8)
# Cinta del campo settentrionale.
cinta=[(.533,.185),(.481,.041),(.465,.020),(.390,.033),(.335,.145),(.316,.170)]
for aa,bb in zip(cinta,cinta[1:]):bridge(aa,bb,1.8)
for u,v in [(.481,.041),(.465,.020),(.390,.033),(.335,.145)]:circle(u,v,4,C['nord'])
building(.316,.173,15,10,C['nord'],.65)
# I tre collegamenti tra le ali, nessuno sostituito dal ponte DH verso l'esterno.
bridge((.602,.769),(.626,.597),5.2)
cx,cy=xy(.596,.852);px=cx+12*math.cos(a)-15*math.sin(a);py=cy+12*math.sin(a)+15*math.cos(a)
bridge((px/600+.5,.55-py/382),(.602,.769),7)
bridge((.539,.633),(.577,.592),5)
bridge((.500,.614),(.500,.529),3.3)
# Rimessa e scalinata con pianerottoli lungo il versante.
building(.793,.906,21.7,13,C['sud']);circle(.802,.891,3.1,C['torri'])
route=[(.639,.879),(.617,.909),(.664,.929),(.687,.900),(.671,.835),(.699,.816),(.733,.845),(.758,.881),(.785,.891)]
for aa,bb in zip(route,route[1:]):bridge(aa,bb,2.9)
# Contesto, in caratteri discreti.
x,y=xy(.332,.423);ax.text(x,y,'COLLINE',color='#839075',fontsize=11,ha='center',va='center',weight='medium')
x,y=xy(.424,.123);ax.text(x,y,'CAMPO\nSETTENTRIONALE',color='#839075',fontsize=8.8,ha='center',va='center',linespacing=1.5)
x,y=xy(.792,.774);ax.text(x,y,'LAGO NERO',color='#6D9699',fontsize=11,ha='center',rotation=0)
x,y=xy(.459,.586);ax.text(x,y,'GOLA',color='#A3957E',fontsize=8,ha='center',rotation=33)
# Numeri e rimandi: tutti esterni alle sagome salvo cortili aperti.
marks=[
(1,(.525,.922),(.471,1.005)),(2,(.536,.804),(.480,.855)),(3,(.487,.718),(.487,.718)),
(4,(.382,.7105),(.351,.810)),(5,(.239,.713),(.238,.772)),(6,(.145,.713),(.100,.768)),
(7,(.182,.354),(.120,.348)),(8,(.552,.457),(.464,.481)),(9,(.553,.394),(.553,.394)),
(10,(.626,.484),(.755,.478)),(11,(.626,.288),(.770,.282)),(12,(.672,.220),(.752,.167)),
(13,(.6265,.571),(.755,.619)),(14,(.614,.682),(.723,.718)),(15,(.558,.612),(.658,.652)),
(16,(.500,.571),(.442,.555)),(17,(.793,.906),(.841,.968))]
for n,target,label in marks:
 tx,ty=xy(*target);lx,ly=xy(*label)
 if target!=label:
  ax.plot([tx,lx],[ty,ly],color='#617477',lw=.85,zorder=21)
  ax.add_patch(Circle((tx,ty),.9,facecolor='#617477',edgecolor='none',zorder=21))
 ax.scatter([lx],[ly],s=195,facecolor=BG,edgecolor=INK,lw=1.1,zorder=22)
 ax.text(lx,ly,str(n),fontsize=9.3,weight='bold',ha='center',va='center',zorder=23)
# Nord.
x,y=xy(.110,.120)
ax.annotate('',xy=(x,y+14),xytext=(x,y-7),arrowprops={'arrowstyle':'-|>','lw':1.5,'color':INK},zorder=20)
ax.text(x,y+19,'N',ha='center',fontsize=12,weight='bold')
ax.set_xlim(-285,244);ax.set_ylim(-190,218);ax.set_aspect('equal');ax.axis('off')
# Testata.
fig.text(.045,.944,'HOGWARTS',fontsize=26,weight='bold',color=INK)
fig.text(.045,.907,'Ricostruzione della disposizione',fontsize=18,color='#566B69')
fig.text(.735,.944,'PIANTA DEGLI ESTERNI',fontsize=10.5,weight='bold',ha='left',color='#657879')
fig.text(.735,.919,'Riferimento HBP / modellino Studio Tour',fontsize=9.3,ha='left',color='#657879')
# Legenda numerata, suddivisa solo tramite il colore del settore.
leg=fig.add_axes([.762,.15,.215,.705]);leg.axis('off');leg.set_xlim(0,1);leg.set_ylim(0,1)
leg.text(0,1.01,'EDIFICI E COLLEGAMENTI',fontsize=10.3,weight='bold',color=INK)
labels=[('Sala Grande',C['sud']),('Scalinata e ufficio di Silente',C['torri']),('Quad e torre Grifondoro',C['sud']),('Orologio, cortile e infermeria',C['ovest']),('Ponte coperto in legno',C['ponti']),('Cerchio di pietre',C['ovest']),('Civettaia',C['ovest']),('Torre di Astronomia',C['torri']),('Cortile Durham / Trasfigurazione',C['nord']),('Torre centrale',C['torri']),('Coppia dei campanili',C['torri']),('Nove serre e conservatorio',C['serre']),('Ingresso del viadotto',C['nord']),('Viadotto tra le due ali',C['ponti']),('Ponte di pietra alto',C['ponti']),('Ponte sospeso',C['ponti']),('Rimessa e scalinata al lago',C['sud'])]
for i,(label,col) in enumerate(labels):
 yy=.951-i*.0515
 leg.scatter([.037],[yy],s=160,transform=leg.transAxes,facecolor=col,edgecolor='none',clip_on=False)
 leg.text(.037,yy,str(i+1),ha='center',va='center',fontsize=8.4,weight='bold',color=INK,transform=leg.transAxes)
 leg.text(.085,yy,label,ha='left',va='center',fontsize=9.2,transform=leg.transAxes)
leg.text(0,.024,'I vuoti chiari sono cortili aperti.\nI tre ponti attraversano la gola\ntra i due grandi nuclei del castello.',fontsize=9,color='#5F736B',linespacing=1.65,va='top')
fig.lines.append(plt.Line2D([.045,.965],[.100,.100],transform=fig.transFigure,color='#D2CEC1',lw=1))
fig.text(.045,.072,'Ricostruzione della disposizione — riferimento HBP / modellino Studio Tour. Quote e dettagli non certificati.',fontsize=9.4,color='#526866')
fig.text(.045,.046,'Schema originale dalla pianta di produzione EE2109 e dai confronti documentati. Terreno e altezze sono ricostruiti.',fontsize=9,color='#6E7B75')
fig.savefig(OUT/'Hogwarts-pianta-studiata.png',dpi=160,facecolor=BG)
print(OUT/'Hogwarts-pianta-studiata.png')
