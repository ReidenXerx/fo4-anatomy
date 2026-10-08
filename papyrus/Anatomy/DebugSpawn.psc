ScriptName Anatomy:DebugSpawn
; Test helpers for the console (the owner, 2026-10-08: "fast debug option to spawn servitron in necessary complectation").
; Global functions, so no plugin record is needed:
;   cgf "Anatomy:DebugSpawn.Servitron" 0      a Servitron in front of you: rubber abdomen GITS (the rigged one)
;   cgf "Anatomy:DebugSpawn.Servitron" 1      the same with the Wetsuit Rubber abdomen
;   cgf "Anatomy:DebugSpawn.Servitron" 2      a MALE Servitron: Anatomy's male GITS Rubber abdomen (AnatomyServitron.esp)
;   cgf "Anatomy:DebugSpawn.Servitron" 3      a male Servitron in the male Wetsuit Rubber abdomen
; Built from Servitron's own Test Dummy and its part mods (Servitron.esm, Nexus 32801), so it is what the Robot
; Workbench would make: head, eyes, ears, a torso with breasts, arms, hands, legs, the rubber abdomen and the female
; animations. It carries AAF's AAF_GenderOverride_Female at once (Anatomy's arousal tick would add it within a tick).

Function Servitron(Int aiWetsuit) global
	ActorBase dummy = Game.GetFormFromFile(0x000008BD, "Servitron.esm") as ActorBase     ; ServitronDummyNpc
	If dummy == None
		Debug.Notification("Anatomy: Servitron.esm is not loaded")
		Return
	EndIf
	Actor player = Game.GetPlayer()
	Actor s = player.PlaceAtMe(dummy, 1, True, False, False) as Actor
	If s == None
		Debug.Notification("Anatomy: the Servitron could not be placed")
		Return
	EndIf
	Int[] parts = new Int[0]
	parts.Add(0x00000BBD, 1)          ; Head - Servitron
	parts.Add(0x00000BB4, 1)          ; Eyes - Mk1
	parts.Add(0x00000BB1, 1)          ; Ears - Servitron
	parts.Add(0x0000108A, 1)          ; Torso - Mk2 with breasts
	parts.Add(0x00001095, 1)          ; Torso Front Armor - none (the Test Dummy wears the Assaultron plate over the breasts)
	parts.Add(0x00000B9E, 1)          ; Arm Left - Servitron
	parts.Add(0x00000BA0, 1)          ; Arm Right - Servitron
	parts.Add(0x00000BB9, 1)          ; Hand Left
	parts.Add(0x00000BBB, 1)          ; Hand Right
	parts.Add(0x00000BC2, 1)          ; Legs - Servitron
	Bool male = aiWetsuit >= 2
	If aiWetsuit == 1
		parts.Add(0x00000B8C, 1)      ; Abdomen - Wetsuit Rubber
	ElseIf !male
		parts.Add(0x00000B89, 1)      ; Abdomen - GITS Rubber
	EndIf
	If male
		parts.Add(0x00000B8D, 1)      ; Animations - Default (a man's)
	Else
		parts.Add(0x00000B8E, 1)      ; Animations - Female
	EndIf
	Int attached = 0
	Int i = 0
	While i < parts.Length
		ObjectMod m = Game.GetFormFromFile(parts[i], "Servitron.esm") as ObjectMod
		If m != None && s.AttachMod(m, 0)
			attached += 1
		EndIf
		i += 1
	EndWhile
	If male                          ; Anatomy's male abdomen (AnatomyServitron.esp: 0x800 GITS, 0x802 Wetsuit)
		ObjectMod mm = None
		If Game.IsPluginInstalled("AnatomyServitron.esp")
			Int id = 0x00000800
			If aiWetsuit == 3
				id = 0x00000802
			EndIf
			mm = Game.GetFormFromFile(id, "AnatomyServitron.esp") as ObjectMod
		EndIf
		If mm == None
			Debug.Notification("Anatomy: AnatomyServitron.esp is not loaded: no male abdomen")
		ElseIf s.AttachMod(mm, 0)
			attached += 1
		EndIf
	EndIf
	; it landed dead (the owner, 10-08: "why this our command spawn them dead?"): the Test Dummy is only ever a workbench
	; preview, and swapping a robot's parts on a live actor can drop its health to nothing. Bring it back whole.
	Bool wasDead = s.IsDead()
	If wasDead
		s.Resurrect()
	EndIf
	s.ResetHealthAndLimbs()
	s.SetUnconscious(False)
	Debug.Trace("Anatomy:DebugSpawn " + s + ": dead after the parts " + wasDead + ", now " + s.IsDead(), 0)
	If Game.IsPluginInstalled("AAF.esm")
		Int kw = 0x000121BC                                                                 ; AAF_GenderOverride_Female
		If male
			kw = 0x000121BB                                                                 ; AAF_GenderOverride_Male
		EndIf
		Keyword role = Game.GetFormFromFile(kw, "AAF.esm") as Keyword
		If role != None && !s.HasKeyword(role)
			s.AddKeyword(role)
		EndIf
	EndIf
	Debug.Notification("Anatomy: a test Servitron, " + attached + " of " + parts.Length + " parts on")
	Debug.Trace("Anatomy:DebugSpawn " + s + ": " + attached + " of " + parts.Length + " Servitron parts attached", 0)
EndFunction
