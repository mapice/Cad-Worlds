import math,bpy
from architecture import *

def build():
 collection('01 • Sala Grande e ingresso')
 x,y=xy(.525,.922); z=60; a=math.atan2(.072*382,.066*600); L=50; W=17; H=34; RH=24
 box('Sala Grande | muratura',(x,y,z+H/2),(L,W,H),'stone',a)
 gable('Sala Grande | timpani',(x,y,z+H),L,W,RH,'stone',a)
 gable('Sala Grande | tetto',(x,y,z+H+.2),L+1.1,W+1.2,RH,'roof',a)
 def pt(u,v,zz): return (x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a),zz)
 for side in [-1,1]:
  for i in range(10):
   u=-L/2+3+i*(L-6)/9
   window('Sala Grande | vetrata',pt(u,side*(W/2+.08),z+7),2.25,21,a if side<0 else a+math.pi,True)
  for i in range(11):
   u=-L/2+1.1+i*(L-2.2)/10
   box('Sala Grande | contrafforte',pt(u,side*(W/2+.65),z+15.7),(1.05,1.6,31.4),'stone',a)
   cone('Sala Grande | pinnacolo',pt(u,side*(W/2+.65),z+31.4),.6,.02,6,'trim',8)
  box('Sala Grande | mensola gronda',pt(0,side*(W/2+.15),z+H-.5),(L+1,.65,1),'trim',a)
  for i in range(8):
   u=-L/2+4+i*(L-8)/7;v=side*W*.31;zz=z+H+RH*.38
   window('Sala Grande | abbaino',pt(u,v,zz),1.0,2.2,a if side<0 else a+math.pi)
   gable('Sala Grande | cuffia abbaino',pt(u,v,zz+2.2),2.4,2.3,2,'roof',a+math.pi/2)
 for side in [-1,1]:
  u=side*(L/2+.1); angle=a+math.pi/2 if side>0 else a-math.pi/2
  window('Sala Grande | grande finestra terminale',pt(u,0,z+8),8.3,26,angle,True)
  for v in [-W/2,W/2]:turret('Sala Grande | guglia terminale',pt(u,v,z+22),1.3,15,12,False)
  beam('Sala Grande | pinnacolo di colmo',pt(u,0,z+H+RH),pt(u,0,z+H+RH+8),.25,'trim')
 # Lanterna ottagonale sulla copertura.
 cone('Sala Grande | lanterna',pt(4,0,z+H+RH-1),2.2,2.2,5,'stone',8)
 spire('Sala Grande | copertura lanterna',pt(4,0,z+H+RH+4),2.7,9,8)
 # Ingresso fra la torre della scalinata e l'estremità nordest della sala.
 building('Sala d’ingresso',loc(.548,.868,60),25,13,25,15,math.pi/2,2,5)
 # Portale della Sala Grande con orologio piccolo sul timpano d'ingresso.
 pp=pt(L/2+.4,0,z+7); panel('Portale della Sala Grande',pp,5,12,a+math.pi/2,'wood',.2)
 
 collection('02 • Torre della Scalinata e ufficio di Silente')
 x,y=xy(.536,.804);z=60;r=16.8;H=86
 cone('Torre della Scalinata | fusto',(x,y,z),r,r,H,'stone',96)
 for zz,rr in [(z+2,r+.6),(z+31,r+.35),(z+60,r+.35),(z+H-2.8,r+.9)]:cone('Scalinata | fascia di pietra',(x,y,zz),rr,rr,1.0,'trim',96)
 round_windows('Scalinata | finestra',(x,y,z+6),r,8,18,1.0,2.2,9.6)
 for i in range(54):
  aa=2*math.pi*i/54
  box('Scalinata | mensola merlata',(x+(r+.35)*math.cos(aa),y+(r+.35)*math.sin(aa),z+H-2.0),(1.0,1.3,2.5),'trim',aa)
 spire('Scalinata | grande guglia',(x,y,z+H),r+1.3,70,96,10)
 beam('Scalinata | asta terminale',(x,y,z+H+70),(x,y,z+H+81),.17,'gold')
 # Ufficio di Silente: tre torrette ravvicinate sul medesimo lato sudoccidentale.
 for i,(aa,dz) in enumerate([(3.55,0),(3.87,6),(4.19,1)]):
  xx=x+(r-.3)*math.cos(aa);yy=y+(r-.3)*math.sin(aa);zz=z+H-18+dz
  cone('Silente | mensola',(xx,yy,zz-9),.7,3.5,9,'trim',32)
  turret('Silente | torretta '+str(i+1),(xx,yy,zz),3.4,13,20)
 
 collection('03 • Quadrilatero, infermeria e Grifondoro')
 # Blocchi di più piani intorno al cortile aperto rialzato.
 x0,y0=xy(.487,.718)
 box('Quad | fondazione',(x0,y0,66.5),(75,74,13),'stone')
 box('Quad | pavimentazione',(x0,y0,73.2),(36,39,.8),'path')
 building('Quad | ala nord',loc(.481,.640,73),61,13,33,20,0,3,11)
 building('Quad | ala ovest',loc(.438,.714,73),65,14,33,20,math.pi/2,3,12)
 building('Quad | ala sud',loc(.481,.788,73),54,14,35,21,0,3,10)
 building('Quad | ala est',loc(.532,.706,73),59,14,36,21,math.pi/2,3,11)
 # Arco alto sul lato orientale, riconoscibile anche dal viadotto.
 xq,yq=xy(.532,.744)
 arch('Quad | arco esterno',(xq+7.15,yq,78),9,17,1.4,math.pi/2,3)
 for yy in [yq-5.2,yq+5.2]:box('Quad | piedritto arco',(xq+7.15,yy,86.5),(1.4,1.3,17),'trim')
 turret('Grifondoro | torre nordoccidentale',loc(.428,.620,73),8.5,57,31)
 turret('Quad | torre del ponte alto',loc(.540,.632,73),7.2,47,26)
 turret('Quad | torre sudoccidentale',loc(.429,.799,60),5.7,53,28)
 # Guglie d'angolo sulle ali; posizione non confusa con la torre principale.
 for u,v in [(.449,.622),(.512,.621),(.553,.651),(.448,.794)]:turret('Quad | torretta angolare',loc(u,v,99),2.2,17,12,False)

 collection('04 • Cortile del viadotto')
 x,y=xy(.596,.852);a=math.atan2(.072*382,.066*600);L=42;W=30;z=60
 def p(u,v):return(x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a))
 box('Cortile viadotto | terrazza',(x,y,z-1.05),(L+3,W+3,2.4),'stone',a)
 box('Cortile viadotto | lastre',(x,y,z+.12),(L,W,.24),'path',a)
 # Cortile esterno basso, distinto dal Quad chiuso e più alto.
 for aa,bb in [((-L/2,-W/2),(L/2,-W/2)),((L/2,-W/2),(L/2,W/2)),((-L/2,-W/2),(-L/2,W/2))]:arcade('Cortile viadotto | chiostro',p(*aa),p(*bb),z,7.5,4.8,2.5,2.5)
 for u,v in [(-L/2,-W/2),(L/2,-W/2)]:turret('Cortile viadotto | torretta',(*p(u,v),z),2.4,10,9)
 # Spazio di raccordo al viadotto settentrionale.
 q=xy(.602,.769);t=p(12,15)
 wall('Accesso viadotto | basamento',t,q,z-3,3.3,7,'stone')
 # File sobrie di pietre nel cortile.
 for u in [-12,-6,0,6,12]:wall('Cortile viadotto | giunto',p(u,-12),p(u,12),z+.25,.04,.06,'trim')

 collection('05 • Tre ponti sulla gola')
 bridge('Viadotto',xy(.602,.769),xy(.626,.597),60,9,5.2,10)
 bridge('Ponte di pietra alto',xy(.539,.633),xy(.577,.592),83,19,5,3)
 # Raccordo inclinato dal ponte alto al portale dell'ingresso.
 # Ponte sospeso secondario a ovest, con catene incurvate.
 a=xy(.500,.614);b=xy(.500,.529);L=math.dist(a,b)
 box('Ponte sospeso | tavolato',((a[0]+b[0])/2,(a[1]+b[1])/2,78),(3.3,L,.6),'wood')
 for side in [-1,1]:
  for i in range(18):
   t=i/17;yy=a[1]+(b[1]-a[1])*t;zz=81-2.1*math.sin(math.pi*t)
   beam('Ponte sospeso | montante',(a[0]+side*1.6,yy,78.3),(a[0]+side*1.6,yy,zz),.1,'wood')
   if i:
    t0=(i-1)/17;beam('Ponte sospeso | catena',(a[0]+side*1.6,a[1]+(b[1]-a[1])*t0,81-2.1*math.sin(math.pi*t0)),(a[0]+side*1.6,yy,zz),.11,'gold')
