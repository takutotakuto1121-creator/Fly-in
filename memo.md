#  マルチエージェント　経路探索
## 文献
1. [マルチエージェント経路計画の紹介](https://kei18.github.io/note/posts/mapf-tutorial/)
2. [SSII2023 [OS3] マルチエージェント経路計画の基礎と最新動向](https://speakerdeck.com/ssii/ssii2023-os3-02?slide=26)
3. [離散数学入門#8: 最大流問題(1)：フローネットワークの基礎知識](https://www.youtube.com/watch?v=QTNCb-d4_80&list=PLCo60G1m_ibpJgfB4WcGwWybC6sfyawoL&index=9)

## 最大流問題
`start_hub`から`end_hub`に向かって水を流す。一定時間で流せる水の最大量を求める問題。  
これを応用すれば解けそう。  
Droneは座標と時間軸の三次元.  時間は離散的なt.  
t=0~で全てのドローンが到達できるまで繰り返す.  
→到達したtが最小のt.  

tをfixした時の挙動
0~t,t回ドローンは移動できる。

t回の手数で可能な道全てに水を流し込む。end_hubにドローンの数以上水が来たらそのtがミニマムのtで経路はあと削ってうまいこと？

水を限界まで死ぬほど流す水同士がぶつかれば戻る。表現方法は
1. マルチスレッドで動かしてもしぶつかれば戻るようにする
2. 逆ルートに対応するキャンセルルートを保持し、そこを以降のBFSで探索可能にし、通れば相殺し本来の水の挙動に戻る

明らかに2の方が簡単やし速度も早いかな

--loop.  
t-1の情報をコピー.  
--loop.     
各ドローンに対してBFSでゴールまで行く.  
通った道がキャンセルルートを使ってれば相殺.  
ゴールから逆算したキャンセルルートを作成.  
--loop.    
t++.  
--loop.  

これで水の動き再現

時間拡張グラフの最大流

十分時間がある上でならわかるが
なぜtのminがわかるの？
BFSやし

視覚的には3次元のグラフみたいなもん

t=0からt=1編更新では

S(0) - S(1) のグラフがつながる

違う

DFSの繰り返しでDFSの行ける距離が拡張されていくイメージで今まで探索したとこの情報は持っておいてコピーするから最短手数がわかる。水は可能な限り流すからBFSで可能な限り探索で対応している

なんとなくいけてきた

あとはZoneの情報をうまいこと水で処理できるように調整する
1. zoneをzone_inとzone_outに分けて間はzoneのmax分だけ通れるようなconnectionにする

なんかこれでいけそう

mapf(multi agent find path)


個別のドローンには着目しない
水を流しまくって最後にidを一から順番に振っていく

## pygame


zone1_out -> dummy_in -> dummy_out -> zone2_out 


mapに依存しすぎ
→分割むずい

適当に修正orホームとマップを別ウィンドウにする


## A*の全探索
## CBS
priority-queueでメイクスパンがい使い順に常に並び替え続ければメイクスパンの最短が保証される
## LaCAM*
PIBT

DFS, BFS, tree
dijkstra, A*
TSP, maximun water flow, min cost flow
mapf
cbs, time-expanded frahph

基本: CBS
最先端SOTA: LaCAM/LaCAM*
Unlabeled: Time-Expanded Network Flow
実務・連続空間: Priority Planning/PIBT/ORCA

# MAPF(Multi Agent Path Finding)
## 前提
DFS, BFS, dijkstra, A*などのアルゴリズムの習得は前提条件とする。

## 概観
グラフ$G=(V, E)$, エージェントのグループ$A = \{1, 2, \dots , n\}$, エージェント$i$のスタート地点を$s_i\in V$, ゴール地点を$g_i\in V$, 経路$\pi_i = (\pi_i[0], \pi_i[1], \dots)$とする。

この時、アルゴリズムの評価指標は以下の２つ。
1. $\sum_{i\in A}cost(\pi_i)$
2. $\max_{i\in A}cost(\pi_i)$

MAPFは計算量が莫大なため、エージェントが増えるにつれて、最短の経路探索を行うとすると難しくなる。

よって、コストと探索時間を考慮した様々なアルゴリズムが研究されている。

今回は$\max_{i\in A}cost(\pi_i)$が最短になるアルゴリズムに絞って調査し、実装する。

## 全探索
全エージェントの位置を定め、これを$Q\in V^{|A|}$とする。

ある構成$Q = (v_1, \dots, v_i, \dots, v_n)$が与えられた時、$i \neq j$に対して$v'_i \neq v_j$ならエージェント$i$は衝突なしに$v'_i$に移動することができ、別の構成$Q' = (v_1, \dots, v'_i, \dots, v_n)$が生まれる。

このように、グラフ$G$の最大次数を$\Delta$とすると、１つの構成から$O((\Delta + 1)^{|A|})$個の遷移可能な構成が存在する。

遷移可能な構成(branching factor)をA*で全探索し、$\max_{i\in A}cost(\pi_i)$が最小となる経路を求める。

ただ、実用上はbranching factorが大きすぎてスケーラビリティに難がありすぎる。

## CBS(Conflict Based Search)
基本


## LaCAM*(Lazy Constraint Addition for Multi-Agent Pathfinding)
最新技術, PIBT使用


## Time-Expanded Network Flow
エージェントに区別がない状況で覚醒














