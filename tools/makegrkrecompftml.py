
#!/usr/bin/python3
'''
Makes ftml tests for Greek combinations based on content of grk_compose.feax
Generates a test for each rule in the recomposition lookup
and a test if the first two glyphs match a decomposition (using the USV of the composed glyph)
Also generates tests for smcp and c2sc features on lower or upper case sequences
  see smcp.ftml, etc for glyphs not so produced (eg GrSmAlpha)

Hacky script intended for rare usage. There's no cli, so edit strings below if needed.
Assumes input data is good with no real validation.
'''

# __url__ = 'https://github.com/silnrsi/font-gentium'
__copyright__ = 'Copyright (c) 2024 SIL Global  (https://www.sil.org)'
__license__ = 'Released under the MIT License (https://opensource.org/licenses/MIT)'
__author__ = 'Alan Ward'

import re
import silfont.ufo as ufo

ufo_fn = r"../source/masters/Gentium-Regular.ufo"
feax_fn = r"../source/opentype/grk_compose.feax"
ftml_fn = r"greekrecompose.ftml"

ftml_template = '''
    <test label=\"{}\">
      <string>{}</string>
    </test>
'''[1:]
# The above template should match XML like this:
# <test label="1FB9+0308">
#   <string>\u001FB9\u000308</string>
# </test>

ftml_style_template = '''
    <test label=\"{}\" stylename=\"{}\">
      <string>{}</string>
    </test>
'''[1:]
smcp_stylename="smcp_1"
c2sc_stylename="c2sc_1"

ftml_start = '''
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet href="../tools/ftml.xsl" type="text/xsl"?>
<ftml version="1.0">
  <head>
    <fontscale>200</fontscale>
    <fontsrc label="GR">url(../results/Gentium-Regular.ttf)</fontsrc>
    <fontsrc label="GM">url(../results/Gentium-Medium.ttf)</fontsrc>
    <fontsrc label="GS">url(../results/Gentium-SemiBold.ttf)</fontsrc>
    <fontsrc label="GB">url(../results/Gentium-Bold.ttf)</fontsrc>
    <fontsrc label="GXB">url(../results/Gentium-ExtraBold.ttf)</fontsrc>
    <fontsrc label="GI">url(../results/Gentium-Italic.ttf)</fontsrc>
    <fontsrc label="GMI">url(../results/Gentium-MediumItalic.ttf)</fontsrc>
    <fontsrc label="GSI">url(../results/Gentium-SemiBoldItalic.ttf)</fontsrc>
    <fontsrc label="GBI">url(../results/Gentium-BoldItalic.ttf)</fontsrc>
    <fontsrc label="GXBI">url(../results/Gentium-ExtraBoldItalic.ttf)</fontsrc>
    <fontsrc label="GRv6">url(../references/v6200/GentiumPlus-Regular.ttf)</fontsrc>
    <fontsrc label="GIv6">url(../references/v6200/GentiumPlus-Italic.ttf)</fontsrc>
    <styles>
      <style feats="'smcp' 1" name="smcp_1"/>
      <style feats="'c2sc' 1" name="c2sc_1"/>
    </styles>
    <title>Greek combinations</title>
  </head>
  <testgroup label="Greek recomposition">
'''[1:]

ftml_smcp_special = '''
  </testgroup>
  <testgroup label="Greek small cap specials">
'''[1:]

ftml_end = '''
  </testgroup>
</ftml>
'''[1:]

# build dict to map glyph names to unicode values from UFO
name_to_unicode = {}
ufo_f = ufo.Ufont(ufo_fn)
for g_name in ufo_f.deflayer:
    ufo_g = ufo_f.deflayer[g_name]
    unicode_lst = ufo_g['unicode'] # list of USV strings
    if unicode_lst: # exclude unencoded glyphs
        usv_str = unicode_lst[0].hex # store first USV string
        name_to_unicode[g_name] = usv_str

# build data structs to generate ftml rules
feax_f = open(feax_fn, "r")
feax = feax_f.readlines()
feax_f.close()

ftml_f = open(ftml_fn, "w")
ftml_f.write(ftml_start)

# Only processes feax until the small cap lookup is reached
# Assumes two-to-one mappings are decomposition and one-to-two mappings are recomposition
compose_to_unicode = {}
for l in feax:
    field = re.split(r"\W+", l) # first field of matching lines will contain white space
    glyph_lst = []
    if field[1] == "sub" and field[3] == "by":
        # extract two-to-one mapping from base + diac to encoded precomposed base w diac
        # based on decomposition rules; used to test USV with precomposed glyph
        # for example: sub GrCapAlphaWMacron by GrCapAlpha CombMacron;
        unicode = name_to_unicode[field[2]]
        compose_to_unicode[field[4] + "-" + field[5]] = unicode
        continue
    elif field[1] == "sub" and field[3] != "by":
        # extract many-to-one substitution rules from feax
        # based on recomposition rules
        # for example: sub GrCapAlpha CombRevCommaAbv by GrCapAlphaWDasia;
        # ftml lines are immediately written below
        for s in field[2:]: # slice off leading white space and 'sub'
            if s == "by":
                break
            else:
                glyph_lst.append(s)
    elif field[1] == "grk_sc1_sub": # end loop after decomp and recomp rules processed
        break
    else:
        continue

    # write ftml lines to output file
    unicode_lst = [name_to_unicode[x] for x in glyph_lst]
    test_label = "+".join(unicode_lst) # join USVs with '+'
    test_string = "".join([f"\\u{x:0>6}" for x in unicode_lst]) # USVs with six digits and leading zeroes
    ftml_test_str = ftml_template.format(test_label, test_string)
    ftml_f.write(ftml_test_str)
    if chr(int(unicode_lst[0], 16)).islower(): # add smcp test for lower case glyphs
        ftml_test_str = ftml_style_template.format(test_label, smcp_stylename, test_string)
        ftml_f.write(ftml_test_str)
    if chr(int(unicode_lst[0], 16)).isupper(): # add c2sc test for upper case glyphs
        ftml_test_str = ftml_style_template.format(test_label, c2sc_stylename, test_string)
        ftml_f.write(ftml_test_str)
    if glyph_lst[0] + "-" + glyph_lst[1] in compose_to_unicode: # first two glyphs have a composed form
        # write line to test seqs with precomposed base w diac
        unicode_lst = [compose_to_unicode[glyph_lst[0] + "-" + glyph_lst[1]]]
        unicode_lst.extend([name_to_unicode[x] for x in glyph_lst[2:]]) # add diacs after composed form
        test_label = "+".join(unicode_lst)
        test_string = "".join([f"\\u{x:0>6}" for x in unicode_lst])
        ftml_test_str = ftml_template.format(test_label, test_string)
        ftml_f.write(ftml_test_str)
        if chr(int(unicode_lst[0], 16)).islower():
            ftml_test_str = ftml_style_template.format(test_label, smcp_stylename, test_string)
            ftml_f.write(ftml_test_str)
        if chr(int(unicode_lst[0], 16)).isupper():
            ftml_test_str = ftml_style_template.format(test_label, c2sc_stylename, test_string)
            ftml_f.write(ftml_test_str)

# add tests for certain glyphs that are not accessed through recomposition
#  derived by examinging lookup grk_sc1_sub in grk_compose.feax for non GrSm* glyphs
#  these are also tested in smcp.ftml tests
# no tests added for similar non GrCap* glyphs
ftml_f.write(ftml_smcp_special)
smcp_test_lst = ["GrDottedLunateSigma", "GrLunateSigma", "GrRevDottedLunateSigma",
                  "GrRevLunateSigma", "GrYot"]
for g in smcp_test_lst:
    u = name_to_unicode[g]
    ftml_test_str = ftml_template.format(u, f"\\u{u:0>6}")
    ftml_f.write(ftml_test_str)
    ftml_test_str = ftml_style_template.format(u, smcp_stylename, f"\\u{u:0>6}")
    ftml_f.write(ftml_test_str)

ftml_f.write(ftml_end)
ftml_f.close()
