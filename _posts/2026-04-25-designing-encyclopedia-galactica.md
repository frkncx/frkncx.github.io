---
title: "In Designing Encyclopedia Galactica"
date: 2026-04-25
project: Encyclopedia Galactica
topic: Unity Engineering
lede: >-
  This has been one of my proudest projects made in Unity. Relatively
  straightforward, but hopefully something that will shine in my catalogue for
  as long as it can.
image: /EncyclopediaGalacticaThumbnail.png
original_url: https://furkancx.itch.io/encyclopedia-galactica/devlog/1498993/in-designing-encyclopedia-galactica
play_url: https://furkancx.itch.io/encyclopedia-galactica
description: >-
  How Encyclopedia Galactica was built in Unity — Milky Way mesh and colliders,
  scientifically weighted star classification, scriptable-object civilization
  catalogues, and the Drake Equation panel.
---

This has been one of my proudest projects made in Unity. Relatively straightforward, but hopefully something that will shine in my catalogue for as long as it can

As I learned about scriptable objects, prefab variants, and materials/shaders, I had no problem implementing my ideas to begin with. My development plans were clear, and the idea was already made by Carl Sagan a long time ago, in his Cosmos series and the book. And the calculation mechanic is solely a scientific calculation created by Frank Drake to estimate extraterrestrial civilizations with detectable technology existing right now.

This simulation development took about 10 hours. First, I got a free Milky Way model on one of the 3d model websites. I couldn't use it because it wasn't FBX; it was a GLB file as far as I remember, so I converted it on a free converter website. And voila, I got the whole visual platform. I added about 5 box colliders, because there is no such thing as a disk collider! I got an optimized cubic style circle, which worked just fine. Box Colliders had triggers, and they were needed to get Star Prefabs to spawn accordingly, about 1000 to spawn at once.

Note that star logic is scientific too. They have the following variations: O, B, A, F, G, K, and M, based on the Morgan-Keenan (MK) classification used today. From blue to red, they spawn based on scientific percentages. That's why you will probably never stumble upon a dark blue star :) And instead, you will see a lot of red stars, which are very common in the universe.

Now, for the catalogues, as they are prefabs too, have textmeshpros for every section: Civilization Type, Biology, Technology, Culture, etc., etc., and we get the data from the scriptable object called CivilizationData, which have text arrays for each section, and I manually researched their styles and conventions and scientific plausibility. I used the best pattern recognition tool of our time, AI, to scrutinize each catalogue entry's plausibility to the best of my ability, and filled each array. (Check Carl Sagan's Cosmos series for his examples on civilization catalogues to better understand why I used his science jargon style.)

I created 6 Civilization levels: Pre-filter, Interplanetary, Interstellar, Post-Biologogical, Galactic, and Universal/Omega. Each level corresponds to 3-4 arrays in respective orders. That's why so far I have about 20+ array lists for every data section (i.e., 20+ Biology entries, first 3 are for prefilter, 4-7 for interplanetary, so on and so forth).

Each Catalogue panel instantiates on a generated star's transform position at offset (0, 2, 0), and disables itself as soon as your Drake Calculation gets a positive N.

N = Number of Civilization Catalog Prefab Panels Instantiated on Stars Randomly. Also, you will have affordance on stars with catalogues, by another placeholder white sphere game object for you to click on them. I used raycast and input.mousePosition to trigger the interaction, thanks to the placeholder's collider trigger with tag and re-enabling Civilization Panels on the star with a simple click.

Speaking of mouse and triggers, the Calculation Panel on top was basically EvenTrigger and OnPointerEnter to display a tutorial for each of the InputFields. So simple and elegant. You hover, and the tutorial text (I used scriptable object to populate them too) displays and gets data from the scriptable object accordingly.

The movement and zoom-in controls were boilerplate code I copied and pasted from my Erebus + Realm of Octahedron games. You will know what I'm talking about if you try those games.
