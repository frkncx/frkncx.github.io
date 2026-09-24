---
title: "Crown of Domination Tech Breakdown"
date: 2026-09-15
project: Crown of Domination
topic: Unity Devlogs
lede: >-
  Crown of Domination is my passionate design idea and my capstone project: a
  4v4 social multiplayer RPG game about social power fantasy, influence and
  control.
image: /CrownOfDominationThumbnail.png
original_url: https://furkancx.itch.io/crown-of-domination/devlog/1660981/crown-of-domination-tech-breakdown
description: >-
  A technical breakdown of Crown of Domination, a 4v4 social multiplayer RPG
  built in Unity 6 on Photon Fusion 2: host authority, prediction, custom
  collision, voting and bots.
---

**Crown of Domination** is my passionate design idea and my capstone project: a 4v4 social multiplayer RPG game about social power fantasy, influence and control, where, in this Kingdom vs. Kingdom scenario, players vote for each other, and the most voted player becomes the King.

This game was my first and biggest shot at making a complex multiplayer game, where the networking was harder than anything else, and I had so much to learn.

So far all of my projects have been single-player. But when you decide to go multiplayer, **every design decision becomes an authority-management problem.**

How does the host (lobby creator) create a lobby for the clients (his friends) to join? How to implement measures so players don't cheat? How does networking synchronize the important events, such as finding out who the King is and who is betraying whom?

As a solo dev, I worked on this game for about 4 months and did everything, including the **Photon Fusion** setup myself. As a result, some of the core concepts, such as the **Legitimacy Meter** and most of the role hierarchy, aren't in the game yet.

The shipped game is 4v4, capped at 8 players, with a PvE mode that fills the Red team with four bots. A faction wins by reaching 1500 resources before the other kingdom does, and resources come from holding the capture zones, which are the flags on the map, and I'll explain more about them below.

**Tools Used:**

1. Unity 6
2. Photon Fusion 2 - Using Host/Client Mode
3. Adobe Photoshop for designing player sprites and icons
4. Environment assets were sourced from a copyright-free sprite pack.

```
NetworkManager - session: runner, runner callbacks, input struct
 PlayerSpawner - one Player per client, plus 4 bots in PvE
 LobbyState - factions, names, readiness, survives into the game session
 PlayerPanel - votes, role assignment, King's orders
 BotController - drives the Red bots, host only
Player - movement, combat, role, faction, crown, domination
ScoreManager - resource ticks and win condition (scene object)
CaptureZone - per-zone capture progress (scene object)
```

**NetworkManager** and **LobbyState** persist across the scene load, since the session and the lobby data both have to outlive the menu. Everything else either spawns into the Gameplay scene or already sits in it, and dies when the scene unloads.

## How power actually works

A King is the apex rank, with a set of permissions the network enforces. The King is the only player who can change his faction's roles into Soldiers or Pawns, and **each role carries its own capabilities**: who can block, who can mine, who moves slower, and who deals less damage. So the King decides what his own teammates play as throughout the game, and can change them at any time.

**The King cannot be removed by his own subjects.** Friendly fire is a toggle the King controls, and even when it is on, subjects can damage each other but never the King.

The crown only drops when the enemy kills him. An ally who reaches it first becomes King with no vote, and an enemy who reaches it first can carry it home for 333 resources, a fifth of the win condition, and force your faction into an emergency revote. **The Legitimacy Meter** at the end of this post is my answer to that asymmetry.

Orders are the primary function of the King; however, I have not yet built a mechanic for punishments if a subject refuses the order. A King can tell a Soldier to defend and **nothing in code makes them**. The only leverage a King has over someone who refuses is demotion, and demoting your own Soldier to a Pawn is the current level of punishment, or strategy.

## Why Host mode and not Shared mode

Here is what the network has to settle.

**Election:** Every player in a faction votes for someone on their own team. The most voted player becomes King. A tie clears the votes and forces a revote instead of picking someone arbitrarily.

**Roles:** The King assigns Soldier or Pawn, with 1 to 3 Soldiers and 0 to 2 Pawns per faction. Soldiers are the only role that can block; Pawns deal 70% damage but are the only role that can mine gold; and one difference in their stats is that Kings move slower.

**Requests and orders:** A subject can ask their King for a specific role, and the King grants it or ignores it. The King can issue Attack, Defend, Patrol or Retreat, which pops up on that player's screen as a notification panel.

**Domination:** The King can seize direct control of an ally's body. The subject stops controlling their own character, the King's own body goes inert where it stands, and the King plays as that player until they release them or one of the two dies.

**Capture zones:** Five zones tick resources every second to whichever faction holds them, and the rate doubles with each additional zone a faction controls: 1 per second for a single zone, 2 for two, 4 for three, 8 for four, and 16 when one faction holds all five. Reaching 1500 resources before the enemy kingdom is the win condition.

![Blue Kingdom capturing a zone](/assets/devlogs/crown-of-domination/capture-zones.png)

**Every entry on that list is one player making a claim about another player.**

**In Shared mode**, "I picked up your crown" gets evaluated by the client who owns the crown, which means the game asks a player's machine to agree it was robbed.

**In Host mode**, the host runs the trigger, writes the new role into networked state, and despawns the crown. Every other client receives that result and has no vote in it.

A player can only become King by winning the vote or by picking up a dropped crown, and the code that assigns roles refuses to hand out the King role at all. If that check lived on the client, the player who wants to be King would be the one running it. **Every role change is sent to the host instead**, and the host returns early on the first of these that fails:

```csharp
if (callerPlayer.MyFaction != targetPlayer.MyFaction) return;
if (callerPlayer.MyRole != PlayerRoles.King) return;
if (role == PlayerRoles.King) return;
if (targetRef == callerRef) return;
```

The cost is that the host has an advantage in reaction time, since their inputs never travel, and the session dies when the host leaves.

**Host migration** would prevent that. Fusion raises a callback carrying a token, the game restarts the runner on one of the remaining clients, and the session resumes with player positions, roles and resource totals intact. Every networked value has to be reconstructable on a machine that never held state authority, which is a choice you make before writing the game logic. I did not build it because I lacked the knowledge at the time, and by the time I had it, it was too late.

## Input is a struct

Clients never tell the host what they did. **They tell the host what buttons are down**, and the host reads the values from NetworkInputData.

```csharp
public struct NetworkInputData : INetworkInput
{
    public Vector2 direction;
    public bool attack;
    public bool block;
    public bool sprint;
    public Vector2 aimWorld;
}
```

That is the entire network input for the game: movement, attack, block, sprint, and the world space aim point.

`aimWorld` is the point in the game world the mouse is pointing at. I convert the mouse position into world coordinates on the client before sending it, because every player's camera is somewhere different, so the same pixel on two screens is two different places in the level.

Mouse clicks are read in `Update`, which runs once per rendered frame, but input is only sent to the host on the network tick. **A click that starts and ends between two ticks would never reach the host at all.**

So a click sets a flag on the player, and the next time input is sent, that flag is read once and cleared:

```csharp
public bool ConsumeQueuedAttack(out Vector2 aimWorld)
{
 aimWorld = _queuedAim;
 if (!_queuedAttack) return false;
 _queuedAttack = false;
 return true;
}
```

That way a click is never lost and never sent twice to the host.

## Attacking without waiting for the host

An RPC-based attack costs you a round trip before your own character moves, which at 80ms ping is **160ms of nothing happening** after you click.

The attack instead runs inside `FixedUpdateNetwork,` which means Fusion predicts it locally and resimulates it when the authoritative state arrives. **Your own swing starts on the frame you click.**

```csharp
if (data.attack && !data.block && NextAttackTimer.ExpiredOrNotRunning(Runner))
{
    NextAttackTimer = TickTimer.CreateFromSeconds(Runner, AttackCooldownTime);     
// ... 
}
```

`NextAttackTimer` is a `[Networked] TickTimer`. The client predicts it so the local cooldown feels instant, but **the host holds the authoritative value**, so a client that patches out its own cooldown check just gets its extra swings thrown away on the next resimulation.

Damage is not applied on the swing frame. The swing sets a second timer:

```csharp
AttackDelayTimer = TickTimer.CreateFromSeconds(Runner, AttackDamageDelay);
QueuedAttackAim = aimWorld;
```

and damage resolves 0.1 seconds later, on the frame where the animation actually syncs. Because the delay is a `TickTimer` and the aim is `[Networked]`, the hit resolves once per swing instead of firing again on every rollback.

The damage block itself is wrapped in `if (HasStateAuthority)`, so **the client predicts the animation and the host decides the outcome**.

![Blue King sprite](/assets/devlogs/crown-of-domination/king-blue.png) ![Red King sprite](/assets/devlogs/crown-of-domination/king-red.png)

## Player

`Player.cs` is the biggest script in the project and it holds everything about a character at once. Its networked state covers health, faction, role, name, facing direction, gold, whether they are dead, blocking, mining, carrying the enemy crown, and whether a King is currently driving their body.

**Every one of those values has a render callback attached**, so when the host changes one, each client redraws the matching visual on its own: the sprite color, the weapon sprite, the crown, the health bar, the name label, the minimap dot.

Movement and collision are in the same script and **do not use Unity's 2D physics**. The player moves each tick directly, then steps back out of anything it overlaps by the depth of that overlap. No speed or momentum is stored anywhere, so replaying a tick five times ends in the same place every time, while velocity-based movement drifts apart between host and client because the physics solver does not rewind alongside the simulation.

The trade is no bounce, no friction and no physics materials, which is fine when collision only means not walking through walls or each other.

**`Player.cs` does three unrelated jobs:** the networked data, the visuals, and the movement and combat. It should be a Combat component holding the attack timers, the damage numbers and the block logic, a PlayerVisuals component holding every sprite, the health bar and the minimap dot and doing nothing except reacting when a value changes, and a smaller Player holding the networked state and nothing else.

All three sit on the same GameObject, so every networked property keeps the same owner and nothing about replication changes.

## The host counts the votes

Votes live in a networked dictionary:

```csharp
[Networked, Capacity(8)]
private NetworkDictionary<PlayerRef, PlayerRef> Votes => default;
```

When you press a vote button, **your client sends the vote to the host**, which records it only if your candidate is on your team, you have not voted already, and the 15-second discussion timer has run out.

Once the whole faction has voted, the host counts them. A tie for first clears that faction's votes and runs the vote again, otherwise the winner becomes King and everyone else becomes a Pawn.

## Enemy AI

PvE fills Red with bots, and **a bot is the same `Player` prefab spawned with no input authority**. `BotController` runs all of them on the host inside one `FixedUpdateNetwork`, writing the properties a human's input would drive: `MyRole`, `IsBlocking`, `IsMining`, position, health. Bots inherit role speeds, crown drops and death handling with no separate code path.

**Behavior branches on role.** Soldiers chase the nearest enemy within 15 units, or take the nearest capture zone the faction does not already hold. Pawns only fight if an enemy is close; otherwise they mine and fund the resource race. Kings run while they still have subjects and fight when no allies remain.

Bots don't walk straight at their target. My first version re-picked a way around obstacles every frame, which left two bots grinding against the same wall forever, so now a bot that moves less than 0.1 units in half a second **commits to one strafe side for 0.6 seconds**.

PvE always spawns four bots, so testing solo or with one friend means a full Red team beats you.

A 45-second delayed start and a flaw in the bot's attack reaction are currently the only advantages for real players: a player who hits and backs out of range is gone before the bot's delayed damage step re-checks distance, so **hit-and-run beats them reliably**. I left the hole in because it is the only thing making them beatable at low player counts.

## What I would do differently

**Bot allies**

The game is only 4v4 right now, which isn't small even for PvE mode, since a full game still needs 4 people on your side. The main issue is this game is fun only when you scale the player count, and I should have paid more attention to bot allies too. They would immediately solve the cold start problem while letting me test solo and scale the PvP to 8v8, 16v16 without needing that many real players in the room.

Instead, I made the lobby size adjustable, so even though the game mode is 4v4, I can set the player size to 2, for example, and test a PvP session as 1v1, or PvE as 1v4.

![Red Soldier sprite with shield](/assets/devlogs/crown-of-domination/soldier-red.png)

**Roles that did not ship**

Other scope creep I had to manage was the Servant role, a political branch that works as a minister to the King. The role is still in the code, but a 4-player kingdom didn't require this management hierarchy, so in practice it's King, Soldiers and Pawns.

There were also going to be subclasses where Soldiers equip different styles, Strength, Agility and Power to strategize and give autonomy to lesser ranks that gave diverse attributes and prestige for the combat system. Pawns, on the other hand, could have crafted fortifications, farmed, and used Militia mode to defend themselves, but none of these made it into the game.

![Subject profile panel showing rank and unfinished class slots](/assets/devlogs/crown-of-domination/profile-subject.png)

**Prioritize the Legitimacy system idea I had**

My most important design decision was planning a **Legitimacy Meter** System that would have changed the King's unstoppable rule and given subjects more autonomy and free will over the King. The King would lose legitimacy by abusing their authority, ignoring their subjects, or making unpopular decisions, while maintaining it through effective leadership and cooperation. Players could demote the King's legitimacy and then watch the King lose power over time, or approve his rule and give him an iron fist that would empower the King and reinforce their faction to become more coordinated over the map.

Below is a snapshot of how a Legitimacy meter would work: start at 50%, and fluctuate between 0-100 based on players' feedback.

![King profile panel showing Legitimacy at 50 out of 100](/assets/devlogs/crown-of-domination/legitimacy-meter.png)

**Code**

**NetworkManager.cs** is the script I would change the most. When a player creates a game, it generates a 3-digit join code, creates a GameObject called SessionRunner, attaches a NetworkRunner, and starts the session using the join code as the session name. When a player joins a game, it builds a runner the same way and connects to the session matching the code they typed in. It implements **INetworkRunnerCallbacks**, so the runner calls into it when a player joins or leaves and when a scene finishes loading, and asks it for input every tick, which it fills from the keyboard and mouse.

It also stores twelve references to main menu objects: the Create Game and Join Game buttons, the ready and cancel buttons, the join code field and its label, the name and lobby size fields, the PvP and PvE toggles, the settings blocker, and the lobby roster text it rewrites every frame.

The runner must survive MainMenu into Gameplay and back, so NetworkManager is `DontDestroyOnLoad`, but its menu references die with MainMenu, and a copy of NetworkManager sits in MainMenu as well. Every return loads a second copy: one holds live Inspector references and no session, the other holds the runner and null buttons, so **after a single disconnect you cannot create a game again**.

I first tried re-finding the buttons by their GameObject names on every menu load, which breaks the moment anyone renames one. In the current build the old copy passes the runner, the lobby and the join code to the new copy, then destroys itself.

**It should have been a session object created in code at runtime**, living in no scene so Unity has nothing to duplicate, plus a LobbyUI script in the menu scene holding the Inspector references and receiving the button UnityEvents, which is the only reason the manager was in the scene at all. But it turns out a scene can find one persistent object easily, while one persistent object cannot find twelve scene objects rebuilt on every load.

Respawn uses `WaitForSeconds(30f)`. That is wall clock time inside a tick based simulation. It should be a `TickTimer` like every other timer in the project.

In conclusion, **Crown of Domination** had about four months of development, and its strongest features are still not implemented. I have a lot left to learn about networking and coding, despite everything I got working so far.

With another four months, I would add bot allies to fix the cold start problem and the **legitimacy meter**, because it's the only way to balance the role asymmetry and reinforce socializing for both the King and other roles. Then I'd refactor the code, since that's what makes debugging and adding features efficient for what's coming next for this game.
