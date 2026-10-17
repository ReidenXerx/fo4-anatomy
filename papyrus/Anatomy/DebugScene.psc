ScriptName Anatomy:DebugScene
; Test scenes for the console (the owner, 2026-10-17: "full sequence with climax at the end for every kind of sexual
; activity, being able to pair any npc with it"). Global functions, so no plugin record is needed; the pair and the
; running sequence live on Anatomy:Arousal (Anatomy.esp's quest).
;
;   1. Pick two people: open the console, click someone, type   cgf "Anatomy:DebugScene.Pick"
;      then click the other one and type it again. Nobody clicked = the player. Picking someone twice drops them.
;   2. Run:   cgf "Anatomy:DebugScene.Run" <kind>
;        1 vaginal   2 anal   3 oral   4 handjob   5 titjob   6 footjob   0 all of them, one after another
;      Each run: an AAF scene of that kind, 20 s of it, the climax (AnatomyAim.Climax, as a CLIMAX stage gives it),
;      8 s more inside her, then the scene ends (he pulls out: the gush, the seep, the mouth running out). Notifications
;      say each step. A kind with no animation for the pair says so and is skipped.
;   cgf "Anatomy:DebugScene.RunTimed" <kind> <seconds>   the same with your own length before the climax
;   cgf "Anatomy:DebugScene.Climax"                      a climax now, for the pair (in any scene of theirs)
;   cgf "Anatomy:DebugScene.Stop"                        ends the pair's scene and any sequence waiting
;   cgf "Anatomy:DebugScene.Clear"                       forgets the pair
;
; Every AAF call goes out on a stack of its own (CallGlobalFunctionNoWait): an AAF call can keep its stack from ever
; returning (fo4-rapport docs/aaf-under-the-hood.md), and the sequence must go on. Whether a scene started is read from
; AAF's busy keyword, not from AAF's events: global functions hear no events.

; the timings (seconds; a global script has no properties): inside her after the climax before he pulls out 8, for AAF
; to put them in the scene 20, to let them go 15, and with "all" watching the fluid before the next kind 25

Anatomy:Arousal Function Quest() global
	Return Game.GetFormFromFile(0x00000800, "Anatomy.esp") as Anatomy:Arousal
EndFunction

Keyword Function Busy() global
	AAF:AAF_API api = Game.GetFormFromFile(0x00000F99, "AAF.esm") as AAF:AAF_API
	If api == None
		Return None
	EndIf
	Return api.AAF_ActorBusy
EndFunction

String Function Who(Actor a) global
	If a == None
		Return "nobody"
	ElseIf a == Game.GetPlayer()
		Return "you"
	EndIf
	Return a.GetDisplayName()
EndFunction

String Function PairText(Actor[] pair) global
	If pair.Length == 0
		Return "nobody picked"
	ElseIf pair.Length == 1
		Return Who(pair[0]) + " (pick one more)"
	EndIf
	Return Who(pair[0]) + " + " + Who(pair[1])
EndFunction

String Function KindName(Int aiKind) global
	If aiKind == 1
		Return "vaginal"
	ElseIf aiKind == 2
		Return "anal"
	ElseIf aiKind == 3
		Return "oral"
	ElseIf aiKind == 4
		Return "handjob"
	ElseIf aiKind == 5
		Return "titjob"
	ElseIf aiKind == 6
		Return "footjob"
	EndIf
	Return "?"
EndFunction

; the AAF tags tried for a kind, in order (the counts in the owner's packs, 2026-10-17: PenisToVagina 568,
; PenisToAnus 213, PenisToMouth 131, Blowjob 95, PenisToHand 91, HandToPenis 8, TitJob 4, PenisToNipples 9, Footjob 7,
; PenisToFeet 4)
String[] Function Tags(Int aiKind) global
	String[] t = new String[0]
	If aiKind == 1
		t.Add("PenisToVagina", 1)
	ElseIf aiKind == 2
		t.Add("PenisToAnus", 1)
	ElseIf aiKind == 3
		t.Add("PenisToMouth", 1)
		t.Add("Blowjob", 1)
	ElseIf aiKind == 4
		t.Add("PenisToHand", 1)
		t.Add("HandToPenis", 1)
	ElseIf aiKind == 5
		t.Add("TitJob", 1)
		t.Add("PenisToNipples", 1)
	ElseIf aiKind == 6
		t.Add("Footjob", 1)
		t.Add("PenisToFeet", 1)
	EndIf
	Return t
EndFunction

Function Say(String asText) global
	Debug.Notification("Anatomy debug: " + asText)
	Debug.Trace("[Anatomy] debug scene: " + asText, 0)
EndFunction

Function Pick() global
	Anatomy:Arousal q = Quest()
	If q == None
		Say("Anatomy.esp is not loaded")
		Return
	EndIf
	Actor a = Game.GetCurrentConsoleRef() as Actor
	If a == None
		a = Game.GetPlayer()
	EndIf
	q.DebugPick(a)
	Say(PairText(q.DebugPair()))
EndFunction

Function Clear() global
	Anatomy:Arousal q = Quest()
	If q != None
		q.DebugClear()
		Say("nobody picked")
	EndIf
EndFunction

Function Run(Int aiKind) global
	RunTimed(aiKind, 20)
EndFunction

Function RunTimed(Int aiKind, Int aiSeconds) global
	Anatomy:Arousal q = Quest()
	If q == None
		Say("Anatomy.esp is not loaded")
		Return
	EndIf
	If Busy() == None
		Say("AAF is not loaded")
		Return
	EndIf
	Actor[] pair = q.DebugPair()
	If pair.Length < 2
		Say(PairText(pair) + ": pick two people first")
		Return
	EndIf
	Int i = 0
	While i < 2
		If !pair[i].Is3DLoaded() || pair[i].IsDead()
			Say(Who(pair[i]) + " is not here (or is dead)")
			Return
		EndIf
		i += 1
	EndWhile
	If aiKind < 0 || aiKind > 6
		Say("kinds: 1 vaginal 2 anal 3 oral 4 handjob 5 titjob 6 footjob, 0 all")
		Return
	EndIf
	Float seconds = aiSeconds as Float
	If seconds < 3.0
		seconds = 3.0
	EndIf
	Int token = q.DebugNewToken()
	If aiKind != 0
		Sequence(q, token, pair, aiKind, seconds)
	Else
		Int k = 1
		Bool going = True
		While going && k <= 6
			going = Sequence(q, token, pair, k, seconds)
			If going && k < 6
				Say("next in " + 25 + " s")
				going = Pause(q, token, 25.0)
			EndIf
			k += 1
		EndWhile
	EndIf
	If token == q.DebugToken()
		Say("done")
	EndIf
EndFunction

; one kind: the scene, the climax, he pulls out. False when a stop or a new run took over.
Bool Function Sequence(Anatomy:Arousal q, Int token, Actor[] pair, Int aiKind, Float afSeconds) global
	Keyword busy = Busy()
	String kind = KindName(aiKind)
	If pair[0].HasKeyword(busy) || pair[1].HasKeyword(busy)
		Say("ending their current scene first")
		StopNoWait(pair)
		If !WaitBusy(q, token, pair, busy, False, 15.0)
			Return token == q.DebugToken()
		EndIf
	EndIf
	String[] tags = Tags(aiKind)
	Bool started = False
	Int t = 0
	While !started && t < tags.Length
		Say(kind + ": starting (" + tags[t] + ")")
		Var[] args = new Var[3]
		args[0] = pair[0]
		args[1] = pair[1]
		args[2] = tags[t]
		Utility.CallGlobalFunctionNoWait("Anatomy:DebugScene", "StartAAF", args)
		started = WaitBusy(q, token, pair, busy, True, 20.0)
		If token != q.DebugToken()
			Return False
		EndIf
		t += 1
	EndWhile
	If !started
		Say(kind + ": AAF found no animation for " + PairText(pair) + ", skipped")
		Return True
	EndIf
	Say(kind + ": climax in " + (afSeconds as Int) + " s")
	If !Pause(q, token, afSeconds)
		Return False
	EndIf
	If !pair[0].HasKeyword(busy) && !pair[1].HasKeyword(busy)
		Say(kind + ": the scene ended early, no climax")
		Return True
	EndIf
	Say(kind + ": climax")
	AnatomyAim.Climax(pair)
	If !Pause(q, token, 8.0)
		Return False
	EndIf
	Say(kind + ": pulling out")
	StopNoWait(pair)
	WaitBusy(q, token, pair, busy, False, 15.0)
	Return token == q.DebugToken()
EndFunction

; waits until both are (abWant) or neither is (!abWant) in a scene; False on the timeout or a stop
Bool Function WaitBusy(Anatomy:Arousal q, Int token, Actor[] pair, Keyword busy, Bool abWant, Float afTimeout) global
	Float waited = 0.0
	While waited < afTimeout && token == q.DebugToken()
		Bool a = pair[0].HasKeyword(busy)
		Bool b = pair[1].HasKeyword(busy)
		If abWant && a && b
			Return True
		ElseIf !abWant && !a && !b
			Return True
		EndIf
		Utility.Wait(0.5)
		waited += 0.5
	EndWhile
	Return False
EndFunction

; False when a stop or a new run took over
Bool Function Pause(Anatomy:Arousal q, Int token, Float afSeconds) global
	Float waited = 0.0
	While waited < afSeconds
		If token != q.DebugToken()
			Return False
		EndIf
		Utility.Wait(1.0)
		waited += 1.0
	EndWhile
	Return token == q.DebugToken()
EndFunction

Function StopNoWait(Actor[] pair) global
	Var[] args = new Var[1]
	args[0] = pair[0]
	Utility.CallGlobalFunctionNoWait("Anatomy:DebugScene", "StopAAF", args)
EndFunction

; on a stack of their own (CallGlobalFunctionNoWait)
Function StartAAF(Actor akA, Actor akB, String asTag) global
	AAF:AAF_API api = Game.GetFormFromFile(0x00000F99, "AAF.esm") as AAF:AAF_API
	If api == None
		Return
	EndIf
	AAF:AAF_API:SceneSettings s = api.GetSceneSettings()
	s.includeTags = asTag
	s.excludeTags = "Tease,Pose,Utility,Foreplay,NonSex"
	s.skipWalk = True
	s.preventFurniture = True
	s.duration = 600.0      ; AAF ignores it (a tree leaves by its own exit); the sequence ends the scene itself
	Actor[] actors = new Actor[2]
	actors[0] = akA
	actors[1] = akB
	api.StartScene(actors, s)
EndFunction

Function StopAAF(Actor akA) global
	AAF:AAF_API api = Game.GetFormFromFile(0x00000F99, "AAF.esm") as AAF:AAF_API
	If api != None
		api.StopScene(akA, -1)
	EndIf
EndFunction

Function Climax() global
	Anatomy:Arousal q = Quest()
	If q == None
		Return
	EndIf
	Actor[] pair = q.DebugPair()
	If pair.Length < 2
		Say(PairText(pair) + ": pick two people first")
		Return
	EndIf
	Say("climax: " + PairText(pair))
	AnatomyAim.Climax(pair)
EndFunction

Function Stop() global
	Anatomy:Arousal q = Quest()
	If q == None
		Return
	EndIf
	q.DebugNewToken()
	Actor[] pair = q.DebugPair()
	If pair.Length > 0
		StopNoWait(pair)
	EndIf
	Say("stopped")
EndFunction
