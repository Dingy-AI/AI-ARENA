"""Run all pairs of AI Arena teams. Place beside tron.py; Python 3.10+."""
import argparse
import csv
import itertools
import json
from pathlib import Path
from tron import run

DEFAULT_TEAMS = [
    {'id':'red_1','team':'Red','color':'#ff5268','algorithm':'aggressive'},
    {'id':'blue_1','team':'Blue','color':'#55aaff','algorithm':'defensive'},
    {'id':'green_1','team':'Green','color':'#63df91','algorithm':'territory'},
    {'id':'yellow_1','team':'Yellow','color':'#ffda64','algorithm':'lookahead','depth':6},
]

def tournament(teams, output, games=2, seed=42, width=30, height=30, max_ticks=1200):
    if games<2 or games%2: raise ValueError('Games per pairing must be a positive even number, at least 2, to balance spawns')
    if width<7 or height<5: raise ValueError('Arena must be at least 7 wide and 5 high')
    if len(teams)<2 or len({t['id'] for t in teams})!=len(teams): raise ValueError('Provide at least two racers with unique IDs')
    if len({t['team'] for t in teams})!=len(teams): raise ValueError('Use one racer per distinct team in this tournament')
    for t in teams:
        if t['algorithm'] not in {'aggressive','defensive','territory','lookahead'}: raise ValueError('Unknown algorithm')
        if not 1<=t.get('depth',6)<=20: raise ValueError('Depth must be 1..20')
    output=Path(output)
    # Avoid overwriting earlier tournament records.
    output.mkdir(parents=True,exist_ok=False)
    replay_dir=output/'replays';replay_dir.mkdir()
    rows={t['id']:{'id':t['id'],'team':t['team'],'algorithm':t['algorithm'],'played':0,'wins':0,'draws':0,'losses':0,'points':0} for t in teams}
    matches=[];total=len(teams)*(len(teams)-1)//2*games
    left=(max(1,width//6),height//2);right=(width-1-left[0],height//2)
    for a,b in itertools.combinations(teams,2):
        for game in range(games):
            swapped=bool(game%2)
            riders=[]
            for team,spawn,heading in [(a,right if swapped else left,3 if swapped else 1),(b,left if swapped else right,1 if swapped else 3)]:
                riders.append({**team,'position':list(spawn),'heading':heading})
            # Use the same seed for each two-game spawn-swapped block.
            match_seed=seed+game//2
            config={'width':width,'height':height,'riders':riders}
            replay=run(config,match_seed,max_ticks)
            number=len(matches)+1;filename=f'match_{number:04d}.json'
            (replay_dir/filename).write_text(json.dumps(replay),encoding='utf-8')
            winner=replay['result']['winner']
            for team in (a,b):
                row=rows[team['id']];row['played']+=1
                if winner is None: row['draws']+=1;row['points']+=1
                elif winner==team['id']: row['wins']+=1;row['points']+=3
                else: row['losses']+=1
            matches.append({'match':number,'racers':[a['id'],b['id']],'seed':match_seed,'swapped':swapped,'replay':f'replays/{filename}',**replay['result']})
            print(f"[{number}/{total}] {a['team']} vs {b['team']} | {winner or 'Draw'} | {replay['result']['ticks']} ticks",flush=True)
    standings=sorted(rows.values(),key=lambda r:(-r['points'],-r['wins'],r['team']))
    # Equal points and wins share a rank; alphabetical order is display-only.
    previous=None;rank=0
    for place,row in enumerate(standings,1):
        key=(row['points'],row['wins'])
        if key!=previous: rank=place
        row['rank']=rank;previous=key
    report={'schema_version':1,'settings':{'games_per_pair':games,'base_seed':seed,'width':width,'height':height,'max_ticks':max_ticks,'win_points':3,'draw_points':1},'teams':teams,'standings':standings,'matches':matches}
    (output/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (output/'standings.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['rank','team','id','algorithm','played','wins','draws','losses','points']);writer.writeheader();writer.writerows(standings)
    print('\nStandings (win=3 points, draw=1):')
    for row in standings: print(f"{row['rank']}. {row['team']}: {row['points']} pts | {row['wins']}W {row['draws']}D {row['losses']}L")
    print(f'\nSaved to {output.resolve()}')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--games-per-pair',type=int,default=2,help='Even number; default 2 = each starting side once')
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--output',default='round_robin_results',help='New directory; existing directories are never overwritten')
    p.add_argument('--roster',help='Optional JSON file containing a list of racer objects or {"riders": [...]}')
    p.add_argument('--width',type=int,default=30);p.add_argument('--height',type=int,default=30)
    p.add_argument('--max-ticks',type=int,default=1200)
    args=p.parse_args();teams=DEFAULT_TEAMS
    if args.roster:
        data=json.loads(Path(args.roster).read_text(encoding='utf-8'));teams=data['riders'] if isinstance(data,dict) else data
    try: tournament(teams,args.output,args.games_per_pair,args.seed,args.width,args.height,args.max_ticks)
    except (ValueError,FileExistsError) as exc: p.error(str(exc))
if __name__=='__main__': main()
