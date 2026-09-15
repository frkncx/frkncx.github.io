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

Crown of Domination is my passionate design idea and my capstone project: a 4v4 social multiplayer RPG game about social power fantasy, influence and control, where, in this Kingdom vs. Kingdom scenario, players vote for each other, and the most voted player becomes the King. This game was my first and biggest shot at making a complex multiplayer game, where the networking was harder than anything else, and I had so much to learn.

So far all of my projects have been single-player. But when you decide to go multiplayer, every design decision becomes an authority-management problem. How does the host (lobby creator) create a lobby for the clients (his friends) to join? How to implement measures so players don't cheat? How does networking synchronize the important events, such as finding out who the King is and who is betraying whom?

As a solo dev, I worked on this game for about 4 months and did everything, including the Photon Fusion setup myself. As a result, some of the core concepts, such as the Legitimacy Meter (will be explained below) and most of the role hierarchy, aren't in the game yet. The shipped game is 4v4, capped at 8 players, with a PvE mode that fills the Red team with four bots. The win condition is met when enough resources are gathered before the opponent kingdom, and a game session only starts when the lobby is full.

**Tools Used:**

1. Unity 6
2. Photon Fusion 2 - Using Host/Client Mode
3. Adobe Photoshop for designing player sprites and icons
4. Environment assets were sourced from a copyright-free sprite pack.

```
NetworkManager - session: runner, Fusion callbacks, input struct
 PlayerSpawner - one Player per client, plus 4 bots in PvE
 LobbyState - factions, names, readiness, survives into the match
 PlayerPanel - votes, role assignment, King's orders
 BotController - drives the Red bots, host only

Player - movement, combat, role, faction, crown, domination
ScoreManager - resource ticks and win condition (scene object)
CaptureZone - per-zone capture progress (scene object)
```

NetworkManager and LobbyState persist across the scene load, since the session and the lobby data both have to outlive the menu. Everything else is spawned in the Gameplay scene and dies with it.

## How power actually works

A King is the apex rank, with a set of permissions the network enforces. The King is the only player who can change anyone's role, and roles are capability: who can block, who can mine, who moves fast. So the King decides what their own teammates are allowed to do in a fight.

What stops that from being tyranny is that the position is removable by force. The crown is an object. Kill the King and the crown drops where they fell. An ally who reaches it first becomes King with no vote, or an enemy carries it home, scores 333pts, and forces your faction into an emergency revote in the middle of a match you are already losing.

Orders are the part with no enforcement at all. A King can tell a Soldier to defend and nothing in code makes them. The only leverage a King has over someone who refuses is demotion, and demoting your own Soldier during a fight costs you the fight.

## Why Host mode and not Shared mode

Here is what the network has to settle.

**Election:** Every player in a faction votes for someone on their own team. The most voted player becomes King. A tie clears the votes and forces a revote instead of picking someone arbitrarily.

**Roles:** The King assigns Soldier or Pawn, with 1 to 3 Soldiers and 0 to 2 Pawns per faction. Soldiers are the only role that can block; Pawns deal 70% damage but are the only role that can mine gold; and one difference in their stats is that Kings move slower.

**Requests and orders:** A subject can ask their King for a specific role, and the King grants it or ignores it. The King can issue Attack, Defend, Patrol or Retreat, which pops up on that player's screen as a notification panel.

**Domination:** The King can seize direct control of an ally's body. The subject stops controlling their own character, the King's own body goes inert where it stands, and the King plays as that player until they release them or one of the two dies.

**Capture zones:** Five zones tick resources to whoever holds them, and the resource race is what ends the match.

Every entry on that list is one player making a claim about another player. In Shared mode, "I picked up your crown" gets evaluated by the client who owns the crown, which means the game asks a player's machine to agree it was robbed. In Host mode, the host runs the trigger, writes the new role into networked state, and despawns the crown. Every other client receives that result and has no vote in it.

Host mode also gave me somewhere to put the anti-cheat. The rule that a Pawn cannot promote themselves to King is not a rule if it lives on the client of the player who wants to be King. Every role change arrives as an RPC targeted at the state authority, which exits on the first of these that fails:

```csharp
if (callerPlayer.MyFaction != targetPlayer.MyFaction) return;
if (callerPlayer.MyRole != PlayerRoles.King) return;
if (role == PlayerRoles.King) return;
if (targetRef == callerRef) return;
```

The cost is that the host peer has an advantage in reaction time, since their inputs never travel, and the session dies if the host leaves. I accepted both for a capstone. And host migration is one of the most difficult things to implement, and I found out it is a technical decision that is made before building the game logic, not after, so I left it alone.

## Input is a struct, not RPCs

Clients never tell the host what happened. They tell the host what buttons are down, and the host figures out what happened.

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

That is the entire network input for the game. Movement, attack, block, sprint, and the world space aim point, which I send instead of a screen position because every client has a different camera.

There is one problem this creates that took me a while to see. `OnInput` is called on the network tick, but mouse clicks are polled in `Update`, which runs at render rate. If you click and release between two ticks, the click never existed as far as the simulation is concerned, and the player feels the game eat their input. So the click gets latched:

```csharp
public bool ConsumeQueuedAttack(out Vector2 aimWorld)
{
    aimWorld = _queuedAim;
    if (!_queuedAttack) return false;
    _queuedAttack = false;
    return true;
}
```

`Update` sets the flag, `OnInput` consumes it exactly once. No click is dropped, and no click is ever read twice, which would have been the worse bug.

## Attacking without waiting for the server

An RPC-based attack costs you a round trip before your own character moves, which at 80ms ping is 160ms of nothing happening after you click.

The attack instead runs inside `FixedUpdateNetwork`, which means Fusion predicts it locally and resimulates it when the authoritative state arrives. Your own swing starts on the frame you click.

```csharp
if (data.attack && !data.block && NextAttackTimer.ExpiredOrNotRunning(Runner))
{
    NextAttackTimer = TickTimer.CreateFromSeconds(Runner, AttackCooldownTime);
// ...
}
```

`NextAttackTimer` is a `[Networked] TickTimer`. The client predicts it so the local cooldown feels instant, but the host holds the authoritative value, so a client that patches out its own cooldown check just gets its extra swings thrown away on the next resimulation.

Damage is not applied on the swing frame. The swing sets a second timer:

```csharp
AttackDelayTimer = TickTimer.CreateFromSeconds(Runner, AttackDamageDelay);
QueuedAttackAim = aimWorld;
```

and damage resolves 0.1 seconds later, on the frame where the animation actually connects. Because the delay is a `TickTimer` and the aim is `[Networked]`, the whole thing survives resimulation correctly instead of firing multiple times during rollback. The damage block itself is wrapped in `if (HasStateAuthority)`, so the client predicts the animation and the host decides the outcome.

## Custom collision instead of Rigidbody2D

Players do not use Unity's 2D physics for movement. Position is integrated directly in `FixedUpdateNetwork` and then pushed out of overlaps by hand:

```csharp
Vector2 displacement = (Vector2)transform.position - hit.ClosestPoint(transform.position);
float penetrationDepth = circleCollider.radius - displacement.magnitude;

if (penetrationDepth > 0f)
    transform.Translate((displacement == Vector2.zero ? Vector2.up : displacement.normalized) * penetrationDepth);
```

The reason is that Fusion resimulates ticks and Unity's 2D physics solver does not rewind with it. Any velocity based movement drifts apart between host and client over a few rollbacks. Depenetration is stateless, so running it five times during a resimulation produces the same answer as running it once.

As a result, no bounce, no friction, no physics materials, no joints. For a game where the collisions are "do not walk through walls or through each other" it does the job perfectly.

## The server counts the votes

Votes live in a networked dictionary:

```csharp
[Networked, Capacity(8)]
private NetworkDictionary<PlayerRef, PlayerRef> Votes => default;
```

Every vote arrives through an RPC targeted at the state authority, so the body only ever runs on the host. It checks that voter and candidate share a faction, that nobody voted twice, and that the 15 second discussion timer has expired before recording anything.

## Enemy AI

PvE fills Red with bots, and a bot is the same `Player` prefab spawned with no input authority. `BotController` runs all of them on the host inside one `FixedUpdateNetwork`, writing the properties a human's input would drive: `MyRole`, `IsBlocking`, `IsMining`, position, health. Bots inherit role speeds, crown drops and death handling with no separate code path.

Behavior branches on role. Soldiers chase the nearest enemy within 15 units, or take the nearest capture zone the faction does not already hold. Pawns only fight if an enemy is close; otherwise they mine and fund the resource race. Kings run while they still have subjects and fight when no allies remain.

Bots don't walk straight at their target. My first version re-picked a way around obstacles every frame, which left two bots grinding against the same wall forever, so now a bot that moves less than 0.1 units in half a second commits to one strafe side for 0.6 seconds.

They are not the weak point; they are the balance problem. PvE always spawns four, so testing solo or with one friend means a full Red team beats you. A 45-second delayed start and one gap hold them back: a player who hits and backs out of range is gone before the bot's delayed damage step re-checks distance, so hit-and-run beats them reliably. That is a bug in the attack validation, and I left it in because it is the only thing making them beatable at low player counts.

## What I would do differently

**Bot allies**

The game is only 4v4 right now, which isn't small even for PvE mode, since you still need people to connect to your game. The main issue is this game is fun only when you scale the player count, and I should have paid more attention to bot allies. That immediately solves the cold start problem with an empty lobby, while letting me test solo and scaling the PvP to 8v8, 16v16 and so on.

**Roles that did not ship**

Other scope creeps I had to manage were the Servant role, a political branch that works as a minister to the King. The role is still in the code, but a 4 player kingdom didn't require this management hierarchy, so in practice it's King, Soldiers and Pawns. There are also subclasses where Soldiers can equip different styles, Strength, Agility and Power, to strategize and give autonomy to lesser ranks too. Pawns for example could have been able to craft fortifications, farm, and use Militia mode to defend themselves, but none of these made it to the game.

**Prioritize the Legitimacy system idea I had**

My most important design decision was planning a Legitimacy Meter System that changed the King's unstoppable rule, and gave further social dynamics between roles. The King could lose legitimacy by abusing their authority, ignoring their subjects, or making unpopular decisions, while maintaining it through effective leadership and cooperation. Players could demote the King's legitimacy, and then watch the King lose power over time, or approve his rule, and give him an iron fist that would empower the King and make the Kingdom more coordinated.

**Code**

`NetworkManager.cs` is the one I would change the most. It owns session lifecycle, implements every Fusion callback, builds the input struct, spawns the lobby and the player panel, drives the spawner, and holds eleven main menu UI references that it redraws every frame.

The mistake was giving one class two lifetimes. The runner must survive MainMenu into Gameplay and back, so NetworkManager is `DontDestroyOnLoad`, but its UI references die with the menu scene and it also sits in that scene. Every return loads a second copy: one has live Inspector references and no session, the other has the runner and null buttons. Disconnect and you cannot host again. Re-finding widgets by name in `OnSceneLoaded` held up until anyone renamed anything. What shipped is a handover, where the old copy passes the runner, lobby and join code to the new one and destroys itself. The duplicate is still created every load, the handover just makes it harmless.

It should have been a session object created in code at runtime, living in no scene so Unity has nothing to duplicate, plus a LobbyUI script in the menu scene holding the Inspector references and receiving the button UnityEvents, which is the only reason the manager was in the scene at all. I had it backwards: a scene can find one persistent object easily, one persistent object cannot find eleven that get rebuilt every load.

`Player.cs` is doing too much for the same reason. Movement, combat, visuals, domination, death, respawn and crown handling are all in one file. Combat and the visual state machine should be their own components on the same object.

`FindObjectsOfType<Player>()` appears in several paths that run often, including the UI refresh. It works fine at eight players and would be indefensible at thirty. The host should own a registry populated in `Spawned` and `Despawned` and everything should read from that.

Respawn uses `WaitForSeconds(30f)`. That is wall clock time inside a tick based simulation. It should be a `TickTimer` like every other timer in the project.

In conclusion, Crown of Domination had about four months of development, and its strongest features are still not implemented. I have a lot left to learn about networking and coding, despite everything I got working so far. With another four months, I would add bot allies to fix the cold start problem and the legitimacy meter, because it's the only way to balance the role asymmetry and reinforce socializing for both the King and other roles. Then code refactoring, since that's what makes debugging and adding features efficient.
