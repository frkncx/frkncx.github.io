# In Building Erebus

Erebus was supposed to be one of the weekly jams in my Game Design program. It took me 2 days, and around 12+ hours to build it, relatively short for a visually appealing game. On day one, my first task was to model the Virus and White Cell, which gave me the biggest inspiration for making this happen.

[Placeholder: how you modelled them in Maya. What the shapes are based on, roughly how long it took, and whether the bacteria were made the same way or came later.]

[Placeholder: how you got from "I modelled a virus" to "this is a strategy game inside a blood vessel." Was there a jam theme you were working to?]

## The map is a straight line, so there's no pathfinding

Every organism in the game inherits from one base class that holds health, speed, damage, and how much DNA it drops when it dies. Each type then writes its own movement.

There's no NavMesh or pathfinding anywhere in this, because the map is just a straight vein with a blue end and a red end. A unit normalizes the direction to the far end and moves that way. That's it. My units walk toward the red end, enemy units walk toward the blue end, and anything red that reaches my end destroys itself and takes a point off my score while giving one to the enemy.

[Placeholder: how you built the vein itself. Modelled in Maya or Unity primitives? Anything keeping units from drifting through the walls?]

## Finding enemies

For finding enemies I used InvokeRepeating on a 0.5 second interval instead of checking every frame, so 50 units on screen doesn't mean 50 checks per frame. Each check is a 15m OverlapSphere that grabs the first collider it finds with the enemy tag. Not the closest one, just the first, which is the thing I'd change now.

Once a unit has a target it walks at that instead of the end of the vein. Fighting happens on collision, and OnCollisionStay deals damage every 0.15 seconds for as long as the two are touching.

## Everything happens in OnDestroy

Everything that happens when something dies is inside OnDestroy. Unity calls that for me automatically, so I never needed a separate manager sitting there watching for deaths. Score goes down, DNA gets paid out, the kill sound plays.

This is also where conversion happens. When one of my blue bacteria dies, there's a 25% chance a red bacteria spawns right where it fell. The Purify upgrade gives me the same thing in reverse at 50%. Bacteria also clone themselves on a 30 second timer at 25%, which the enemy gets for free and I have to buy with DNA.

## GameManager and the difficulty

GameManager runs the rest: the two cameras, keyboard input, the enemy spawn countdown, DNA income, and the win check.

My units spawn on keypress if I have the DNA for them. White cells are a flat 15, and blue bacteria cost whatever my live bacteria count is, so the more I have alive the more the next one costs.

The enemy timer starts at 10 seconds and tightens to 1 second over about 7 minutes, rolling viruses more often the longer the game runs. Each virus gets one random scale number, and I used that single number for everything: its size, its health, the DNA it drops, and its tier name (Beta, Alpha, Delta, Omega). One roll, four results.

[Placeholder: where the tier names came from, and whether the spawn numbers came out of playtesting or you tuned them by feel.]

## Two cameras

There's a top-down camera for commanding and an interior camera for looking around inside the vein, and F1 swaps between them. Both are clamped so you can't fly out of the level. The top camera moves on z between -60 and 94 with its FOV held between 45 and 75, and the interior camera clamps its rotation to 0-90 on x and -90 to 90 on y.

[Placeholder: why you built the interior camera at all. Was it to show off the models up close, or does it change how you play?]

## The glow

The glow on the organisms is a Fresnel node in Shader Graph on an unlit URP shader. Unlit because they're microorganisms in a dark vein and I wanted the silhouettes readable when you zoom out.

[Placeholder: anything else visual worth mentioning. Post-processing, bloom, the vein material, the floating health bars.]

## What I'd change now

The four unit classes (BlueBacteria, WhiteCell, RedBacteria, Virus) are near-identical copies of each other. They differ by which tag they look for, which end of the vein they walk to, and what happens in their OnDestroy. That should be one class with a faction field, or the movement and combat should sit in the base class.

MovePosition is being called from Update instead of FixedUpdate, which means movement is tied to framerate and fights the physics step.

The OverlapSphere allocates a new array every half second for every single unit, and it has no layer mask, so it's testing walls and geometry too. OverlapSphereNonAlloc with a mask fixes both at once.

The enemy spawn logic is also a long if-ladder of hardcoded numbers. An AnimationCurve or a ScriptableObject table would let me tune the difficulty without recompiling.

[Placeholder: GIFs pulled from your gameplay footage. Two or three placed through the post, one near the top.]
