---
title: "In Building Erebus"
date: 2026-08-02
project: Erebus
topic: Unity Devlogs
lede: >-
  Erebus was supposed to be one of the weekly jams in my Game Design program.
  It took me 2 days, and around 12+ hours to build it, relatively short for a
  visually appealing game.
image: /ErebusThumbnail.png
original_url: https://furkancx.itch.io/erebus/devlog/1611907/in-building-erebus
play_url: https://furkancx.itch.io/erebus
description: >-
  A technical breakdown of Erebus, a 3D microscopic strategy game built in
  Unity URP over two days: models, gameplay loop, GameManager, abilities, and
  camera systems.
---

Erebus was supposed to be one of the weekly jams in my Game Design program. It took me 2 days, and around 12+ hours to build it, relatively short for a visually appealing game. On the first day of the week, I imagined a two-sided fight of microorganisms involving viruses and white cells, which gave me the biggest inspiration for making this happen. This would be a Tug of War-style microscopic battle simulation. The currency is DNA, and there is the Blue side, where we get the beneficial microorganisms (White Cell and good bacteria), and the red side, where enemy AI simply gets the pathogens (Viruses and bad bacteria). Both sides start at 100 points, and whoever kills an organism reduces the enemy's score each time. The side with the remaining score wins.

Tools I used for making Erebus: Unity, Adobe Photoshop for button/ability sprites, Maya for the models, and ChipTone (free sound effect generator tool) for simple sound effects.

## Models and Environment

I used Maya to model the Virus and the White Cell, as well as the Bacteria tail, which I made using simple topology. They are relatively simple models to shape (a default sphere), so this was no issue for me. My only constraint was time, so for the model spikes, I created a cylinder and smoothly warped it to give a realistic shape, then copied and pasted it across the Sphere's surface. Bacteria itself is a simple capsule, and its eyes are just spheres made inside Unity.

My initial goal was to make this a simple spatial combat arena on a square mesh. But this idea was subsequently scrapped since the theme was biology and microscopy. Therefore, I decided to go with a vein tunnel, and made one using Unity's Probuilder. I created a simple cylinder, emptied it, and made a tube out of it using ProBuilder tools. However, as I will explain in the Camera Features section, there are two cameras which players can toggle, and from the outside view, the interior of the tunnel is not visible at all, nor the Bacteria or the cells. So instead of one tunnel, I created two and intertwined them. One has the outside view faces completely inverted, so they are comfortably visible from the outside angle, but completely enclosed in the interior camera view, which works naturally.

For the scene and lighting, I used a procedural SkyBox and set it to a dark red to match the human blood vein. The glow on the organisms is a Fresnel node in Shader Graph on an unlit URP shader, and I used YouTube tutorials to set it up manually. The material is unlit because they're microorganisms in a dark vein, and I wanted the outline silhouettes to be clearly visible and aesthetically pleasing. I then used URP's Post Processing effects, increased the Bloom effect, and made everything glowing and visually intense. The blue side (player side) gets the Blue glowing outlines, and the red side (Enemy AI) gets the crimson red outline, clearly signalling danger and nailing the theme, especially on Virus.

Last but not least, I'd like to break down how I set up the Particle System for red blood cells. As with all the ability icons in the game, I designed the sprites for the red blood cells too, and used a particle system: set the shape to Box, added noise, speed over lifetime, and gave it a natural behaviour for ambiance.

## Gameplay

**Win Condition:** Starting with the gameplay loop, each side has a slider bar at the top of the screen. The player owns BlueScore, the enemy owns RedScore, and both are integers on GameManager starting at 100. `GameResult()` runs every frame inside Update and compares the two. If BlueScore reaches 0 while RedScore is above 0, the GameLost scene loads. If RedScore reaches 0 while BlueScore is above 0, the GameWon scene loads. Both cases also make the cursor visible again and play their own sound.

**Currency:** DNA (the game's currency) starts at 0. A coroutine adds to it every 3 seconds, starting at 1 and increasing to 5 as the game timer passes 60, 120, 180, and 240 seconds. Killing Red Bacteria and Viruses also adds their protocolDNA (unit's DNA currency upon death) value. DNA is used for spawning Bacteria and White Cell, and purchasing 4 Abilities (see abilities section below).

**Organism Unit Inheritance:** Every organism in the game inherits from one base class called `MicroOrganizms.cs` that holds health, speed, damage, and how much DNA it drops when it dies. Because the variables are public, each type and its values for each unit can be modified using the inspector.

**Enemy Spawn Composition:** A float in Update counts down each frame, and when it reaches zero, it calls `EnemySpawnComposition()` and resets itself to the current spawn timer interval. That method runs GameTimer through a chain of if statements placed at 30-second marks, and each one sets two values: the spawn timer interval and the odds between a Red Bacteria and a Virus. It begins at one spawn every 10 seconds, all Red Bacteria. The odds shift at each mark and settle at 60/40 (Bacteria/Virus) by 300 seconds. The spawn timer interval keeps shortening past that point and hits its floor of 1 second at 420 seconds.

**How Organism Units Move:** The base class holds two hardcoded Vector3 destinations, blueSide at (0, 20, -150) and redSide at (0, 20, 120), and every unit carries both of them. Movement comes down to a single bool called isChasing. If it's true, the unit steers toward whatever it found. If it's false, it steers toward the enemy's end of the vein. Either way, it normalizes that vector and calls `rb.MovePosition` with protocolSpeed and Time.deltaTime, so the Rigidbody moves the unit instead of the transform. Red units run one extra check inside that same else branch, using `Vector3.Distance` against blueSide. Similar to a Tug of War game, when any red unit reaches the blue side, it destroys itself, decrements BlueScore, and increments RedScore.

**How Organism Units Find Enemies:** Each unit calls InvokeRepeating in Start, which runs `DetectEnemies()` every 0.5 seconds instead of checking every frame. Each check is a 15m OverlapSphere that returns the first collider with the enemy tag. Once a unit has a target, it walks towards that instead of the end of the vein. Fighting happens on collision, and OnCollisionStay deals damage every 0.15 seconds for as long as the two units are colliding with each other.

**Units' OnDestroy Logic:** Everything that happens when units die occurs in `OnDestroy()`, which Unity calls automatically when a game object is destroyed. The score decrements on the dying unit's side, DNA is added, and the kill sound plays. `OnDestroy()` is also where conversion happens. When a Blue Bacteria dies, Random.Range gives a 25% chance that a Red Bacteria is Instantiated in its place (Purify ability for the enemy) and RedScore increases by 1. Red Bacteria also runs a 30-second coroutine that instantiates a copy of themselves at 25% (Clone ability for the enemy). Both of these run from the start of the game. The Abilities section will cover more about how abilities were set up below.

## GameManager and the difficulty

GameManager is a singleton and the flagship script that manages most features, game jam style code that gives authority to a single manager: the two cameras, keyboard input, the enemy spawn countdown, DNA income, and the win check.

Key 1 spawns a Blue Bacteria and key 2 spawns a White Cell, both blocked if the DNA total is too low. White Cells cost a flat 15 DNA. Blue Bacteria cost whatever the live Blue Bacteria count is, so the first is free and every one after costs 1 more than the last. 1, 2, 3-- 20, etc.

Each Virus is instantiated with one value from Random.Range, and that single value sets its size, its health, the DNA it drops, and its tier name. The tiers are Beta, Alpha, Delta and Omega, named after mutation variants and Greek letters, and they drop 7 up to 15 DNA. The range that the value is picked from widens as the game runs, so later Viruses are larger and tougher.

## Abilities

There are four upgrades in Erebus, each with shortcut keys 3 through 6. Each one costs DNA, sets a bool on GameManager to true, and plays an upgrade sound.

**Clone Efficiency:** 20 DNA. Every Blue Bacteria starts a coroutine in Start that loops forever. While CloneEfficiency is false, it yields null every frame. Once it is true, the coroutine waits 30 seconds, calls `Random.Range(0f, 4f)`, and if the result is above 3 it Instantiates a Blue Bacteria at the same position and rotation and adds 1 to BlueScore. That threshold is a 25% chance. Red Bacteria run the same coroutine from the start with no purchase, which gives the enemy a head start.

**DNA Bonus:** 25 DNA. In the OnDestroy of Blue Bacteria and White Cells, if BonusDNA is true, that unit's protocolDNA value is added to blue side's DNA total.

**Purify:** 30 DNA. In Red Bacteria's `OnDestroy()`, if PurifyBacteria is true and `Random.Range(0f, 4f)` returns above 2, a Blue Bacteria is Instantiated at the dead unit's position, adding 1 to BlueScore. Blue Bacteria contains the same logic with no upgrade check, so 25% of dying Blue Bacteria Instantiate a Red Bacteria and add 1 to RedScore from the start of the game, which is another headstart for the enemy.

**White Cell Mutation:** 40 DNA. When a White Cell is Instantiated and WhiteCellMutation is true, GameManager calls `Random.Range(0, 200f)` and uses that number three ways: localScale is multiplied by 1 plus the number over 100, protocolHealth is increased by protocolHealth times the number over 100, and the FloatingHealthBar's maxValue and offset are both multiplied by 1 plus the number over 100. This is the same scaling applied to Viruses.

## Camera Features

There are two cameras and F1 swaps between them by flipping the enabled flag on each one, plus a TopCameraActive bool so Update knows which controller to run. The top camera is for overseeing the vein, and the interior one is for moving through the vein and actually seeing the models up close for immersion.

Pressing left or right moves the top camera along the vein, which runs down the world Z axis, so horizontal input multiplies into Vector3.forward rather than Vector3.right. That result is added to the camera's current position to get a target, the target's z is clamped between -60 and 94, and the camera Lerps toward it so it eases instead of snapping. Vertical input zooms by changing the camera's field of view, clamped between 45 and 75.

The interior camera maps the inputs differently. Vertical input moves it down the vein on Vector3.forward and horizontal input strafes it on Vector3.right, offering a nice first-person camera view. Z is clamped between -112 and 120, x between -21 and 24, and both Lerp the same way as the top camera. Mouse X and Mouse Y rotate the camera, with pitch clamped 0 to 90 and yaw clamped -90 to 90.

## World UI

Each organism also has a floating health bar which follows the current camera the player uses.

## What I'd change now

The biggest logic I would change is that OnDestroy throws a null reference when the game ends. `GameResult()` loads the win or lose scene, Unity tears down the old one in no particular order, and if GameManager dies first then every organism's OnDestroy hits a reference that no longer exists. The reason for my approach was simple: OnDestroy is easy to use and makes sense, but it causes problems on scene teardown and on quit, when I don't want scoring or spawning to run. The right fix isn't a null check, it's moving the game logic out into an explicit `Die()` method and leaving OnDestroy for cleanup only, so teardown can't trigger gameplay at all.

The four unit classes (BlueBacteria, WhiteCell, RedBacteria, Virus) are near-identical copies of each other. They differ by which tag they look for, which end of the vein they walk to, and what happens in their OnDestroy.

MovePosition is being called from Update instead of FixedUpdate, which means movement is tied to framerate and desyncs from the physics. I'm paying more attention to this now and realize that physics is applicable (and preferable) to be used in the FixedUpdate method.

The OverlapSphere allocates a new array every half second for every single unit, and it has no layer mask. OverlapSphereNonAlloc is already suggested by IntelliSense in VS, so this is something I would prioritize to optimize the game.

The enemy spawn logic is also a long if else statement ladder of hardcoded numbers, all inside the GameManager script. An AnimationCurve or a ScriptableObject table would let me tune the difficulty without recompiling.

I would consider these acceptable flaws for a working game jam made only in a couple of nights. I would like to say the game holds surprisingly well and without issues, and it remains one of my most successful ideas.
