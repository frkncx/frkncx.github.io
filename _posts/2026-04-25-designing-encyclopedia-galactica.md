---
title: "In Designing Encyclopedia Galactica"
date: 2026-04-25
project: Encyclopedia Galactica
topic: Unity Devlogs
lede: >-
  Encyclopedia Galactica has been one of my proudest projects made in Unity,
  based on scientific topics blended with hard sci-fi.
image: /EncyclopediaGalacticaThumbnail.png
original_url: https://furkancx.itch.io/encyclopedia-galactica/devlog/1498993/in-designing-encyclopedia-galactica
play_url: https://furkancx.itch.io/encyclopedia-galactica
description: >-
  How Encyclopedia Galactica was built in Unity: Milky Way mesh and colliders,
  scientifically weighted star classification, scriptable-object civilization
  catalogues, and the Drake Equation panel.
---

Encyclopedia Galactica has been one of my proudest projects made in Unity, based on scientific topics blended with hard sci-fi.

As I learned about **Scriptable Objects**, prefab variants, and materials/shaders during this time, I had no problem implementing my project idea to begin with. My development plans were clear, and the idea was already made by Carl Sagan in his Cosmos series and his book.

It is based on the Drake Equation: a scientific calculation created by Frank Drake to estimate extraterrestrial civilizations with detectable technology living in the Milky Way galaxy.

## MILKY WAY

This simulation development took about 10 hours. First, I got a free **Milky Way** model on one of the 3d model websites. I couldn't use it because it wasn't **FBX**; it was a **GLB** file, so I converted it on a free converter website. As a result, I got the whole visual platform.

I added about 5 box colliders because there is no such thing as a disk collider. I got an optimized cubic-style circle, which worked just fine. The box colliders had triggers, and they were needed to spawn star prefabs accordingly, about 1000 at once.

## STARS

Note that star logic is scientific too. They have the following variations: O, B, A, F, G, K, and M, based on the **Morgan-Keenan (MK)** classification used today. From blue to red, they spawn based on scientific percentages. That's why you will probably never stumble upon a dark blue star. Instead, you will see a lot of red stars, which are very common in the universe.

## CIVILIZATION CATALOGUES

Now, for the catalogues, as they are prefabs too, have **TextMeshPro** for every section: Civilization Type, Biology, Technology, Culture, etc., and we get the data from the Scriptable Object called **CivilizationData**, which have text arrays for each section, and I manually researched their styles and conventions and scientific plausibility. I used AI to scrutinize each catalogue entry's plausibility to the best of my ability, and filled each array.

(Check Carl Sagan's Cosmos series for his examples on civilization catalogues to better understand why I used his science jargon style.)

I created 6 Civilization levels: **Pre-filter**, **Interplanetary**, **Interstellar**, **Post-Biological**, **Galactic**, and **Universal/Omega**. Each level corresponds to 3-4 arrays in respective orders. That's why so far I have about 20+ array lists for every data section (i.e., 20+ Biology entries; the first 3 are for prefilter, 4-7 for interplanetary, and so forth).

## THE CATALOGUE PANELS

Each Catalogue panel instantiates at a generated star's transform position at offset (0, 2, 0), and disables itself as soon as your Drake Calculation gets a positive N.

N = Number of **Civilization Catalogue Prefab** Panels Instantiated on Stars Randomly.

Also, you will have affordance on stars with catalogues, by another placeholder white sphere game object for you to click on them. I used raycast and input.mousePosition to trigger the interaction, thanks to the placeholder's collider trigger with a tag and re-enabling Civilization Panels on the star with a simple click.

Speaking of mouse and triggers, the **Calculation Panel** on top was basically an **EventTrigger** and **OnPointerEnter** to display a tutorial for each of the InputFields. So simple and elegant. You hover, and the tutorial text (I used a Scriptable Object to populate them too) displays and gets data from the Scriptable Object accordingly.

## CONTROLS

The movement and zoom-in controls were boilerplate code I wrote from my Erebus + Realm of Octahedron games, which is an efficient way to integrate mechanics, especially for fast iterative projects, instead of reinventing the wheel every time.
