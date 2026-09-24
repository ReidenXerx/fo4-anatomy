Scriptname AnatomyAim Native Hidden
{fo4-anatomy A-28: who is in a scene, for the aim in fo4-anatomy's cbp.dll (the fo4-ocbpc fork), which
registers this native. Anatomy:Arousal calls it; nothing else needs to.}

; Everyone near the player in an AAF scene. The aim turns a shaft onto an opening only between these,
; and forgets the list when it is not told again for ten seconds.
Function SetBusy(Actor[] akBusy) Global Native
