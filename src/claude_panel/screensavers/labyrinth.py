
from rich.text import Text
import math
import random
from collections import deque

random.seed()

# ── Procedural maze ──
MZ = 31
maze = [[1] * MZ for _ in range(MZ)]
stk = [(1, 1)]
maze[1][1] = 0
while stk:
    cx, cy = stk[-1]
    nb = []
    for dx, dy in ((0,-2),(2,0),(0,2),(-2,0)):
        nx, ny = cx+dx, cy+dy
        if 1 <= nx < MZ-1 and 1 <= ny < MZ-1 and maze[ny][nx]:
            nb.append((nx, ny, cx+dx//2, cy+dy//2))
    if nb:
        nx, ny, wx, wy = random.choice(nb)
        maze[wy][wx] = maze[ny][nx] = 0
        stk.append((nx, ny))
    else:
        stk.pop()

# ── Diameter path ──
def bfs(sx, sy):
    vis = {(sx,sy): None}
    q = deque([(sx,sy)])
    end = (sx,sy)
    while q:
        c = q.popleft(); end = c
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n = (c[0]+dx, c[1]+dy)
            if 0 <= n[0] < MZ and 0 <= n[1] < MZ and n not in vis and not maze[n[1]][n[0]]:
                vis[n] = c; q.append(n)
    path = []
    while end: path.append(end); end = vis[end]
    path.reverse()
    return path

p1 = bfs(1, 1)
pts = bfs(*p1[-1])
if len(pts) < 2: pts = [(1,1),(1,2)]

dirs = [math.atan2(pts[i+1][1]-pts[i][1], pts[i+1][0]-pts[i][0]) for i in range(len(pts)-1)]
dirs.append(dirs[-1])

# ── Torches ──
torches = set()
random.seed(42)
for i in range(0, len(pts), 4):
    cx, cy = pts[i]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        wx, wy = cx+dx, cy+dy
        if 0 <= wx < MZ and 0 <= wy < MZ and maze[wy][wx]:
            torches.add((wx, wy)); break
random.seed()

# ── Collectible items (placed dead-center in corridor cells) ──
LOOT = [
    ("◆",255,60,60),("◆",60,220,255),("◆",80,255,120),("◆",255,230,50),
    ("●",220,90,255),("●",90,255,200),("☠",230,220,200),("♦",255,200,60),
]
items = []
random.seed(77)
for i in range(4, len(pts), 6):
    cx, cy = pts[i]
    ch, r, g, b = random.choice(LOOT)
    items.append([cx+0.5, cy+0.5, ch, r, g, b, random.uniform(0,6.28), True])
random.seed()

# ── Rats ──
rats = []
random.seed(88)
for i in range(6, len(pts), 14):
    cx, cy = pts[i]
    dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
    rats.append((cx+0.5, cy+0.5, dx, dy, random.uniform(0,6.28)))
random.seed()

# ── Ghosts ──
ghosts = []
random.seed(123)
step = max(1, len(pts)//4)
for i in range(step, len(pts)-step, step):
    cx, cy = pts[i]
    ghosts.append((cx+0.5, cy+0.5, random.uniform(0,6.28)))
random.seed()

# ── Config ──
FOV = math.pi / 3.2
MAXD = 10.0
FPC = 6
RH = height - 2
N = min(len(pts) * FPC, 400)
proj_k = width / (2 * math.tan(FOV / 2))
collected = 0

vig_x = [max(0.4, 1-(2*sx/max(1,width-1)-1)**2*0.45) for sx in range(width)]
vig_y = [max(0.5, 1-(2*y/max(1,RH-1)-1)**2*0.35) for y in range(RH)]

for f in range(N):
    canvas.clear()
    fade = min(1.0, f/15.0) * min(1.0, (N-f-1)/20.0)

    ci = min(f//FPC, len(pts)-2)
    t = (f%FPC)/FPC
    ni = min(ci+1, len(pts)-1)
    cpx = pts[ci][0]+0.5+(pts[ni][0]-pts[ci][0])*t
    cpy = pts[ci][1]+0.5+(pts[ni][1]-pts[ci][1])*t
    da, db = dirs[ci], dirs[ni]
    dd = db-da
    while dd > math.pi: dd -= 2*math.pi
    while dd < -math.pi: dd += 2*math.pi
    ca = da + dd*min(1, t*1.4)

    # ── Collect nearby items ──
    for sp in items:
        if sp[7] and (sp[0]-cpx)**2+(sp[1]-cpy)**2 < 0.15:
            sp[7] = False; collected += 1

    buf = [[" "]*width for _ in range(RH)]
    clr = [[""]*width for _ in range(RH)]
    z_buf = [MAXD]*width

    # ── Raycast ──
    for sx in range(width):
        ra = ca + FOV*(sx/max(1,width-1)-0.5)
        rdx, rdy = math.cos(ra), math.sin(ra)
        cos_fix = math.cos(ra-ca)

        d = 0.0; hit = False
        hx = hy = 0.0; hmx = hmy = 0; side = 0
        while d < MAXD:
            d += 0.06
            rx, ry = cpx+rdx*d, cpy+rdy*d
            mx, my = int(rx), int(ry)
            if not (0 <= mx < MZ and 0 <= my < MZ): break
            if maze[my][mx]:
                hit = True; hx, hy, hmx, hmy = rx, ry, mx, my
                frac = rx-mx; side = 0 if (frac < 0.08 or frac > 0.92) else 1; break

        pd = d*cos_fix if hit else MAXD
        z_buf[sx] = pd
        wh = int(RH/max(0.2, pd))
        wt = max(0,(RH-wh)//2); wb = min(RH, wt+wh)
        fog = max(0, 1-pd/MAXD)
        is_t = hit and (hmx,hmy) in torches
        wtype = ((hmx*7+hmy*13)%4) if hit else 0
        vx = vig_x[sx]

        for y in range(RH):
            v = vx*vig_y[y]*fade
            scan = 0.88 if y%2 else 1.0
            if y < wt:
                cd = RH*0.5/max(0.01,RH*0.5-y)
                cf = max(0,1-cd/MAXD)*0.35*v*scan
                r=int(cf*40+4); g=int(cf*30+3); b=int(cf*25+5)
                clr[y][sx] = f"rgb({r},{g},{b})"
                if cf > 0.15 and random.random() < 0.006: buf[y][sx] = "·"
            elif y < wb:
                s = fog*(0.65 if side else 1.0)*v
                wu = (hx+hy)%1.0 if hit else 0
                wv = (y-wt)/max(1,wh)
                br = int(wv*4); bu = wu+(0.5 if br%2 else 0)
                mortar = (wv*4)%1 < 0.12 or (bu*2)%1 < 0.1
                s *= 0.3 if mortar else 1.0
                tg = fog*0.7*(0.65+0.35*math.sin(f*0.22+sx*0.04))*v if is_t else 0
                if wtype==1: r=min(255,int(s*100+18+tg*130)); g=min(255,int(s*140+20+tg*110)); b=min(255,int(s*65+12+tg*20))
                elif wtype==2: r=min(255,int(s*85+16+tg*130)); g=min(255,int(s*100+15+tg*110)); b=min(255,int(s*140+20+tg*60))
                elif wtype==3: r=min(255,int(s*160+22+tg*180)); g=min(255,int(s*80+12+tg*90)); b=min(255,int(s*55+10+tg*20))
                else: r=min(255,int(s*145+22+tg*180)); g=min(255,int(s*110+16+tg*110)); b=min(255,int(s*65+10+tg*20))
                r=int(r*scan); g=int(g*scan); b=int(b*scan)
                buf[y][sx] = "█" if s>0.42 else "▓" if s>0.25 else "▒" if s>0.1 else "░"
                clr[y][sx] = f"rgb({r},{g},{b})"
            else:
                fd = RH*0.5/max(0.01,y-RH*0.5)
                ad = fd/max(0.01,cos_fix)
                ffx=cpx+rdx*ad; ffy=cpy+rdy*ad
                ff = max(0,1-fd/MAXD)*0.6*v*scan
                ck = (int(ffx)+int(ffy))%2
                if ck: iv=int(ff*70+14); r,g,b=min(255,iv+8),iv,max(0,iv-4)
                else: iv=int(ff*40+8); r,g,b=min(255,iv+4),iv,max(0,iv-2)
                clr[y][sx] = f"rgb({r},{g},{b})"
                if random.random()<0.018 and ff>0.12: buf[y][sx]=random.choice(["·","∙",","])

    # ── Sprites (far → near) ──
    cos_ca=math.cos(ca); sin_ca=math.sin(ca)
    all_sp = []
    for sp in items:
        if sp[7]:
            dx,dy = sp[0]-cpx, sp[1]-cpy
            all_sp.append((dx*dx+dy*dy, "i", sp))
    for rat in rats:
        rx = rat[0]+rat[2]*math.sin(f*0.08+rat[4])*0.4
        ry = rat[1]+rat[3]*math.sin(f*0.08+rat[4])*0.4
        dx,dy = rx-cpx, ry-cpy
        all_sp.append((dx*dx+dy*dy, "r", (rx,ry,rat[4])))
    for gh in ghosts:
        dx,dy = gh[0]-cpx, gh[1]-cpy
        all_sp.append((dx*dx+dy*dy, "g", gh))
    all_sp.sort(key=lambda x: -x[0])

    for dsq, kind, sp in all_sp:
        if kind=="i": dx,dy = sp[0]-cpx, sp[1]-cpy
        elif kind=="r": dx,dy = sp[0]-cpx, sp[1]-cpy
        else: dx,dy = sp[0]-cpx, sp[1]-cpy

        tz = dx*cos_ca+dy*sin_ca
        tx = -dx*sin_ca+dy*cos_ca
        if tz < 0.3: continue
        dist = math.sqrt(dsq)
        scr_x = int(width*0.5 + tx/tz*proj_k)

        if kind == "i":
            # ── BIG bright items with halo ──
            bob = math.sin(f*0.12+sp[6])*0.08
            scr_y = int(RH*0.5 + (0.5-0.32-bob)*RH/tz)
            # Minimal dimming - items glow bright even at distance
            dim = max(0.4, 1 - dist/MAXD) * fade
            r,g,b = int(sp[3]*dim), int(sp[4]*dim), int(sp[5]*dim)
            # Sprite width scales with distance (wider when close)
            sprite_hw = max(1, int(2.5 / tz))  # half-width in columns
            sprite_hh = max(1, int(1.5 / tz))  # half-height in rows

            for sdx in range(-sprite_hw, sprite_hw+1):
                for sdy in range(-sprite_hh, sprite_hh+1):
                    px, py = scr_x+sdx, scr_y+sdy
                    if 0<=px<width and 0<=py<RH and tz<z_buf[px]:
                        if sdx==0 and sdy==0:
                            buf[py][px] = sp[2]
                            clr[py][px] = f"bold rgb({r},{g},{b})"
                        elif abs(sdx)<=1 and abs(sdy)<=1:
                            # Inner glow - bright
                            gr,gg,gb = max(1,r*2//3), max(1,g*2//3), max(1,b*2//3)
                            if buf[py][px] in (" ","·","∙",",","░"):
                                buf[py][px] = "∗"
                                clr[py][px] = f"rgb({gr},{gg},{gb})"
                        else:
                            # Outer glow - softer
                            gr,gg,gb = max(1,r//3), max(1,g//3), max(1,b//3)
                            if buf[py][px] in (" ","·","∙",",","░"):
                                buf[py][px] = "·"
                                clr[py][px] = f"rgb({gr},{gg},{gb})"

        elif kind == "r":
            # ── Bright rats with animation ──
            scr_y = int(RH*0.5 + 0.40*RH/tz)
            dim = max(0.5, 1-dist/MAXD) * fade
            anim = (f+int(sp[2]*10)) % 8
            ch = "🐀" if False else ("~≈~" if anim<4 else "≈~≈")  # 3-char rat
            rv = int(200*dim); gv = int(150*dim); bv = int(80*dim)
            rat_hw = max(1, int(1.5/tz))
            for sdx in range(-rat_hw, rat_hw+1):
                px, py = scr_x+sdx, scr_y
                if 0<=px<width and 0<=py<RH and tz<z_buf[px]:
                    rc = "~" if (sdx+anim)%2==0 else "≈"
                    buf[py][px] = rc
                    clr[py][px] = f"bold rgb({rv},{gv},{bv})"
            # Eyes above
            ey = scr_y - 1
            if 0<=scr_x<width and 0<=ey<RH and tz<z_buf[scr_x]:
                buf[ey][scr_x] = "°°"[0]
                clr[ey][scr_x] = f"bold rgb(255,{int(100*dim)},0)"

        else:
            # ── Ghost: wide, tall, eerie ──
            sway = math.sin(f*0.04+sp[2])*0.2
            gsx = int(width*0.5+(tx+sway)/tz*proj_k)
            gh_h = max(2, int(RH*0.6/tz))
            gh_top = int(RH*0.5-gh_h*0.65)
            gh_bot = int(RH*0.5+gh_h*0.25)
            # Visible at medium distance, fades in/out
            gvis = max(0, min(1, (dist-1.5)/2.5)) * 0.7
            gvis *= 0.4+0.6*math.sin(f*0.03+sp[2])
            ghost_hw = max(1, int(2.0/tz))
            if gvis > 0.05:
                for gxo in range(-ghost_hw, ghost_hw+1):
                    gxx = gsx+gxo
                    edge_fade = 1.0 - abs(gxo)/max(1,ghost_hw+1)
                    gv = int(gvis*fade*100*edge_fade)
                    gvb = int(gvis*fade*140*edge_fade)
                    for gy in range(max(0,gh_top), min(RH,gh_bot)):
                        if 0<=gxx<width and tz<z_buf[gxx]:
                            # Face hint at top
                            is_face = (gy == gh_top+1 and abs(gxo) == max(1, ghost_hw//2))
                            if is_face:
                                buf[gy][gxx] = "●"
                                clr[gy][gxx] = f"bold rgb({min(255,gv+80)},{min(255,gv+80)},{min(255,gvb+100)})"
                            else:
                                buf[gy][gxx] = "░"
                                clr[gy][gxx] = f"rgb({gv},{gv},{gvb})"

    # ── Crosshair ──
    ch_y, ch_x = RH//2, width//2
    if 0<=ch_y<RH and 1<=ch_x<width-1:
        buf[ch_y][ch_x]="+"; clr[ch_y][ch_x]="bold rgb(255,255,255)"
        buf[ch_y][ch_x-1]="—"; clr[ch_y][ch_x-1]="rgb(200,200,200)"
        buf[ch_y][ch_x+1]="—"; clr[ch_y][ch_x+1]="rgb(200,200,200)"

    # ── Minimap ──
    ms = min(6, width//8, RH//4)
    if ms >= 3:
        mx0 = width-ms*2-3; my0 = 1
        for bx in range(mx0-1, mx0+ms*2+1):
            if 0<=bx<width:
                if 0<=my0-1<RH: buf[my0-1][bx]="─"; clr[my0-1][bx]="rgb(40,55,40)"
                if 0<=my0+ms<RH: buf[my0+ms][bx]="─"; clr[my0+ms][bx]="rgb(40,55,40)"
        for by in range(my0-1, my0+ms+1):
            if 0<=by<RH:
                if 0<=mx0-1<width: buf[by][mx0-1]="│"; clr[by][mx0-1]="rgb(40,55,40)"
                bx2=mx0+ms*2
                if 0<=bx2<width: buf[by][bx2]="│"; clr[by][bx2]="rgb(40,55,40)"
        for mmy in range(ms):
            for mmx in range(ms):
                wx=int(cpx)-ms//2+mmx; wy=int(cpy)-ms//2+mmy
                qx,qy = mx0+mmx*2, my0+mmy
                if 0<=qx<width and 0<=qy<RH:
                    if wx==int(cpx) and wy==int(cpy): buf[qy][qx]="◉"; clr[qy][qx]="bold rgb(80,255,80)"
                    elif 0<=wx<MZ and 0<=wy<MZ:
                        if maze[wy][wx]: buf[qy][qx]="█"; clr[qy][qx]="rgb(60,50,40)"
                        else: buf[qy][qx]="·"; clr[qy][qx]="rgb(30,40,25)"

    # ── Render ──
    for y in range(RH):
        line = Text()
        for x in range(width):
            c = clr[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    # ── HUD ──
    hbar = Text()
    hbar.append("═"*width, style="rgb(50,70,50) on rgb(2,4,2)")
    canvas.write(hbar)

    lvl = f//100+1; hp = max(15,100-(f%80))
    compass = ["E","SE","S","SW","W","NW","N","NE"]
    ci2 = int(((math.degrees(ca)%360)+22.5)/45)%8
    depth = f"{pd:.1f}" if hit else "??"
    info = f" ■ LVL {lvl}  ♥ {hp}%  ◆ {collected}  ⌖ {int(cpx):02},{int(cpy):02}  ↕ {depth}  ◈ {compass[ci2]:>2}"
    hl = Text()
    hl.append(info, style="bold rgb(30,200,30) on rgb(2,4,2)")
    hl.append(" "*max(0, width-len(info)), style="on rgb(2,4,2)")
    canvas.write(hl)

    await sleep(0.05)
