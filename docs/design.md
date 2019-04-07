# pyos - Python Open Solitaire

# Motivation
I enjoy the occasional Solitaire on my phone like many and I don't like ads, 
especially when they are intrusive and force you to watch the same things over 
and over, just to get to the actual game. It's almost a second game inside the 
game to find the *"spot marked __`X`__"*, when you finally can skip whatever 
you were forced to watch.

So I decided to take a shot at making yet another Klondike/Solitaire clone and 
if I succeed, to distribute it for Android w/o advertisement and completely 
free *(because selling a product would imply maintaining it, even if I get 
bored with it, which can happen, you know...)*.

# Roadmap

##### V 0.1 - V 0.3
See: 
* [V 0.1](https://github.com/tcdude/pyos/projects/1)
* [V 0.2](https://github.com/tcdude/pyos/projects/2)
* [V 0.3](https://github.com/tcdude/pyos/projects/3)

##### V 0.4
* Online Features
    * Server (Free GCE or similar)
        * Light weight message protocol
        * Avoid unnecessary traffic
        * Keep it simple
    * *Pseudo* Multiplayer one-vs-one (Recorded Gameplay)
        * Use the **share** feature of the OS
        * Register Protocol to open App directly
        * TBD
        
##### V 1.0 *(probably...)*
* Polish + Extensive Testing

# Game Logic

## Setup

1. Shuffle Cards (seed aware for pseudo *online play*)
1. Place Cards on the **Tableau** 7 columns with `column index` 
   cards face down and on top 1 card face up
1. Place remaining cards on Stock face down


## Game Loop

##### Repeat while not win or abort:
1. Check User Input and perform move
    1. Single tap/click on Card:
        1. try to move to Foundation
        1. try to move to Tableau
        1. shake animation
    1. Drag Start   -> Identify Card in pointer pos
    1. Drag During  -> Update Card pos relative to Drag Start pos
    1. Drag End     -> Verify allowed (y/n):
        1. Drop Card on destination
        1. fly back animation
    1. Single tap/click on Stock:
        1. Flip top most card to Waste
        1. If no card recycle Waste
1. *Optional:* Automatically move
1. Update Move Count and Points
1. Check win condition


##### Win Condition:
1. Calculate Points = `Points + 700'000 / max(seconds, 30)`
1. Show Win Screen `(Points, Duration, Moves)`


## Scoring

##### During Game Play
| Move  |  Points  |
| --- | --- |
| Waste to Tableau | 5 |
| Waste to Foundation | 10 |
| Tableau to Foundation | 10 |
| Turn over Tableau card | 5 |
| Foundation to Tableau | -15 |
| Undo (*any*) | -15 |
| Recycle waste<br> *(when playing draw one)* | -100 |

##### Bonus
`700'000 / max(seconds, 30)`


# Visual

## Screen

##### Legend
| Short  |  Name  |
| --- | --- |
| ST | Stack |
| WS | Waste |
| T*N* | Tableau index *N* |
| F*N* | Foundation *N* |


##### View: Stack Right

`+----------------------+`<br>
`| F1 F2 F3 F4 ||  WS ST |`<br>
`+----------------------+`<br>
`| T0 T1 T2 T3 T4 T5 T6 |`<br>
`+----------------------+`<br>

##### View: Stack Left

`+----------------------+`<br>
`| ST WS || F1 F2 F3 F4 |`<br>
`+----------------------+`<br>
`| T0 T1 T2 T3 T4 T5 T6 |`<br>
`+----------------------+`<br>

---

# Winner Deal

*An different way of dealing the deck to assure a winnable Game.*

Instead of simply shuffling the deck and dealing, the process starts with a
completed game *(all cards on foundation)* and works its way backwards to a
valid starting state. To achieve a good level of randomness, a distance 
function is introduced to measure the distance in moves to the desired state
*(i.e. 24 cards on the stack and 28 cards on the tableau with the top most
7 cards on the tableau face up and the rest face down)*. Since an average
game can be finished in approx. 130 moves, this will be used as an 
indicator to steer the random selection of moves. Only testing will show what
number of maximum moves leads to adequate randomness.

#### The algorithm should fulfill the following parameters:
* High information entropy *(Good shuffled -> Interesting to play)*
* No redundancy *(e.g. no repeat moves)*
* Find a solution in reasonable time

#### All the possible Moves

| From | To | Single Card | Remarks |
| :---: | :---: | :---: | :--- |
| Foundation | Tableau | Y | Either to a valid position or as new top card |
| Foundation | Waste | Y | Face Up only |
| Tableau | Waste | Y | ^ |
| Tableau | Tableau | N | Either to a valid position or as new top card<sup>1</sup> |
| Tableau | Tableau | Flip card when not top most anymore |
| Tableau | Foundation | Limit to reduce potential unnecessary moves |
| Waste | Stack | 1 or 3 cards only if a complete move is possible! |
| Stack | Waste | 1 or 3 cards allowed at any time |

<sup>1</sup> *when moving a card/stack to an invalid position leads to flipping
the card below* 

#### Distance Function

