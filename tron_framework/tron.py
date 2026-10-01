"""AI Arena: deterministic simultaneous-move Tron, Python standard library only."""
from __future__ import annotations
import argparse, json, random
from collections import deque
from dataclasses import dataclass
from pathlib import Path

DIRECTIONS = ((0,-1),(1,0),(0,1),(-1,0))
@dataclass(frozen=True)
class Rider:
    id: str
    team: str
    color: str
    algorithm: str
    position: tuple[int,int]
    heading: int
    depth: int = 6

def target(p, d):
    dx,dy = DIRECTIONS[d]
    return p[0]+dx,p[1]+dy

class Arena:
    def __init__(self, width, height, riders):
        if width < 5 or height < 5: raise ValueError('Arena must be at least 5x5')
        self.width,self.height = width,height
        self.riders = {r.id:r for r in riders}
        if len(self.riders)!=len(riders) or len(riders)<2: raise ValueError('Need at least two unique rider IDs')
        self.positions = {r.id:r.position for r in riders}
        self.headings = {r.id:r.heading for r in riders}
        self.alive = set(self.riders)
        self.occupied = {}
        self.tick = 0
        for r in riders:
            if not self.inside(r.position) or r.position in self.occupied: raise ValueError('Invalid spawn')
            if r.heading not in range(4): raise ValueError('Invalid heading')
            self.occupied[r.position]=r.id
    def inside(self,p): return 0<=p[0]<self.width and 0<=p[1]<self.height
    def free(self,p): return self.inside(p) and p not in self.occupied
    def legal(self,id):
        return [d for d in range(4) if d!=(self.headings[id]+2)%4 and self.free(target(self.positions[id],d))]
    def step(self, actions):
        # All destinations computed from the same board, then committed together.
        destinations={i:target(self.positions[i],actions[i]) for i in sorted(self.alive)}
        deaths={}
        for i,p in destinations.items():
            d=actions[i]
            if d not in range(4) or d==(self.headings[i]+2)%4: deaths[i]='illegal turn'
            elif not self.inside(p): deaths[i]='wall'
            elif p in self.occupied: deaths[i]='trail'
            elif sum(q==p for q in destinations.values())>1: deaths[i]='head-on'
        for i,p in destinations.items():
            self.headings[i]=actions[i]
            if i not in deaths:
                self.positions[i]=p
                self.occupied[p]=i
        self.alive.difference_update(deaths)
        self.tick+=1
        return deaths
    def snapshot(self):
        return {'tick':self.tick,'positions':{i:list(p) for i,p in self.positions.items()},'alive':sorted(self.alive)}

def distance_map(arena,start,blocked=frozenset()):
    distances={start:0}; queue=deque([start])
    while queue:
        p=queue.popleft()
        for d in range(4):
            q=target(p,d)
            if arena.free(q) and q not in blocked and q not in distances:
                distances[q]=distances[p]+1; queue.append(q)
    return distances

def choose(arena,id,rng):
    rider=arena.riders[id]; options=arena.legal(id)
    if not options: return arena.headings[id]
    opponents=[arena.positions[j] for j in sorted(arena.alive) if j!=id]
    def score(d):
        p=target(arena.positions[id],d)
        # Avoid cells an enemy could enter on the same tick where possible.
        danger=sum(p==target(arena.positions[j],e) for j in sorted(arena.alive) if j!=id for e in arena.legal(j))
        space=distance_map(arena,p)
        mobility=sum(arena.free(target(p,e)) for e in range(4))
        proximity=min((abs(p[0]-q[0])+abs(p[1]-q[1]) for q in opponents),default=0)
        if rider.algorithm=='aggressive':
            value=len(space)*0.15-proximity*3+mobility*2
        elif rider.algorithm=='defensive':
            value=len(space)+mobility*3+proximity*0.3
        elif rider.algorithm=='territory':
            enemy_maps=[distance_map(arena,q) for q in opponents]
            value=sum(all(n<m.get(cell,10**9) for m in enemy_maps) for cell,n in space.items())+mobility*2
        elif rider.algorithm=='lookahead':
            # Bounded beam search of own future trail; enemies are stationary.
            frontier=[(p,d,frozenset([p]))]; best=0
            for depth in range(1,rider.depth+1):
                expanded=[]
                for pos,heading,visited in frontier:
                    best=max(best,depth*100+len(distance_map(arena,pos,visited-{pos})))
                    for e in range(4):
                        q=target(pos,e)
                        if e!=(heading+2)%4 and arena.free(q) and q not in visited:
                            expanded.append((q,e,visited|{q}))
                if not expanded: break
                expanded.sort(key=lambda x:len(distance_map(arena,x[0],x[2]-{x[0]})),reverse=True)
                frontier=expanded[:12]
            value=best
        else: raise ValueError(f'Unknown algorithm: {rider.algorithm}')
        return value-danger*10000
    rng.shuffle(options)
    return max(options,key=score)

def run(config,seed=1,max_ticks=1200):
    if max_ticks<1: raise ValueError('max_ticks must be positive')
    riders=[Rider(**{**r,'position':tuple(r['position'])}) for r in config['riders']]
    for r in riders:
        if r.algorithm not in {'aggressive','defensive','territory','lookahead'}: raise ValueError('Unknown algorithm')
        if not 1<=r.depth<=20: raise ValueError('Depth must be 1..20')
    arena=Arena(config['width'],config['height'],riders); rng=random.Random(seed)
    frames=[arena.snapshot()]
    while len(arena.alive)>1 and arena.tick<max_ticks:
        actions={i:choose(arena,i,rng) for i in sorted(arena.alive)}
        deaths=arena.step(actions)
        frames.append({**arena.snapshot(),'actions':actions,'deaths':deaths})
    winner=next(iter(arena.alive)) if len(arena.alive)==1 else None
    return {'schema_version':1,'seed':seed,'config':config,'frames':frames,'result':{'winner':winner,'reason':'survival' if winner else ('tick_limit' if len(arena.alive)>1 else 'mutual_elimination'),'ticks':arena.tick}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default=str(Path(__file__).with_name('teams.json')))
    parser.add_argument('--seed',type=int,default=1)
    parser.add_argument('--max-ticks',type=int,default=1200)
    parser.add_argument('--output',default='replay.json')
    args=parser.parse_args()
    replay=run(json.loads(Path(args.config).read_text()),args.seed,args.max_ticks)
    Path(args.output).write_text(json.dumps(replay))
    print(json.dumps(replay['result']))
if __name__=='__main__': main()
