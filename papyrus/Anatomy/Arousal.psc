Scriptname Anatomy:Arousal extends Quest
{Arousal, and what it does to her nipples (fo4-anatomy decision A-16, the owner's poll 2026-09-23).

Every few seconds each woman near the player moves toward the strongest thing arousing her:

  in an AAF scene (AAF's busy keyword)             1.0   fast (half-life 10 s)
  Ivy, when her own mod says she is aroused        0.8   (CompanionIvy.esm _ivy_IsAroused)
  watching a scene within WATCH_RADIUS             0.55  (half-life 30 s)
  a companion's Overture Desire (0..1)             0.7 x Desire (Overture.esp OvertureCompanionDesire)
  naked (nothing in the body slot)                 0.3   slow (half-life 45 s)

and falls back when it is gone (half-life 60 s: she stays aroused a while after a scene).

Her nipples follow it: NippleLength, NipplePerk2, NippleTip and NipplePerkiness rise by GAINS x arousal,
in steps of a tenth, ON TOP of her own shape. LooksMenu takes the MAX over its keyword layers, so our
layer (Anatomy.esp's keyword) is written as her strongest other value plus our rise: a woman with
small nipples stays smaller than one with big ones, and Silhouette's flattening under heavy clothes
(NipBGone) still wins where armour covers them. At zero the layer is removed and she is forgotten.

Every source is optional: a missing plugin only removes that source. No AAF call is made (a call
into AAF can end the calling stack, fo4-rapport docs/aaf-under-the-hood.md); only its keyword is read.

The player's settings (MCM, page "Arousal"; tools/build_mcm.py builds the menu from Defaults()) are
read every tick: on/off (off removes every layer of ours), how far the nipples rise, how fast arousal
rises and fades, and which sources count. Without MCM the defaults below are the behaviour.}

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

; the player's settings (Defaults() and LoadSettings())
Bool bEnabled = True
Float fNippleStrength = 1.0      ; x GAINS: 1 is the tuned look, 0 shows nothing
Float fRiseSpeed = 1.0           ; divides every source's half-life
Float fFadeSpeed = 1.0           ; divides FALL_HALF
Bool bScenes = True
Bool bWatching = True
Bool bCompanions = True          ; Ivy's own arousal and Overture's Desire
Bool bNaked = True
Bool _mcm = False
Float _appliedStrength = -1.0    ; the strength the shown layers were written with
Int _aimBusy = 0                 ; how many the fork's aim was last told are in a scene (A-28)

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
Keyword _refit                   ; Silhouette's refit marker keyword, None without Silhouette

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

; Silhouette put a new body on her (its S-24 event). Our layer is her own strongest value plus the
; rise, so it is rebuilt against the new body now, not when her arousal next changes a step.
Event Silhouette:Bridge.OnActorGenerated(Silhouette:Bridge akSender, Var[] akArgs)
	If akArgs == None || akArgs.Length < 1
		Return
	EndIf
	Actor a = akArgs[0] as Actor
	Int k = _who.Find(a)
	If k >= 0 && _shown[k] > 0.0
		_shown[k] = -1.0                         ; "a layer may be on her": Show rebuilds it
		Show(k)
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
	; the owner's first look (2026-09-23): "gorgeous ... lets make nipples a slightly bigger in erect
	; state": length 0.55 -> 0.70 and size 0.25 -> 0.40; perk and tip kept. Then (2026-09-24, Photo163):
	; "lets make nipple erection SLIGHLY less" -- every gain about an eighth down. Then (2026-09-25): "not
	; only longer but also wider ... more BUMPED not just STRETCHED". Measured (A-16): Length pushes a thin
	; tube out (radius ~0.5), and NippleSize NARROWS the tip (0.43 -> 0.25); Perk2 and Perkiness widen it
	; into a dome. The same height (0.85 over the resting tip, was 0.83), 1.6-2x as wide all the way up.
	_morphs[0] = "NippleLength"               ; the erection itself: up to 1.1 units out at 1.0
	_gains[0] = 0.30
	_morphs[1] = "NipplePerk2"                ; the bump: widest at the nipple's base
	_gains[1] = 0.70
	_morphs[2] = "NippleTip"
	_gains[2] = 0.35
	_morphs[3] = "NipplePerkiness"            ; a puffier areola under it
	_gains[3] = 0.40
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
	; Silhouette's refit marker (its S-49/S-50 contract, 2026-09-23): the keyword SilhouetteRefitKeyword
	; (Silhouette.esp 0x803, light) carries the morph "Silhouette_Refit"
	_refit = None
	If Game.IsPluginInstalled("Silhouette.esp")
		_refit = Game.GetFormFromFile(0x00000803, "Silhouette.esp") as Keyword
		; its new bodies (the Silhouette session's request, 2026-09-23): the event handler above
		Silhouette:Bridge bridge = Game.GetFormFromFile(0x00000802, "Silhouette.esp") as Silhouette:Bridge
		If bridge != None
			RegisterForCustomEvent(bridge, "OnActorGenerated")
		EndIf
	EndIf
	; asked once per load, not every tick: without MCM.pex the call fails (and logs) and answers False
	_mcm = MCM.IsInstalled()
	LoadSettings()
	Debug.Trace("[Anatomy] arousal: layer " + (_layer != None) + ", AAF busy keyword " + (_busy != None) \
		+ ", Overture desire " + (_desire != None) + ", Ivy " + (_ivyAroused != None && _ivy != None) \
		+ ", MCM " + _mcm + ", enabled " + bEnabled + ", tracking " + _who.Length, 0)
EndFunction

Function Defaults()
	bEnabled = True
	fNippleStrength = 1.0
	fRiseSpeed = 1.0
	fFadeSpeed = 1.0
	bScenes = True
	bWatching = True
	bCompanions = True
	bNaked = True
EndFunction

Function LoadSettings()
	Defaults()
	; MCM answers -1 / false for any key it never loaded (f4mcm SettingStore.cpp), and a false bEnabled
	; would read as the player switching it off. A slider key cannot prove the defaults were loaded: a
	; player's one moved slider is answered from Settings/Anatomy.ini while every other key is missing.
	; So settings.ini carries [Meta] iDefaults=1 on no control (MCM loads every key of it, measured in
	; its source); without it the defaults stand.
	If _mcm && MCM.GetModSettingInt("Anatomy", "iDefaults:Meta") == 1
		bEnabled = MCM.GetModSettingBool("Anatomy", "bEnabled:General")
		fNippleStrength = AtLeast(MCM.GetModSettingFloat("Anatomy", "fNippleStrength:General"), 0.0)
		fRiseSpeed = AtLeast(MCM.GetModSettingFloat("Anatomy", "fRiseSpeed:General"), 0.1)
		fFadeSpeed = AtLeast(MCM.GetModSettingFloat("Anatomy", "fFadeSpeed:General"), 0.1)
		bScenes = MCM.GetModSettingBool("Anatomy", "bScenes:Sources")
		bWatching = MCM.GetModSettingBool("Anatomy", "bWatching:Sources")
		bCompanions = MCM.GetModSettingBool("Anatomy", "bCompanions:Sources")
		bNaked = MCM.GetModSettingBool("Anatomy", "bNaked:Sources")
	EndIf
EndFunction

Float Function AtLeast(Float value, Float floor)
	If value < floor
		Return floor
	EndIf
	Return value
EndFunction

Function Tick()
	If _layer == None || _npc == None
		Return
	EndIf
	LoadSettings()
	If !bEnabled                                 ; switched off: nothing of ours stays on anyone
		Int w = _who.Length - 1
		While w >= 0
			Forget(w)
			w -= 1
		EndWhile
		_lastTick = -1.0
		TellAim(BusyAmong(People()))             ; the aim is not arousal's: it still hears who is in a scene
		Return
	EndIf
	If fNippleStrength != _appliedStrength       ; a new strength: rewrite every shown layer
		Int s = 0
		While s < _shown.Length
			If _shown[s] != 0.0
				_shown[s] = -1.0                     ; "a layer may be on her, value unknown": Show rewrites it
			EndIf
			s += 1
		EndWhile
		_appliedStrength = fNippleStrength
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

	Actor[] people = People()
	Actor[] busy = BusyAmong(people)
	TellAim(busy)
	Int i = 0

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

; the player and everyone alive and loaded around them
Actor[] Function People()
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
	Return people
EndFunction

; those of them in an AAF scene (AAF's busy keyword); nobody without AAF
Actor[] Function BusyAmong(Actor[] people)
	Actor[] busy = new Actor[0]
	If _busy != None
		Int i = 0
		While i < people.Length
			If people[i].HasKeyword(_busy)
				busy.Add(people[i], 1)
			EndIf
			i += 1
		EndWhile
	EndIf
	Return busy
EndFunction

; A-28: the fork's aim (cbp.dll) turns a shaft onto an opening only between people in a scene, and hears
; who they are from here, each tick while anyone is, and once more when nobody is. So with a cbp.dll that
; lacks the native, Papyrus can complain only during scenes.
Function TellAim(Actor[] busy)
	If busy.Length > 0 || _aimBusy > 0
		AnatomyAim.SetBusy(busy)
	EndIf
	_aimBusy = busy.Length
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
	Bool inScene = _busy != None && a.HasKeyword(_busy)
	If inScene && bScenes
		drive = SCENE_DRIVE                      ; the strongest source: nothing below can pass it
		half = SCENE_HALF
	EndIf
	If bCompanions && IVY_DRIVE > drive && _ivy != None && _ivyAroused != None && a.GetActorBase() == _ivy \
			&& _ivyAroused.GetValue() >= 1.0
		drive = IVY_DRIVE
		half = IVY_HALF
	EndIf
	; someone in a scene is not watching it: with scenes switched off, her partner next to her must not
	; count as a scene she watches
	If bWatching && !inScene && WATCH_DRIVE > drive && Watching(a, busy)
		drive = WATCH_DRIVE
		half = WATCH_HALF
	EndIf
	If bCompanions && _desire != None
		Float d = a.GetValue(_desire) * DESIRE_SCALE
		If d > drive
			drive = d
			half = DESIRE_HALF
		EndIf
	EndIf
	If bNaked && NAKED_DRIVE > drive && Naked(a)
		drive = NAKED_DRIVE
		half = NAKED_HALF
	EndIf
	If drive < cur
		half = FALL_HALF / fFadeSpeed
	Else
		half = half / fRiseSpeed
	EndIf
	Float nxt = cur + (drive - cur) * (1.0 - Math.Pow(0.5, dt / half))
	If nxt < 0.0
		nxt = 0.0
	ElseIf nxt > 1.0
		nxt = 1.0
	EndIf
	Return nxt
EndFunction

; Silhouette's marker: an EVEN whole number of 2 or more is heavy clothing (odd = light, 0.25 = being
; written, 0 or absent = none). Read directly, so any Silhouette version works and nothing is called.
Bool Function HeavilyDressed(Actor a)
	If _refit == None
		Return False
	EndIf
	Float v = BodyGen.GetMorph(a, True, "Silhouette_Refit", _refit)
	If v < 2.0
		Return False
	EndIf
	Int n = Math.Floor(v)
	Return (n as Float) == v && n % 2 == 0
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
	; heavily dressed (Silhouette's refit marker): her nipples stay flat under the armour. Our layer
	; comes off so Silhouette's NipBGone floor wins (LooksMenu shows the MAX: any value of ours would
	; beat a floor); her arousal keeps counting, and taking the armour off shows where it is
	If stepped > 0.0 && HeavilyDressed(a)
		stepped = 0.0
	EndIf
	If stepped == _shown[k]
		Return
	EndIf
	; LooksMenu runs BodyGen only for an actor with NO stored morphs, so a layer of ours on a woman
	; whose body is not generated yet would keep her bodiless (the Silhouette session, 2026-09-23)
	If _shown[k] <= 0.0 && stepped > 0.0 && !HasBody(a)
		Return                                   ; not yet: retried next tick, still unshown
	EndIf
	_shown[k] = stepped
	If stepped <= 0.0 || fNippleStrength <= 0.0
		BodyGen.RemoveMorphsByKeyword(a, True, _layer)
	Else
		Float rise = fNippleStrength * stepped
		; our layer is rewritten whole: a morph dropped from the set (NippleSize, 2026-09-25) must not stay
		; on a woman who was aroused when the save was made (Strongest skips our layer, so it reads the same)
		BodyGen.RemoveMorphsByKeyword(a, True, _layer)
		Int m = 0
		While m < _morphs.Length
			BodyGen.SetMorph(a, True, _morphs[m], _layer, Strongest(a, _morphs[m]) + _gains[m] * rise)
			m += 1
		EndWhile
	EndIf
	BodyGen.UpdateMorphs(a)
EndFunction

; She has a body: some morph of hers holds an UNKEYED value, the layer BodyGen and Silhouette write.
Bool Function HasBody(Actor a)
	String[] names = BodyGen.GetMorphs(a, True)
	Int j = 0
	While names != None && j < names.Length
		If BodyGen.GetMorph(a, True, names[j], None) != 0.0
			Return True
		EndIf
		j += 1
	EndWhile
	Return False
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
	If a != None && _shown[k] != 0.0             ; shown, or -1: a layer may be on her
		BodyGen.RemoveMorphsByKeyword(a, True, _layer)
		If a.Is3DLoaded()
			BodyGen.UpdateMorphs(a)
		EndIf
	EndIf
	_who.Remove(k, 1)
	_level.Remove(k, 1)
	_shown.Remove(k, 1)
EndFunction
