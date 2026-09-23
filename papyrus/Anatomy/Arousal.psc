Scriptname Anatomy:Arousal extends Quest
{Arousal, and what it does to her nipples (fo4-anatomy decision A-16, the owner's poll 2026-09-23).

Every few seconds each woman near the player moves toward the strongest thing arousing her:

  in an AAF scene (AAF's busy keyword)             1.0   fast (half-life 10 s)
  Ivy, when her own mod says she is aroused        0.8   (CompanionIvy.esm _ivy_IsAroused)
  watching a scene within WATCH_RADIUS             0.55  (half-life 30 s)
  a companion's Overture Desire (0..1)             0.7 x Desire (Overture.esp OvertureCompanionDesire)
  naked (nothing in the body slot)                 0.3   slow (half-life 45 s)

and falls back when it is gone (half-life 60 s: she stays aroused a while after a scene).

Her nipples follow it: NippleLength, NipplePerk2, NippleTip and NippleSize rise by GAINS x arousal,
in steps of a tenth, ON TOP of her own shape. LooksMenu takes the MAX over its keyword layers, so our
layer (Anatomy.esp's keyword) is written as her strongest other value plus our rise: a woman with
small nipples stays smaller than one with big ones, and Silhouette's flattening under heavy clothes
(NipBGone) still wins where armour covers them. At zero the layer is removed and she is forgotten.

Every source is optional: a missing plugin only removes that source. No AAF call is made (a call
into AAF can end the calling stack, fo4-rapport docs/aaf-under-the-hood.md); only its keyword is read.}

Int Property TICK = 1 AutoReadOnly
Float Property TICK_SECONDS = 3.0 AutoReadOnly
Float Property SCAN_RADIUS = 3000.0 AutoReadOnly     ; ~43 m: the people around the player
Float Property WATCH_RADIUS = 1200.0 AutoReadOnly    ; ~17 m from someone in a scene
Int Property MAX_PEOPLE = 100 AutoReadOnly           ; Papyrus arrays hold 128
Float Property MAX_STEP_SECONDS = 10.0 AutoReadOnly  ; menus stop the timer, not the clock

Float Property SCENE_DRIVE = 1.0 AutoReadOnly
Float Property SCENE_HALF = 10.0 AutoReadOnly
Float Property IVY_DRIVE = 0.8 AutoReadOnly
Float Property IVY_HALF = 20.0 AutoReadOnly
Float Property WATCH_DRIVE = 0.55 AutoReadOnly
Float Property WATCH_HALF = 30.0 AutoReadOnly
Float Property DESIRE_SCALE = 0.7 AutoReadOnly
Float Property DESIRE_HALF = 45.0 AutoReadOnly
Float Property NAKED_DRIVE = 0.3 AutoReadOnly
Float Property NAKED_HALF = 45.0 AutoReadOnly
Float Property FALL_HALF = 60.0 AutoReadOnly

Actor[] _who
Float[] _level
Float[] _shown
Float _lastTick = -1.0

String[] _morphs
Float[] _gains
Keyword _layer
Keyword _npc
Race _human
Keyword _busy
ActorValue _desire
GlobalVariable _ivyAroused
ActorBase _ivy

Event OnInit()
	Setup()
	StartTimer(TICK_SECONDS, TICK)
EndEvent

Event Actor.OnPlayerLoadGame(Actor akSender)
	Setup()                                  ; plugins may have come or gone since the save
	_lastTick = -1.0                         ; the real-time clock restarts with the game
	StartTimer(TICK_SECONDS, TICK)
EndEvent

Event OnTimer(Int aiTimerID)
	If aiTimerID == TICK
		Tick()
		StartTimer(TICK_SECONDS, TICK)
	EndIf
EndEvent

Function Setup()
	RegisterForRemoteEvent(Game.GetPlayer(), "OnPlayerLoadGame")
	If _who == None
		_who = new Actor[0]
		_level = new Float[0]
		_shown = new Float[0]
	EndIf
	_morphs = new String[4]
	_gains = new Float[4]
	_morphs[0] = "NippleLength"               ; the erection itself: up to 1.1 units out at 1.0
	_gains[0] = 0.55
	_morphs[1] = "NipplePerk2"
	_gains[1] = 0.5
	_morphs[2] = "NippleTip"
	_gains[2] = 0.4
	_morphs[3] = "NippleSize"
	_gains[3] = 0.25
	_layer = Game.GetFormFromFile(0x00000801, "Anatomy.esp") as Keyword
	_npc = Game.GetFormFromFile(0x00013794, "Fallout4.esm") as Keyword          ; ActorTypeNPC
	_human = Game.GetFormFromFile(0x00013746, "Fallout4.esm") as Race           ; HumanRace
	_busy = None
	If Game.IsPluginInstalled("AAF.esm")
		AAF:AAF_API api = Game.GetFormFromFile(0x00000F99, "AAF.esm") as AAF:AAF_API
		If api != None
			_busy = api.AAF_ActorBusy
		EndIf
	EndIf
	_desire = None
	If Game.IsPluginInstalled("Overture.esp")
		_desire = Game.GetFormFromFile(0x00000851, "Overture.esp") as ActorValue
	EndIf
	_ivyAroused = None
	_ivy = None
	If Game.IsPluginInstalled("CompanionIvy.esm")
		_ivyAroused = Game.GetFormFromFile(0x000011AA, "CompanionIvy.esm") as GlobalVariable
		_ivy = Game.GetFormFromFile(0x00000803, "CompanionIvy.esm") as ActorBase
	EndIf
	Debug.Trace("[Anatomy] arousal: layer " + (_layer != None) + ", AAF busy keyword " + (_busy != None) \
		+ ", Overture desire " + (_desire != None) + ", Ivy " + (_ivyAroused != None && _ivy != None) \
		+ ", tracking " + _who.Length, 0)
EndFunction

Function Tick()
	If _layer == None || _npc == None
		Return
	EndIf
	Float now = Utility.GetCurrentRealTime()
	Float dt = TICK_SECONDS
	If _lastTick >= 0.0 && now > _lastTick
		dt = now - _lastTick
	EndIf
	_lastTick = now
	If dt > MAX_STEP_SECONDS
		dt = MAX_STEP_SECONDS
	EndIf

	Actor player = Game.GetPlayer()
	Actor[] people = new Actor[0]
	people.Add(player, 1)
	ObjectReference[] near = player.FindAllReferencesWithKeyword(_npc, SCAN_RADIUS)
	Int i = 0
	While near != None && i < near.Length && people.Length < MAX_PEOPLE
		If near[i] is Actor
			Actor a = near[i] as Actor
			If a != player && !a.IsDead() && a.Is3DLoaded()
				people.Add(a, 1)
			EndIf
		EndIf
		i += 1
	EndWhile

	Actor[] busy = new Actor[0]
	If _busy != None
		i = 0
		While i < people.Length
			If people[i].HasKeyword(_busy)
				busy.Add(people[i], 1)
			EndIf
			i += 1
		EndWhile
	EndIf

	; everyone here who could be aroused
	i = 0
	While i < people.Length
		Actor a = people[i]
		If IsWoman(a)
			Int k = _who.Find(a, 0)
			Float cur = 0.0
			If k >= 0
				cur = _level[k]
			EndIf
			Float nxt = Next(a, cur, busy, dt)
			If k < 0
				If nxt > 0.001 && _who.Length < MAX_PEOPLE      ; anything arousing her: start counting
					_who.Add(a, 1)
					_level.Add(nxt, 1)
					_shown.Add(0.0, 1)
					k = _who.Length - 1
				EndIf
			Else
				If nxt < 0.02 && nxt <= cur                       ; fading out: let go below
					nxt = -1.0
				EndIf
				_level[k] = nxt
			EndIf
			If k >= 0 && _level[k] >= 0.0
				Show(k)
			EndIf
		EndIf
		i += 1
	EndWhile

	; the tracked who are no longer here: let go of them
	i = _who.Length - 1
	While i >= 0
		Actor a = _who[i]
		If a == None || people.Find(a, 0) < 0 || _level[i] < 0.0
			Forget(i)
		EndIf
		i -= 1
	EndWhile
EndFunction

Bool Function IsWoman(Actor a)
	If a == None || a.GetRace() != _human
		Return False
	EndIf
	ActorBase b = a.GetLeveledActorBase()
	Return b != None && b.GetSex() == 1
EndFunction

; Where her arousal is a step later: toward the strongest source, at that source's pace, or down.
Float Function Next(Actor a, Float cur, Actor[] busy, Float dt)
	Float drive = 0.0
	Float half = FALL_HALF
	If _busy != None && a.HasKeyword(_busy)
		drive = SCENE_DRIVE
		half = SCENE_HALF
	Else
		If _ivy != None && _ivyAroused != None && a.GetActorBase() == _ivy && _ivyAroused.GetValue() >= 1.0
			drive = IVY_DRIVE
			half = IVY_HALF
		EndIf
		If WATCH_DRIVE > drive && Watching(a, busy)
			drive = WATCH_DRIVE
			half = WATCH_HALF
		EndIf
		If _desire != None
			Float d = a.GetValue(_desire) * DESIRE_SCALE
			If d > drive
				drive = d
				half = DESIRE_HALF
			EndIf
		EndIf
		If NAKED_DRIVE > drive && Naked(a)
			drive = NAKED_DRIVE
			half = NAKED_HALF
		EndIf
	EndIf
	If drive < cur
		half = FALL_HALF
	EndIf
	Float nxt = cur + (drive - cur) * (1.0 - Math.Pow(0.5, dt / half))
	If nxt < 0.0
		nxt = 0.0
	ElseIf nxt > 1.0
		nxt = 1.0
	EndIf
	Return nxt
EndFunction

Bool Function Watching(Actor a, Actor[] busy)
	Int j = 0
	While j < busy.Length
		If busy[j] != a && a.GetDistance(busy[j]) < WATCH_RADIUS
			Return True
		EndIf
		j += 1
	EndWhile
	Return False
EndFunction

Bool Function Naked(Actor a)
	Actor:WornItem worn = a.GetWornItem(3, False)       ; slot 33, the body
	Return worn == None || worn.item == None
EndFunction

; Put tracked woman k's nipples where her arousal says, in tenths (each change rebuilds her morphs).
Function Show(Int k)
	Actor a = _who[k]
	Float stepped = Math.Floor(_level[k] * 10.0 + 0.5) / 10.0
	If stepped == _shown[k]
		Return
	EndIf
	_shown[k] = stepped
	If stepped <= 0.0
		BodyGen.RemoveMorphsByKeyword(a, True, _layer)
	Else
		Int m = 0
		While m < _morphs.Length
			BodyGen.SetMorph(a, True, _morphs[m], _layer, Strongest(a, _morphs[m]) + _gains[m] * stepped)
			m += 1
		EndWhile
	EndIf
	BodyGen.UpdateMorphs(a)
EndFunction

; Her value of a morph from every layer but ours: what LooksMenu would show without us.
Float Function Strongest(Actor a, String asMorph)
	Float best = BodyGen.GetMorph(a, True, asMorph, None)
	Keyword[] kws = BodyGen.GetKeywords(a, True, asMorph)
	Int j = 0
	While kws != None && j < kws.Length
		If kws[j] != None && kws[j] != _layer
			Float v = BodyGen.GetMorph(a, True, asMorph, kws[j])
			If v > best
				best = v
			EndIf
		EndIf
		j += 1
	EndWhile
	Return best
EndFunction

Function Forget(Int k)
	Actor a = _who[k]
	If a != None && _shown[k] > 0.0
		BodyGen.RemoveMorphsByKeyword(a, True, _layer)
		If a.Is3DLoaded()
			BodyGen.UpdateMorphs(a)
		EndIf
	EndIf
	_who.Remove(k, 1)
	_level.Remove(k, 1)
	_shown.Remove(k, 1)
EndFunction
