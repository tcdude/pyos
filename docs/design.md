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

##### V 0.1
* Working Prototype on Android
* Playable Game Loop
* Handling of `HW Back Button` / `Transition to Background` / `Restore from 
Background`

##### V 0.2
* Options Menu
* Different Play Types (`Draw One`, `Draw Three`)
* Stats (`Personal Best [moves, time, score]`)

##### V 0.3
* Auto to Foundation
* Undo Move
* Screen Rotation and Layout for Landscape mode

##### V 0.4
* Online Features
    * Implement Google Play Games Services API
    * *Pseudo* Multiplayer one-vs-one (Recorded Gameplay)
        * Find free or cheap way to pass messages between players<br> 
        (maybe register custom Protocol?)
        * Matchmaking?
        * TBD
        
##### V 1.0 *(probably...)*
* Polish + Extensive Testing

# Game Logic

## Setup

1. Shuffle Cards (fixed seed for pseudo *online play*)
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