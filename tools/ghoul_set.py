"""The ghoul women's body, built by BodySlide on the player's PC (Dudu 2026-11-09: the Ghouls mod needs Anatomy, ships
no body mesh; the body is CBBE + Nahka's genitals, which nothing of ours may redistribute).

When the Ghouls plugin is active the builder adds:
    Tools/BodySlide/ShapeData/Anatomy/AnatomyGhoul.nif   Anatomy.nif with the genital shape's material renamed to
                                                         Materials\\Anatomy\\AnatomyGenitalsGhoul.bgsm (string table
                                                         only: every block keeps its bytes, nif.save_renamed)
    a second slider set "Anatomy Body (Ghoul)" in Anatomy.osp: the same sliders and .osd, that source file, output
    Meshes\\Actors\\Character\\CharacterAssets\\FemaleBodyGhoul (+ .tri when morphs are built), in the same groups
The Ghouls plugin points the ghoul torso's women's model (NakedGhoulTorso, Fallout4.esm 0EAFB9) at FemaleBodyGhoul.nif;
its skin texture swap still applies (only the model path differs), so only the genital shape changes material."""
import pathlib
import re

import nif

GHOUL_PLUGIN = 'Anatomy Ghoul Genitals.esp'
SET = 'Anatomy Body'
GHOUL_SET = 'Anatomy Body (Ghoul)'
GHOUL_SOURCE = 'AnatomyGhoul.nif'
GHOUL_OUTPUT = 'FemaleBodyGhoul'
HUMAN_MAT = 'Materials\\Anatomy\\AnatomyGenitals.bgsm'
GHOUL_MAT = 'Materials\\Anatomy\\AnatomyGenitalsGhoul.bgsm'
NIF_REL = 'Tools/BodySlide/ShapeData/Anatomy/' + GHOUL_SOURCE


def ghoul_nif(src, dst):
    """Anatomy.nif -> AnatomyGhoul.nif: the genital material string renamed, nothing else"""
    m = nif.Nif(src)
    hit = [s for s in m.strings if s.lower() == HUMAN_MAT.lower()]
    if len(hit) != 1:
        raise SystemExit(f'{src}: expected one {HUMAN_MAT} in its string table, found {hit}')
    m.save_renamed(dst, {hit[0]: GHOUL_MAT})
    back = nif.Nif(dst)
    if [s.name for s in back.shapes()] != [s.name for s in m.shapes()] or GHOUL_MAT not in back.strings:
        raise SystemExit(f'{dst}: the renamed copy does not read back as expected')
    return dst


def ghoul_osp(text):
    """Anatomy.osp with a second slider set: a copy of "Anatomy Body" pointed at AnatomyGhoul.nif and FemaleBodyGhoul"""
    m = re.search(r'(?s)(    <SliderSet name="' + re.escape(SET) + r'">.*?</SliderSet>\n)', text)
    if not m:
        raise SystemExit(f'Anatomy.osp has no slider set "{SET}"')
    block = m.group(1)
    copy = block.replace(f'<SliderSet name="{SET}">', f'<SliderSet name="{GHOUL_SET}">', 1)
    copy, n1 = re.subn(r'<SourceFile>[^<]*</SourceFile>', f'<SourceFile>{GHOUL_SOURCE}</SourceFile>', copy, count=1)
    copy, n2 = re.subn(r'(<OutputFile[^>]*>)[^<]*(</OutputFile>)', rf'\g<1>{GHOUL_OUTPUT}\g<2>', copy, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit('Anatomy.osp: the slider set has no SourceFile or OutputFile to point at the ghoul body')
    if f'name="{GHOUL_SET}"' in text:
        return text
    return text.replace(block, block + copy, 1)


def ghoul_groups(groups_xml):
    """the slider groups with the ghoul set beside "Anatomy Body" in every group that lists it"""
    member = f'<Member name="{SET}"/>'
    if member not in groups_xml:
        raise SystemExit('the slider groups do not list "Anatomy Body"')
    return groups_xml.replace(member, member + f'\n        <Member name="{GHOUL_SET}"/>')


def stage(osp_path, nif_path, groups_xml, work):
    """-> {published path: produced file} for the ghoul body, and the osp + groups that replace the plain ones"""
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    nif_out = ghoul_nif(nif_path, work / GHOUL_SOURCE)
    osp_out = work / 'Anatomy.osp'
    osp_out.write_text(ghoul_osp(pathlib.Path(osp_path).read_text(encoding='utf-8')), encoding='utf-8')
    grp_out = work / 'AnatomyGroups.xml'
    grp_out.write_text(ghoul_groups(groups_xml), encoding='utf-8')
    print(f'   {GHOUL_SET}: {GHOUL_SOURCE} (genitals -> {GHOUL_MAT}), output {GHOUL_OUTPUT}')
    return {NIF_REL: nif_out, 'Tools/BodySlide/SliderSets/Anatomy.osp': osp_out,
            'Tools/BodySlide/SliderGroups/Anatomy.xml': grp_out}
