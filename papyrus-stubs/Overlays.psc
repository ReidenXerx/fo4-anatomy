Scriptname Overlays Native Hidden
{Import-only stub of LooksMenu's (F4EE) Overlays, for compiling Anatomy:Arousal; never shipped. The struct
and the signatures are read from its compiled script (LooksMenu - Main.ba2, Scripts/Overlays.pex),
not remembered: Add(Actor, Bool isFemale, Entry) -> Int uid, GetAll, Remove(uid), Update(Actor).}

Struct Entry
	String template
	Int uid
	Float red
	Float green
	Float blue
	Float alpha
	Float offset_u
	Float offset_v
	Float scale_u
	Float scale_v
	Int priority
EndStruct

Int Function Add(Actor akActor, Bool isFemale, Entry overlay) Native Global
Bool Function Remove(Actor akActor, Bool isFemale, Int uid) Native Global
Entry[] Function GetAll(Actor akActor, Bool isFemale) Native Global
Function Update(Actor akActor) Native Global
