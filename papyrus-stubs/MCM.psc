Scriptname MCM Native Hidden
{IMPORT ONLY - never compiled into the release. The natives Anatomy:Arousal calls on Mod Configuration
 Menu (F4SE Menu Framework ships the real MCM.pex). Declared here so the build does not depend on a
 game folder; signatures as MCM documents them (copied from fo4-chemistry/papyrus-stubs/MCM.psc).}

Bool Function IsInstalled() Native Global
Int Function GetModSettingInt(String asModName, String asSetting) Native Global
Bool Function GetModSettingBool(String asModName, String asSetting) Native Global
Float Function GetModSettingFloat(String asModName, String asSetting) Native Global
