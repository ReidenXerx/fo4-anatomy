Scriptname AnatomyAim Native Hidden
{fo4-anatomy A-28: who is in a scene, for the aim in fo4-anatomy's cbp.dll (the fo4-ocbpc fork), which
registers this native. Anatomy:Arousal calls it; nothing else needs to.}

; Everyone near the player in an AAF scene. The aim turns a shaft onto an opening only between these,
; and forgets the list when it is not told again for ten seconds.
Function SetBusy(Actor[] akBusy) Global Native

; A stage tagged CLIMAX began (AAF's animation events, heard by Anatomy:Arousal): its actors. The engine's fluid
; strands: each man with a shaft chain inside an opening the aim holds leaves drips from it once he is out; outside,
; shots from his tip.
Function Climax(Actor[] akActors) Global Native

; For testing and support: a climax of the man aiHim with aiHer (form ids, decimal), as a CLIMAX stage gives it. Console:
;   cgf "AnatomyAim.ClimaxTest" <his form id> <her form id>
Function ClimaxTest(Int aiHim, Int aiHer) Global
	Actor[] actors = new Actor[0]
	Actor him = Game.GetForm(aiHim) as Actor
	Actor her = Game.GetForm(aiHer) as Actor
	If him != None
		actors.Add(him, 1)
	EndIf
	If her != None
		actors.Add(her, 1)
	EndIf
	Climax(actors)
EndFunction
