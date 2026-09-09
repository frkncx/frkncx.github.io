---
title: "Realms of Uldar - Post Mortem"
date: 2026-05-24
project: "Realms of Uldar: Void Crystal"
topic: Unity Devlogs
lede: >-
  Realms of Uldar: Void Crystal is a fast-paced top-down action RPG built for a
  game jam and a passionate idea, roughly in 5 days, and around 27 hours of
  development time.
image: /RealmsOfUldarThumbnail.png
original_url: https://furkancx.itch.io/realms-of-uldar-void-crystal/devlog/1533111/realms-of-uldar-post-mortem
play_url: https://furkancx.itch.io/realms-of-uldar-void-crystal
description: >-
  Post mortem on Realms of Uldar: Void Crystal. What went right with game
  feel, 2D URP lighting and progression, what went wrong with animation and
  balance, and what comes next.
---

## What is this game?

Realms of Uldar: Void Crystal is a fast-paced top-down action RPG built for a game jam and a passionate idea, roughly in 5 days, and around 27 hours of development time. You play as the Void Wraith character, wielding a scythe, and carrying 7 abilities to unlock and upgrade as you level up, tasked with destroying the Void Crystal before it reaches full charge, and regaining control over your forces. It features 15 levels, 4 active abilities, 3 passive abilities, fast game progression and enemy composition, and two difficulty modes to choose from.

Built with:

1. Unity (game engine)
2. Adobe Photoshop (all sprites and visual assets)
3. Capcut (audio editing and clip padding)
4. Pixabay and royalty-free sources (sound effects and ambiance)

## What went right?

This was the first project where I invested heavily in the game feel from the start and researched all the ways I could add juice to the game.

- **Camera Shake:** On structure destruction, Void Chasms and Void Crystals on shattering feels interactive and realistic thanks to the camera controller script with shake method implemented.
- **Enemy death scatter:** Enemies no longer destroy themselves on death. Instead, their parts are added individually as game objects, and their behaviour is controlled by adding rigidbody2d and applying force and torque at runtime. No animations, and better chaos.
- **Health bar lerping:** Fluid health bars are implemented by adding a second health slider that has a white fill color, and a lerp logic that delays and follows the original health bar, creating a smooth delta effect.
- **Ghost trail on using R ability:** The Phantom ability that triggers a speed boost with ghost echo trails and a time slow snapshot added via code again. Coroutine with time scale adjustments, and player mesh duplication with color alpha value reduced for each spawned behind the player.
- **Particles:** I already had created particles, and I know the workflow. Void mist particle on the crystal, Void Chasm electric sprite, player void bolt ability, they are all similar and different variations of the same thing from previous particles I have created before, and they worked seamlessly. With rotation, colour over time, and noise, the game felt much better and improved flow and affordance.

### Lighting

This was my first time implementing lighting in a 2D game in a Unity project. I have never thoroughly tried URP's 2D lighting renderer features; Shadow Caster 2D, point lights, spot lights, sprite lights dedicated for 2D. This was the perfect chance to learn something new while making the game even more polished. Getting through the setup took some learning, for example, replacing game object sprites with sprite-lit-default sprites that responded to light, and learning how to add and set up a 2D shadow caster that casts the player's shadow near bright objects. Also, a global dark-ish light with low intensity and purple colouring contributed to the game's overall theme.

### Sprites

Working with vector art in Photoshop, I created all the sprites for the character, the enemies, the grasses, and integrated the crystal which was already a concept I had. I imported all sprites as PSD to Unity, which was very efficient, no re-exporting, and always up-to-date changes. I set up 128 ppu (pixels per unit) in Unity and used 256x256 to 1024x1024 canvases for each sprite in Photoshop to ensure consistent scaling, and larger objects simply got larger canvases to work with, without tinkering with transform scales.

### Gameplay flow

The void chasm system across two difficulties, spawning on each specific interval, and each spawning 2 enemies (4 for advanced difficulty) as baseline, while protecting and amplifying the crystal, was the main drive I had to make the game fun and challenging. Each one adds 0.1% (25% more for Advanced difficulty) to the crystal charge per second, creating urgency and a call to action to act fast. Each destroyed chasm adds 50% more health to the next one (75% for Advanced) and 2 extra enemies, incrementing indefinitely, and the game gets harder as you succeed.

Player level system. This was the second drive I had. Its the most fun thing to progress and achieve mastery, and 15 levels is a fast and scalable milestone. Each minute on average allows 3 level-ups, and each level-up grants overall better stats: 200 HP to 1000 HP, 20Dmg to 50Dmg, and so on. First 3 active abilities get 3 upgrades, and the rest get 1, except the first passive ability, giving strategic choice and a unique build to go towards. Because this is a fast-paced game, the exp progression is linear; each level takes 100 exp, nothing more. It worked seamlessly in my opinion, the magic of RPG games was implemented here in 5 days. It works.

### Audio

Splitting audio into three separate AudioSources (UI, Sfx, Combat) and three different mixer groups solved the sound interruption and made things cleaner with sound design. I added a compressor effect also on the Master mixer group, and did my best to balance each sound I downloaded from Pixabay and royalty-free videos. I have a static audiomanager that singlehandedly triggers all sound events across scripts, nothing complicated to play a sound on player level up, for example, or crystal destruction. Sound themes are void, alienish, and chaotic with lightning. So ambiance and attack sfx reflect this with energy beams, thunder, and more.

## What went wrong?

Animations. They were the biggest constraint because I built every sprite from scratch, and I am not super good at creating sprite sheets for every movement and then assembling them in Unity. Instead, for a game jam timeline, I decided to add a weapon that strikes and swings using rotation changes in Unity's animation window, without relying on complex body animation itself, and code-driven effects and particle systems that compensated for what traditional animation would have provided.

Some audio discrepancies, such as clips under 0.2s, didn't trigger in the WebGL version in the browser, so I extended the clips with no additional sounds, and the browser no longer dropped them. One thing that didn't fully resolve with sounds is the balance and consistency, some sounds overlap and are much louder than others. This is something I have to be more careful about in the future.

A well-balanced game difficulty was an issue that wasn't fully resolved. Tuning difficulty and game balance with no reference player is genuinely hard. So at the last hour, I decided to add a difficulty system. Normal is too easy for me, and Advanced difficulty is on the threshold. Better to have 2 difficulties to choose from than to guess to nail the game flow. All players can simply choose a difficulty without being forced into a single experience, which was one way to stop second guessing if it's balanced or not.

Players have access to a tutorial menu, but new players who are not aware of action RPG dynamics (or any other relevant game dynamics) can have a hard time figuring out the controls. This was not tested, and it remains an open question, so feedback will be appreciated.

## What I learned and What's Next

Realms of Uldar was a significant step forward in how I approach game feel and visual polish within constraints. I learned a lot about lighting in 2D, and implemented it from scratch as I learned. I created my own sprites with pretty much the same components, and used variations of different combinations for efficiency and consistency across all sprites, and developed cool animations using different techniques, like using rigidbody features to scatter dead body parts for enemies.

I also implemented systems I hadn't built before to make the game feel alive. I learned about implementing dynamic health bars with smooth transitions, a broadcast notifications system, escalating difficulty progression with chasm spawns, and audio manager with different sound sources through a mixer, and full ability features with cooldowns sliders, timers, shortcuts, and unique effects with ghost trails that takes gameplay to the next level.

For particles, reusable workflow taught me how to approach future projects more efficiently with what I already know instead of reinventing the wheel every single time. Each particle can be tweaked and show a completely different result, while retaining the necessary features and consistency, instead of creating a new feature from scratch.

Character animation was the weak point of this project. Working with separated sprite parts and making rotations feel realistic rather than robotic takes more than simple character design. I think they require planning beforehand, during the game's planning stage, to decide whether getting sprite assets online is worth it rather than deciding it later in mid-development and then worrying about workarounds after the core visual concept is already created.

Realms of Uldar has more stories to tell. My vision was simple: a core game loop around character progression, racing against escalating game difficulty. A loop that rewards mastery while constantly raising the stakes to keep the flow. Void Crystal established the core loop, the visual identity, and introduced the world. The next games will feature challenging missions with new characters, diverse ability systems and game objectives built on top of the same concept. The foundation is here. What comes next is everything it's building toward.
