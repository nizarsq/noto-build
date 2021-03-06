# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import sys
import urllib.parse
import urllib.request
import requests
import copy
import re
import shutil
from pathlib import Path
from argparse import ArgumentParser

from defcon import Font
from fontTools import ttLib
from fontTools.subset import Subsetter
from fontTools.subset import Options
from fontTools import merge
from fontTools.ttLib.tables._n_a_m_e import makeName
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

from third_party.scalefonts import scale_font



class Download:
    def __init__(self, local_folder, repo_names, scriptsFolder, hinted=False):
        self.local_file = local_folder
        self.repoNames = repo_names
        self.notoFontsFolder = os.path.join(scriptsFolder, "NotoFonts")
        if not os.path.exists(self.notoFontsFolder):
                os.makedirs(self.notoFontsFolder)
        self.hinted = hinted
        self.editedRepoNames = copy.deepcopy(repo_names)

    def oldSha(self, repoName):
        oldShaPath = os.path.join(self.notoFontsFolder, repoName, "sha.md")
        with open(oldShaPath, "r") as text:
            _oldSha = text.read()
        return _oldSha

    def getSha(self, repoName):
        if self.hinted is False:
            folder_url = (
                "https://api.github.com/repos/notofonts/"
                + repoName
                + "/tree/master/fonts/ttf/unhinted"
            )
        else:
            folder_url = (
                "https://api.github.com/repos/notofonts/"
                + repoName
                + "/tree/master/fonts/ttf/hinted"
            )
        api_url = self.createUrl(folder_url)
        response = urllib.request.urlretrieve(api_url)
        with open(response[0], "r") as content:
            data = json.loads(content.read())
            for index, file in enumerate(data):
                if file["name"] == "instance_ttf":
                    self.sha = file["sha"]
        return self.sha
        # if response.getcode() != 404
        # elif response.getcode() == 404:
        # print("Too much Gituh Requests.")

    def writeSha(self, repoName):
        shaTxt = os.path.join(self.notoFontsFolder, repoName, "sha.md")
        with open(shaTxt, "w") as text:
            text.write(self.sha)

    def dwnldFonts(self):
        current_url = "https://api.github.com/repos/notofonts/"
        if self.local_file  is True:
            current_url = "notofonts/"
            
        for i in self.repoNames:
            if self.hinted is False:
                if self.local_file  is True: 
                    url = (
                        current_url
                        + i
                        + "/instance_ttf"
                        #"/tree/master/fonts/ttf/unhinted/instance_ttf"
                    )
                else:
                    url = (
                        current_url
                        + i
                        + "/tree/master/fonts/ttf/unhinted/instance_ttf"
                    )                    
            else:
                if self.local_file  is True: 
                    url = (
                        current_url
                        + i
                        + "/instance_ttf"
                    )
                else:
                    url = (
                        current_url
                        + i
                        + "/tree/master/fonts/ttf/hinted/instance_ttf"
                    )   
            if self.local_file  is False:
                try:
                    api_url = self.createUrl(url)
                except:
                    try:
                        askedByUser = i
                        i = i.replace("Serif", "Sans")
                        url = url.replace("Serif", "Sans")
                        _ = self.getSha(i)
                        for z in range(len(self.editedRepoNames)):
                            if self.editedRepoNames[z] == askedByUser:
                                self.editedRepoNames[z] = i
                        api_url = self.createUrl(url)
                    except:
                        print(i.replace("Sans", "Serif"), "does not exist." +
                                "Removed from writing system list"
                                )
                        self.editedRepoNames.remove(askedByUser)
                        continue
            # CHECK SHA
                dlBool = True
                if os.path.exists(os.path.join(self.notoFontsFolder, i)):
                    # print(">>> ", self.oldSha(i), self.getSha(i))
                    if self.oldSha(i) == self.getSha(i):
                        dlBool = False
                    else:
                        print("else")
                        dlBool = True
                if dlBool is True:
                    print("INFO: "+i+" download begin")
                    dest = self.getFilepathFromUrl(url, self.notoFontsFolder)
                    dest = os.path.join(os.path.dirname(dest), i, "instance_ttf")
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    response = urllib.request.urlretrieve(api_url)
                    with open(response[0], "r") as f:
                        data_brutes = f.read()
                        data = json.loads(data_brutes)
                        for index, file in enumerate(data):
                            file_url = file["download_url"]
                            file_name = file["name"]
                            temp_path = os.path.join(dest, file_url.split(
                                "/")[-1]).replace("%20", " "
                                    )
                            if file_url is not None:
                                with requests.get(file_url) as response:
                                    binary = response.content
                                    self.writeBin(temp_path, binary)
                    self.getSha(i)
                    self.writeSha(i)

    def writeBin(self, path, binary):
        with open(path, "wb") as f:
            f.write(binary)

    def createUrl(self, url):
        branch = re.findall(r"/tree/(.*?)/", url)
        api_url = url.replace("https://github.com",
                            "https://api.github.com/repos"
                            )
        if len(branch) == 0:
            branch = re.findall(r"/blob/(.*?)/", url)[0]
            api_url = re.sub(r"/blob/.*?/", "/contents/", api_url)
        else:
            branch = branch[0]
            api_url = re.sub(r"/tree/.*?/", "/contents/", api_url)

        api_url = api_url + "?ref=" + branch
        return api_url

    def getFilepathFromUrl(self, url, dirpath):
        url_path_list = urllib.parse.urlsplit(url)
        abs_filepath = url_path_list.path
        basepath = os.path.split(abs_filepath)[-1].split("-")[0]

        return os.path.join(dirpath, basepath)

    def getEditedRepoNames(self):
        return self.editedRepoNames


class GlyphsToRemove:

    def __init__(self):
        self.writingSys2glifToRemove = {}

    def addGlyphToRemove(self, unicodez: list, scriptname):
        if scriptname in self.writingSys2glifToRemove:
            previous = list(self.writingSys2glifToRemove[scriptname])
            self.writingSys2glifToRemove[scriptname] = set(unicodez + previous)
        else:
            self.writingSys2glifToRemove[scriptname] = set(unicodez)

    def getListFor(self, scriptname):
        return [x for x in writingSys2glifToRemove[scriptname]]

    def getScript(self):
        return set([i for i in self.writingSys2glifToRemove])

    def getGlyphsToRemove(self, scriptname):
        return self.getListFor(scriptname)

    def getScriptsToSubset(self):
        return self.getScript()

    def getDict(self):
        return self.writingSys2glifToRemove


class Notobuilder:
    """ docstring
    """

    def __init__(
        self,
        local,
        newName,
        output,
        writingsystems,
        contrast,
        styles,
        preset,
        swapedstyles,
        weight,
        width,
        hinted,
        ui,
        metrics,
        compatibility,
        subset,
        version
    ):
        self.scriptsFolder = os.path.split(sys.argv[0])[0]
        self.notoFontsFolder = os.path.join(self.scriptsFolder, "NotoFonts")
        self.writingSystems = writingsystems
        self.local = local
        self.newName = str(" ".join(newName))
        self.output = output  # OTF and VF merging not available
        self.preset = preset
        self.swapedstyles = swapedstyles
        self.contrast = str(contrast[0])
        self.styles = styles
        self.fonts2subset = list()
        self.weight = weight
        self.width = width
        self.default = []
        self.toKeep = dict()
        self.hinted = hinted
        self.uniGlyphsAlreadySorted = list()
        self.path = "instance_ttf"
        self.ui = ui
        self.version = version[0]
        self.duplicatesAreResolved = False
        if len(metrics) != 0:
            self.metrics = [int(i) for i in metrics]
        else:
            self.metrics = metrics
        self.compatibility = compatibility
        self.subset = subset
        # self.unhintedfontpath = "fonts/ttf/unhinted/instance_ttf"
        # self.hintedfontpath = "fonts/ttf/hinted/instance_ttf"
        self.lgcfonts = [
            "NotoSans",
            "NotoSerif",
            "NotoSans-Italic",
            "NotoSerif",
            "NotoSansDisplay",
            "NotoSerifDisplay",
            "NotoSansDisplay-Italic",
            "NotoSerifDisplay",
            "NotoSansMono",
        ]

        self.arabicFamilies = [
            "NotoNaskhArabic", "NotoNaskhArabicUI"
        ]

        self.repo_naming_translation = {
            "NotoSansKufi": "NotoKufiArabic",
            "NotoSansMusic": "NotoMusic",
            "NotoSerifMusic": "NotoMusic",
            "NotoSerifNaskh": "NotoNaskhArabic",
            "NotoSerifNaskhUI": "NotoNaskhArabicUI",
            "NotoSerifNastaliqUrdu": "NotoNastaliqUrdu",
            #"NotoSerifHebrew": "NotoRashiHebrew",
            "NotoSerifRashi": "NotoRashiHebrew",
            # "NotoSerifNushu": "NotoTraditionalNushu",
            "NotoSerifTamil-Italic": "NotoSerifTamilSlanted",
            "NotoSansTamil-Italic": "NotoSansTamil",  # Does not exists, but Serif "Italic" (slanted) does.
            "NotoSansNaskh": "NotoSansArabic",
            "NotoSerifMonoDisplay": "NotoSerifDisplay",
            "NotoSerifMono": "NotoSerif",
            "NotoSerifMono-Italic": "NotoSerif-Italic",
            "NotoSerifDisplayMono": "NotoSerifDisplay",
            "NotoSerifDisplayMono-Italic": "NotoSerifDisplay-Italic",
            "NotoSansMono-Italic": "NotoSansMono",
            "NotoSansDisplayMono-Italic": "NotoSansMono",
            "NotoSansDisplayMono": "NotoSansMono",
            "NotoSerifIndicSiyaqNumbers": "NotoSansIndicSiyaqNumbers",
            "NotoSerifTraditionalNushu": "NotoTraditionalNushu",
            "NotoSansTraditionalNushu": "NotoTraditionalNushu",
            "NotoSerifTamilSupplement": "NotoSansTamilSupplement",
            "NotoSerifKufi": "NotoKufiArabic",
            "NotoSansAhom": "NotoSerifAhom",
            "NotoSerifJavanese": "NotoSansJavanese",
            }

        self.sansOnly = ["CanadianAboriginal", "Kufi", "Music",
                        "InscriptionalPahlavi", "PsalterPahlavi",
                        "Javanese"]

        self.fonts_with_ui_version = [
            "NotoSansKannada",
            "NotoSansArabic",
            "NotoSansDevanagari",
            "NotoSansLao",
            "NotoNaskhArabic",
            # "NotoSansBengali",
            # "NotoSansGujarati",
            # "NotoSansGurmukhi",
            # "NotoSansKannada",
            # "NotoSansKhmer",
            # "NotoSansLao",
            # "NotoSansMalayalam",
            # "NotoSansMyanmar",
            # "NotoSansOriya",
            # "NotoSansSinhala",
            # "NotoSansTamil",
            # "NotoSansTelugu",
            # "NotoSansThai",
            ]


        #1. FIND THE REPO NAME
        self.buildRepoName()
        #2. DOWNLOAD FONTS AND SWITCH CONTRAST STYLE IF NEEDED
        dl = Download(self.local, self.repoNames, self.scriptsFolder, self.hinted)
        dl.dwnldFonts()
        self.repoNames = dl.getEditedRepoNames()
        #3. BUILD ALL WIDTH-WEIGHT STYLE NAME
        self.buildWghtWdthstyleName()
        #4. FOR EACH STYLE ASKED : (e.g. Bold, then CondensedBold, etc.)
        for s in self.wghtwdth_styles:
            # 4.a find the fonts thaht matches the style
            self.buildFonts2mergeList(s)
            # 4b. SUBSET LATIN / GREEK / CYRILLIC IF NEEDED
            self.lgcSub()
            #4c. SUBSET ARABIC IF NEEDED
            if "Arabic" in self.writingSystems:
                if "BasicArabic" in self.preset:
                    for ar in self.repoNames:
                        if ar in self.arabicFamilies:
                            self.arabicSub(ar)
            #4d. RESOLVE DUPLICATES IF IT'S NOT ALREADY DONE
            if self.duplicatesAreResolved is False:
                self.resolveDuplicate()
            #4e. REMOVE DUPLICATES
            self.prepFontsForMerging()
            #4f. ACTUALLY MERGE AND RENAME FONTS
            self.merging()

    @property
    def monospaced(self):
        self._monospaced = ""
        if "Mono" in self.styles:
            self._monospaced = "Mono"
        return self._monospaced

    @property
    def opticalSize(self):
        self._opticalSize = ""
        if "Display" in self.styles:
            self._opticalSize = "Display"
        return self._opticalSize

    @property
    def italic(self):
        self._slant = ""
        if "Italic" in self.styles:
            self._slant = "-Italic"
        return self._slant

    @property
    def italicName(self):
        self._ital = ""
        if "Italic" in self.styles:
            self._ital = "Italic"
        return self._ital

    @property
    def arabicStyle(self):
        self._arabicStyle = "Naskh"
        if "Kufi" in self.styles:
            self._arabicStyle = "Kufi"
        elif "Nastaliq" in self.styles:
            self._arabicStyle = "Nastaliq"
        return self._arabicStyle

    def readJson(self, jsonpath, writingsystem):
        lgcPresets = {"Latin":["BasicLatin", "ExtendedLatin", "UnicodeLatin"],
                "Greek": ["BasicGreek", "ExtendedGreek"],
                "Cyrillic":["BasicCyrillic", "ExtendedCyrillic"]}

        # if no preset is specified, take the basic set
        if len(set(self.preset) & set(lgcPresets[writingsystem])) == 0:
            self.preset.append(lgcPresets[writingsystem][0])

        for askedPreset in self.preset:
            if askedPreset in lgcPresets[writingsystem]:
                with open(jsonpath, "r") as subsetDict:
                    subset = json.load(subsetDict)
                for subName in subset:
                    if subName == askedPreset:
                        for g in subset[askedPreset]:
                            if g not in self.panEuropeanSub:
                                self.panEuropeanSub.append(g)


    def lgcSub(self):
        if len(self.swapedstyles) > 0:
            self.swaper() # fisrt apply the stylistic changes
        self.panEuropeanSub = []
        lgcSub = [s for s in self.writingSystems if s in ["Latin", "Greek", "Cyrillic"]]
        if 0 < len(lgcSub) < 3 and "Full" not in self.preset:
            europeanSubsetFolder = os.path.join(self.notoFontsFolder, "EuropeanSubset")
            if not os.path.exists(europeanSubsetFolder):
                os.makedirs(europeanSubsetFolder)
            for script in lgcSub:
                self.readJson(
                    os.path.join(self.scriptsFolder, "subsets", script.lower() + "_subsets.json"), script)
            for ftpath in self.fonts2merge_list:
                if os.path.basename(ftpath).split("-")[0] in self.lgcfonts:
                    font = self.subsetter(ttLib.TTFont(ftpath), self.panEuropeanSub)
                    newpath = os.path.join(
                        europeanSubsetFolder, os.path.basename(ftpath)
                        )
                    font.save(newpath)
                    self.fonts2merge_list = self.listReplacer(ftpath, newpath, self.fonts2merge_list)

    def arabicSub(self, repoName):
        self.arabicSub = []
        with open(os.path.join(self.scriptsFolder, "subsets", repoName+"_subsets.json"), "r") as subsetDict:
            subset = json.load(subsetDict)
            for g in subset["BasicArabic"]:
                if g not in self.arabicSub:
                    self.arabicSub.append(g)

        arabicSubsetFolder = os.path.join(self.notoFontsFolder, "ArabicSubset")
        if not os.path.exists(arabicSubsetFolder):
            os.makedirs(arabicSubsetFolder)

        for ftpath in self.fonts2merge_list:
            if os.path.basename(ftpath).split("-")[0] in self.arabicFamilies:
                font = self.arabicSubsetter(ttLib.TTFont(ftpath), self.arabicSub)
                newpath = os.path.join(
                        arabicSubsetFolder, os.path.basename(ftpath)
                        )
                font.save(newpath)
                self.fonts2merge_list = self.listReplacer(ftpath, newpath, self.fonts2merge_list)

    def buildRepoName(self):
        self.repoNames = []
        for script in self.writingSystems:
            if script in ["Latin", "Greek", "Cyrillic"]:
                name = (
                    "Noto"
                    + self.contrast
                    + self.opticalSize
                    + self.monospaced
                    + self.italic
                )
            elif script in ["Tamil"]:
                name = "Noto" + self.contrast + script + self.italic
            elif script == "Arabic":
                name = "Noto" + self.contrast + self.arabicStyle
            else:
                if self.contrast == "Serif" and script in self.sansOnly:
                    name = "Noto" + "Sans" + script
                else:
                    name = "Noto" + self.contrast + script
            if name in self.repo_naming_translation:
                name = self.repo_naming_translation[name]
            if self.ui is True and name in self.fonts_with_ui_version:
                name = name + "UI"
            if name not in self.repoNames:
                self.repoNames.append(name)
        if "ExtendedTamil" in self.preset:
            self.repoNames.append("NotoSansTamilSupplement")


    def buildWghtWdthstyleName(self):
        if self.compatibility is True:
            common = set()
            family2weightwidth = dict()
            for family in self.repoNames:
                repoPath = os.path.join(self.notoFontsFolder, family, self.path)
                weightwidth = list()
                for ft in os.listdir(repoPath):
                    weightwidth.append(ft.split("-")[1].replace(".ttf", ""))
                family2weightwidth[family] = weightwidth
            common = set(family2weightwidth[self.repoNames[0]])
            for i in family2weightwidth:
                common = common & set(family2weightwidth[i])
            self.wghtwdth_styles = list(common)
        else:
            self.wghtwdth_styles = []
            for wdth in self.width:
                for wght in self.weight:
                    if wdth == "Normal":
                        self.wghtwdth_styles.append(wght)
                    elif wght == "Regular":
                        self.wghtwdth_styles.append(wdth)
                    else:
                        self.wghtwdth_styles.append(wdth + "-" +wght)

    def buildFonts2mergeList(self, s):
        fallback = False
        localisation = 8
        typographicStyles = ["Black", "Bold", "SemiBold",
                "Medium", "Regular", "Light",
                "SemiLight", "Light", "Thin", "Regular"
                ]
        # for s in self.wghtwdth_styles:
        print("> Gather fonts to build", self.newName, s)
        self.tempStyle = s.replace("-", "")
        self.fonts2merge_list = []
        # print("> The followings fonts can be merged:")
        for n in self.repoNames:
            ftname = "-".join([n, self.tempStyle]) + ".ttf"
            if "Italic" in ftname:
                old = "-Italic-" + self.tempStyle
                new = "-" + self.tempStyle + "Italic"
                ftname = ftname.replace(
                    old, new.replace("Regular", "")
                )  # remove Reg in the Italic case)
            ftpath = os.path.join(self.notoFontsFolder, n, self.path, ftname)
            if Path(ftpath).exists():
                print("  ✓", os.path.basename(ftpath))
                self.fonts2merge_list.append(ftpath)
            else:
                if "-" in s: #width incompatibility
                    extractedWidth = s.split("-")[0]

                    fallback = False
                    if s.split("-")[1] in typographicStyles:
                        localisation = typographicStyles.index(s.split("-")[1])
                    for styl in typographicStyles[localisation:]:
                        if fallback is False:
                            if os.path.isfile(
                                os.path.join(
                                    os.path.dirname(ftpath),
                                    os.path.basename(ftpath.replace(self.tempStyle, extractedWidth+styl)),
                                )
                            ):
                                self.fonts2merge_list.append(
                                    ftpath.replace(
                                        ftpath,
                                        os.path.join(
                                            os.path.dirname(ftpath),
                                            os.path.basename(
                                                ftpath.replace(self.tempStyle, extractedWidth+styl)
                                            ),
                                        ),
                                    )
                                )
                                print(
                                    "  ✓",
                                    os.path.basename(ftpath.replace(self.tempStyle, extractedWidth+styl)),
                                    "[FALLBACK]",
                                )
                                fallback = True

                    if fallback is False:
                        if os.path.isfile(
                            os.path.join(
                                os.path.dirname(ftpath),
                                os.path.basename(ftpath.replace(extractedWidth, "")),
                            )
                        ):
                            self.fonts2merge_list.append(ftpath.replace(extractedWidth, ""))
                            print(
                                "  ✓",
                                os.path.basename(ftpath.replace(extractedWidth, "")),
                                "[FALLBACK]",
                            )
                        else:
                            fallback = False
                            if s.split("-")[1] in typographicStyles:
                                localisation = typographicStyles.index(s.split("-")[1])
                            for styl in typographicStyles[localisation:]:
                                if fallback is False:
                                    if os.path.isfile(
                                        os.path.join(
                                            os.path.dirname(ftpath),
                                            os.path.basename(ftpath.replace(self.tempStyle, styl)),
                                        )
                                    ):
                                        self.fonts2merge_list.append(
                                            ftpath.replace(
                                                ftpath,
                                                os.path.join(
                                                    os.path.dirname(ftpath),
                                                    os.path.basename(
                                                        ftpath.replace(self.tempStyle, styl)
                                                    ),
                                                ),
                                            )
                                        )
                                        print(
                                            "  ✓",
                                            os.path.basename(ftpath.replace(self.tempStyle, styl)),
                                            "[FALLBACK]",
                                        )
                                        fallback = True
                else:
                    localisation = 8
                    fallback = False
                    if s in typographicStyles:
                        localisation = typographicStyles.index(s)
                    for styl in typographicStyles[localisation:]:
                        if fallback is False:
                            if os.path.isfile(
                                os.path.join(
                                    os.path.dirname(ftpath),
                                    os.path.basename(ftpath.replace(s, styl)),
                                )
                            ):
                                self.fonts2merge_list.append(
                                    ftpath.replace(
                                        ftpath,
                                        os.path.join(
                                            os.path.dirname(ftpath),
                                            os.path.basename(
                                                ftpath.replace(s, styl)
                                            ),
                                        ),
                                    )
                                )
                                print(
                                    "  ✓",
                                    os.path.basename(ftpath.replace(s, styl)),
                                    "[FALLBACK]",
                                )
                                fallback = True

    def ft2uni(self):
        ft2unilist = dict()
        for ftpath in self.fonts2merge_list:
            f = ttLib.TTFont(ftpath)
            uni_list = list()
            cmap = f["cmap"].tables
            for table in cmap:
                if table.platformID == 3:
                    for uni, name in table.cmap.items():
                        if uni not in uni_list:
                            uni_list.append(uni)
            ft2unilist[ftpath] = uni_list
        return ft2unilist

    def resolveDuplicate(self):
        self.duplicatedToRemove = GlyphsToRemove()
        fonts2test = copy.deepcopy(self.fonts2merge_list)
        ft2unilist = self.ft2uni()
        self.script2warnSubset = dict()

        uniNaming = ["", "U+000", "U+00", "U+0", "U+"]

        while len(fonts2test) > 1:
            for i in fonts2test[1:]:
                ft2uni_temp = dict()
                ft2uni_temp[fonts2test[0]] = ft2unilist[fonts2test[0]]
                ft2uni_temp[i] = ft2unilist[i]
                identicAlreadyDone, duplicates = self.getIdentic(ft2uni_temp)
                if len(identicAlreadyDone) != 0:
                    self.duplicatedToRemove.addGlyphToRemove(
                        identicAlreadyDone, os.path.basename(i).split("-")[0]
                        )
                if len(duplicates) != 0:
                    removedUni = []
                    for d in set(duplicates+identicAlreadyDone):
                        u = str(hex(d)).upper()[2:]
                        uni = uniNaming[len(u)] + u
                        removedUni.append(uni)
                    warnSubset = "    WARN: " + " ".join(removedUni) + " are removed from " + os.path.basename(i)
                    # print(warnSubset)
                    self.script2warnSubset[os.path.basename(i).split("-")[0]] = warnSubset
                    self.duplicatedToRemove.addGlyphToRemove(
                        duplicates, os.path.basename(i).split("-")[0]
                        )
            del fonts2test[0]
        self.duplicatesAreResolved = True

    def population(self, path, script2glifToDel):
        populate = []
        uniToremove = [i for i in script2glifToDel[os.path.basename(path).split("-")[0]]]
        uni2glyphname = self.uni2glyphname(path)
        for uni in uni2glyphname:
            if uni not in uniToremove:
                populate.append(uni2glyphname[uni])
        return populate

    def prepFontsForMerging(self):
        self.destination = os.path.join(self.scriptsFolder, "Custom_Fonts")
        if not os.path.exists(self.destination):
            os.makedirs(self.destination)

        glifToRemove = self.duplicatedToRemove.getDict()

        self.actualFonts2merge = list()
        self.subsettedFonts2remove = list()
        for path in self.fonts2merge_list:
            if (
                os.path.basename(path).split("-")[0]
                in glifToRemove
                ):
                print("    INFO:", os.path.basename(path).split("-")[0], "subseted")
                if os.path.basename(path).split("-")[0] in self.script2warnSubset:
                    print(self.script2warnSubset[os.path.basename(path).split("-")[0]])
                keep = self.population(path, glifToRemove)
                font = self.subsetter(ttLib.TTFont(path), keep)
                font.save(os.path.join(self.destination, os.path.basename(path)))
                self.actualFonts2merge.append(
                    os.path.join(self.destination, os.path.basename(path))
                    )
                self.subsettedFonts2remove.append(
                    os.path.join(self.destination, os.path.basename(path))
                    )
            else:
                self.actualFonts2merge.append(path)

    def merging(self):
        print("    INFO: starts merging")
        merger = merge.Merger()

        for ftpath in self.actualFonts2merge:
            ft, upm = self.upm(ftpath)
            if upm != 1000:
                print("Scale", os.path.basename(ftpath), "at 1000 upm")
                scale_font(ft, 1000 / upm)
                ft.save(ftpath)
        self.font = merger.merge(self.actualFonts2merge)
        if len(self.metrics) > 0:
            self.font = self.updateMetrics(self.font)
        renamed = self.renamer()
        cleanedNewName = (
            self.newName.replace(" ", "")
            + "-"
            + self.tempStyle
            + self.italic.replace("-", "")
            + ".ttf"
        )
        if "ttf" in self.output:
            renamed.save(
                os.path.join(
                    self.destination, cleanedNewName.replace("RegularItalic", "Italic")
                )
            )
        if "woff2" in self.output:
            print("    save woff2 fonts")
            renamed.flavor = "woff2"
            woofName = cleanedNewName.replace(".ttf", ".woff2")
            renamed.save(
                os.path.join(
                    self.destination, woofName.replace("RegularItalic", "Italic")
                )
            )
        for suppr in self.subsettedFonts2remove:
            os.remove(suppr)
        print("    INFO: ends merging\n")
        if self.subset != "":
            customDir = os.path.join(self.scriptsFolder, "Custom_Fonts")
            for ftpath in os.listdir(customDir):
                for flavour in [".ttf", ".woff2"]:
                    if ftpath.endswith(flavour):
                        kept = str(self.subset)[2:-2]
                        font = self.customSubsetting(
                            ttLib.TTFont(os.path.join(customDir, ftpath)), kept
                        )
                        font.save(os.path.join(customDir, os.path.basename(ftpath)))

    def updateMetrics(self, ft):
        ascendent = self.metrics[0]
        descendent = self.metrics[1]

        OS_2 = ft.get("OS/2")
        OS_2.sTypoAscender = ascendent
        OS_2.sTypoDescender = descendent
        OS_2.sTypoLineGap = 0
        OS_2.usWinAscent = ascendent
        OS_2.usWinDescent = abs(descendent)

        hhea = ft.get("hhea")
        hhea.ascent = ascendent
        hhea.descent = descendent
        hhea.lineGap = 0

        return ft

    def uni2glyphname(self, ftpath):
        f = ttLib.TTFont(ftpath)
        uni2glyphname = dict()
        cmap = f["cmap"].tables
        for table in cmap:
            if table.platformID == 3:
                for uni, name in table.cmap.items():
                    if uni not in uni2glyphname:
                        uni2glyphname[uni] = name
        return uni2glyphname

    def getIdentic(self, mydict):
        values = list(mydict.values())
        identic = copy.deepcopy(set(values[0]))
        identic2add = []
        allDuplicates = []
        identicAlreadyDone = []
        for x in values[1:]:
            identic = identic & set(x)
        allDuplicates = [ad for ad in identic]
        for i in identic:
            if i not in self.uniGlyphsAlreadySorted:
                self.uniGlyphsAlreadySorted.append(i)
                identic2add.append(i)
            else:
                identicAlreadyDone.append(i)
        return identicAlreadyDone, identic2add

    def duplicate(self, head, tail):
        self.toKeep = {**self.uni2glyphname(head), **self.toKeep}
        self.toSubset = self.uni2glyphname(tail)
        duplicate = set(self.toKeep.keys()) & set(self.toSubset.keys())
        remove = []
        for i in duplicate:
            remove.append(self.toSubset[i])
        populate = []
        for i in ttLib.TTFont(tail).getGlyphOrder():
            if i not in remove:
                populate.append(i)
        return populate

    def glyphOrders(self, fontpathlist):
        ftpath2glyphorder = dict()
        for fpath in fontpathlist:
            ftpath2glyphorder[fpath] = ttLib.TTFont(fpath).getGlyphOrder()
        return ftpath2glyphorder

    def getChrs(self, duplicate):
        s = ""
        l = []
        for uni in duplicate:
            s += chr(uni) + " "
            l.append(chr(uni))
        return s

    def upm(self, ftpath):
        ft = ttLib.TTFont(ftpath)
        upm = ft["head"].unitsPerEm
        return ft, upm

    def subsetter(self, font, subset):
        """ use the noto fonts glyphsnames
            to subset fonts with premade subsettings
        """
        options = Options()
        options.layout_features = "*"  # keep all GSUB/GPOS features
        # options.no_layout_closure = True # TESTING
        options.glyph_names = False  # keep post glyph names
        options.legacy_cmap = True  # keep non-Unicode cmaps
        options.name_legacy = True  # keep non-Unicode names
        options.name_IDs = ["*"]  # keep all nameIDs
        options.name_languages = ["*"]  # keep all name languages
        options.notdef_outline = False
        options.ignore_missing_glyphs = True
        options.prune_unicode_ranges = True
        options.recommended_glyphs = True
        subsetter = Subsetter(options=options)
        subsetter.populate(glyphs=subset)
        subsetter.subset(font)

        return font

    def customSubsetting(self, font, text):
        options = Options()
        options.layout_features = "*"  # keep all GSUB/GPOS features
        options.glyph_names = False  # keep post glyph names
        options.legacy_cmap = True  # keep non-Unicode cmaps
        options.name_legacy = True  # keep non-Unicode names
        options.name_IDs = ["*"]  # keep all nameIDs
        options.name_languages = ["*"]  # keep all name languages
        options.notdef_outline = True
        options.ignore_missing_glyphs = False
        options.recommended_glyphs = True
        options.prune_unicode_ranges = True
        subsetter = Subsetter(options=options)
        subsetter.populate(text=text, unicodes=[0, 13, 32])
        subsetter.subset(font)

        return font

    def arabicSubsetter(self, font, subset):
        options = Options()
        options.layout_features = "*"  # keep all GSUB/GPOS features
        options.no_layout_closure = True
        options.glyph_names = False  # keep post glyph names
        options.legacy_cmap = True  # keep non-Unicode cmaps
        options.name_legacy = True  # keep non-Unicode names
        options.name_IDs = ["*"]  # keep all nameIDs
        options.name_languages = ["*"]  # keep all name languages
        options.notdef_outline = False
        options.ignore_missing_glyphs = False
        options.recommended_glyphs = True
        options.prune_unicode_ranges = True
        subsetter = Subsetter(options=options)
        subsetter.populate(glyphs=subset)
        subsetter.subset(font)

        return font

    def swaper(self):
        ftpathList, swaped, unicodesInt = [], [], []
        propLF = [
            "zero.lf",
            "one.lf",
            "two.lf",
            "three.lf",
            "four.lf",
            "five.lf",
            "six.lf",
            "seven.lf",
            "eight.lf",
            "nine.lf",
        ]
        propOSF = [
            "zero.osf",
            "one.osf",
            "two.osf",
            "three.osf",
            "four.osf",
            "five.osf",
            "six.osf",
            "seven.osf",
            "eight.osf",
            "nine.osf",
        ]
        tabOSF = [
            "zero.tosf",
            "one.tosf",
            "two.tosf",
            "three.tosf",
            "four.tosf",
            "five.tosf",
            "six.tosf",
            "seven.tosf",
            "eight.tosf",
            "nine.tosf",
        ]
        salt = ['I.salt', 'IJ.salt', 'Iacute.salt', 'Ibreve.salt',
                'uni01CF.salt', 'Icircumflex.salt', 'uni0208.salt',
                'Idieresis.salt', 'uni1E2E.salt', 'Idotaccent.salt',
                'uni1ECA.salt', 'Igrave.salt', 'uni1EC8.salt',
                'uni020A.salt', 'Imacron.salt', 'Iogonek.salt',
                'Itilde.salt', 'uni1E2C.salt', 'J.salt',
                'Jcircumflex.salt', 'uni01C7.salt', 'uni01CA.salt',
                'uniA7F7.salt', 'uni0406.salt', 'uni0407.salt',
                'uni0408.salt', 'uni04C0.salt', 'uni04CF.salt',
                'uni037F.salt', 'Iota.salt', 'Iotatonos.salt',
                'Iotadieresis.salt', 'uni1F38.salt', 'uni1F39.salt',
                'uni1F3A.salt', 'uni1F3B.salt', 'uni1F3C.salt',
                'uni1F3D.salt', 'uni1F3E.salt', 'uni1F3F.salt',
                'uni1FDA.salt', 'uni1FDB.salt', 'uni1FD8.salt',
                'uni1FD9.salt', 'uni1D35.salt', 'uni1D36.salt'
        ]
        unicodeIJ = [73, 306, 205, 300, 463, 206, 520, 207, 7726,
                     304, 7882, 204, 7880, 522, 298, 302, 296, 7724,
                     74, 308, 455, 458, 42999, 1030, 1031, 1032, 1216,
                     1231, 895, 921, 906, 938, 7992, 7993, 7994, 7995,
                     7996, 7997, 7998, 7999, 8154, 8155, 8152, 8153, 7477, 7478
        ]
        unicodesFig = [i for i in range(48, 58)]

        for path in self.fonts2merge_list:
            if os.path.basename(path).split("-")[0] in self.lgcfonts:
                ftpathList.append(path)

        tosfOsfLinningFonts = ["NotoSans", "NotoSans-Italic","NotoSerif",
                            "NotoSerif-Italic", "NotoSansDisplay-Italic",
                            "NotoSansDisplay", "NotoSerifDisplay", "NotoSerifDisplay-Italic"
                            ]
        altIJFonts = ["NotoSans", "NotoSans-Italic",
                    "NotoSansDisplay", "NotoSansDisplay-Italic"
                    ]

        if self.repoNames[0] in tosfOsfLinningFonts:
            if "tosf" in self.swapedstyles:
                swaped = tabOSF
            elif "osf" in self.swapedstyles:
                swaped = propOSF
            elif "plf" in self.swapedstyles:
                swaped = propLF

        if len(swaped) > 0:
            unicodesInt = unicodesFig

        if "Sans" in self.contrast:
            lgc = set(altIJFonts) & set(self.repoNames)
            if "altIJ" in self.swapedstyles and len(lgc) > 0:
                swaped = swaped + salt
                unicodesInt = unicodesInt + unicodeIJ

        for path in ftpathList:
            ft = ttLib.TTFont(path)
            cmap = ft['cmap']
            go = ft.getGlyphOrder()
            outtables = []

            for table in cmap.tables:
                modif = table.cmap
                for uni in unicodesInt:
                    if uni in modif:
                        if swaped[unicodesInt.index(uni)] in go:
                            modif[uni] = swaped[unicodesInt.index(uni)]
                newtable = CmapSubtable.newSubtable(table.format)
                newtable.platformID = table.platformID
                newtable.platEncID = table.platEncID
                newtable.language = table.language
                newtable.cmap = modif
                outtables.append(newtable)

                cmap.tables = []
                cmap.tables = outtables
                newpath = path.replace(".ttf", "_edited.ttf")

                ft.save(newpath)
                self.fonts2merge_list = self.listReplacer(path, newpath, self.fonts2merge_list)

    def listReplacer(self, old, new, list_):
        edited = copy.deepcopy(list_)
        for i in range(len(edited)):
            if edited[i]==old:
                edited[i]=new
        return edited

    def renamer(self):
        if "." in self.version:
            vMaj = self.version.split(".")[0]
            vMin = self.version.split(".")[1]
        else :
            vMaj, vMin = self.version, "000"
        isThere17 = False
        isThere16 = False
        if self.newName:
            renamedFont = self.font
            for namerecord in renamedFont["name"].names:
                namerecord.string = namerecord.toUnicode()
                if namerecord.nameID == 1:
                    name = namerecord.string
                if namerecord.nameID == 2:
                    WeightName = namerecord.string
                if namerecord.nameID == 16:
                    name = namerecord.string
                if namerecord.nameID == 17:
                    WeightName = namerecord.string
            WeightName = self.tempStyle
            for namerecord in renamedFont["name"].names:
                namerecord.string = namerecord.toUnicode()
                # Create the naming of the font Family + style if the style is non RBIBI
                if namerecord.nameID == 1:
                    if WeightName in ["Bold", "Regular", "Italic", "Bold Italic"]:
                        namerecord.string = self.newName
                    else:
                        namerecord.string = self.newName + " " + WeightName
                if namerecord.nameID == 2:
                    if self.italicName == "Italic":
                        if WeightName not in ["Bold", "Bold Italic"]:
                            namerecord.string = "Italic"
                        elif WeightName == "Bold":
                            namerecord.string = "Bold Italic"
                    elif WeightName == "Bold":
                        namerecord.string = "Bold"
                    else:
                        namerecord.string = "Regular"
                if namerecord.nameID == 3:
                    if self.italicName == "Italic":
                        if WeightName == "Regular":
                            WeightName = "Italic"
                        else:
                            WeightName = (
                                WeightName.replace("Italic", "") + " " + self.italicName
                            )
                    unicID = namerecord.string.split(";")
                    newUnicID = (
                        self.version
                        + ";"
                        + unicID[1]
                        + ";"
                        + "".join(self.newName.split(" "))
                        + "-"
                        + "".join(WeightName.split(" "))
                    )
                    namerecord.string = newUnicID
                if namerecord.nameID == 4:
                    namerecord.string = self.newName + " " + WeightName
                if namerecord.nameID == 5:
                    namerecord.string = "Version " + self.version
                if namerecord.nameID == 6:
                    namerecord.string = (
                        "".join(self.newName.split(" "))
                        + "-"
                        + "".join(WeightName.split(" "))
                    )
                if namerecord.nameID == 16:
                    namerecord.string = self.newName
                    isThere16 = True
                if namerecord.nameID == 17:
                    namerecord.string = WeightName
                    isThere17 = True

            if isThere17 is False:
                if WeightName not in ["Italic", "Regular", "Bold", "Bold Italic"]:
                    n17_p3 = makeName(WeightName, 17, 3, 1, 0x409)
                    renamedFont["name"].names.append(n17_p3)
            if isThere16 is False:
                if WeightName not in ["Italic", "Regular", "Bold", "Bold Italic"]:
                    n16_p3 = makeName(self.newName, 16, 3, 1, 0x409)
                    renamedFont["name"].names.append(n16_p3)

            renamedFont['head'].fontRevision = float(self.version)

            return renamedFont


def main():
    parser = ArgumentParser()
    parser.add_argument("--local", action="store_true")
    parser.add_argument(
        "-n", "--name", help="Rename the custom fonts as asked.", nargs=1)
    parser.add_argument(
        "-s", "--scripts", help="List of the writing systems to insert.", nargs="*")
    parser.add_argument(
        "-o", "--output", help="Generate the Custom Fonts as ttf or woff2.", nargs="*")
    parser.add_argument(
        "--contrast",
        help="Output the Custom Font in a contrasted or no contrasted style.", nargs=1,)
    parser.add_argument(
        "--styles", help="Italic, Display or Monospaced style for Latin, Greek, Cyrillic." +
        " Kufi or Nastaliq for Arabic. Italic for Tamil.", nargs="*")
    parser.add_argument("--swap", nargs="*", help="Replace the I and J shapes by the alternate ones (arg : 'altIJ');"+
        " or replace default figures (that are lining and monospaced) by : - old style figures (arg: 'osf'),"+
        " - or tabular old style figures (arg: 'tosf'); or proportional lining figures ('plf').")
    parser.add_argument("--preset", nargs="*", help ="Premade subsets.")
    parser.add_argument("--weight", nargs="*", help="Input the weight(s) you want. Default is Regular")
    parser.add_argument("--width", nargs="*", help="Input the weight(s) you want. Normal is default")
    parser.add_argument("--hinted", action="store_true", help="Use the hinted version of the fonts.")
    parser.add_argument("--ui", help="Use the UI version of the family if it exists." +
        " Tighter vertical metrics and mark positioning.", action="store_true")
    parser.add_argument("--metrics", nargs=2, help="Modify the vertical metrics.")
    parser.add_argument("--subset", nargs=1)
    parser.add_argument("--compatibility", action="store_true")
    parser.add_argument("--version", nargs=1, help="Change the version number.")
    args = parser.parse_args()

    version = "1.000"
    newName = ["MyNoto"]
    subset = ""
    preset = list()
    swapedstyles = list()
    output = ["ttf"]
    weight = ["Regular"]
    width = ["Normal"]
    styles = ""
    hinted = False
    ui = False
    metrics = []
    compatibility = False
    local = False
    
    if "--local" in sys.argv or "-l" in sys.argv:
        local = True
    if "--output" in sys.argv or "-o" in sys.argv:
        output = args.output
    if "--styles" in sys.argv:
        styles = args.styles
    if "-n" in sys.argv or "--name" in sys.argv:
        newName = args.name
    if "--swap" in sys.argv:
        swapedstyles = args.swap
    if "--preset" in sys.argv:
        preset = args.preset
    if "--weight" in sys.argv:
        weight = args.weight
    if "--width" in sys.argv:
        width = args.width
    if "--hinted" in sys.argv:
        hinted = True
    if "--ui" in sys.argv:
        ui = True
    if args.compatibility:
        compatibility = True
    if "--metrics" in sys.argv:
        metrics = args.metrics
    if "--subset" in sys.argv:
        subset = args.subset
    if "--version" in sys.argv:
        version = args.version

    build = Notobuilder(
        local,  # optional
        newName,  # optional
        output,  # only ttf (and therefor woff2) for now
        args.scripts,  # list of writing systems
        args.contrast,  # sans or serif
        styles,  # italic, kufi, display, etc…
        preset,  # pre made subset
        swapedstyles,  # swap the IJ shapes, use [tabular] old style/lining figures as default
        weight,  # list of weight. Set as Regular if not specified
        width,  # list of width. Set as Normal if not specified
        hinted,  # take unhinted fonts as default.
        ui, #use the UI version if it exists
        metrics, #modify the vertical metrics
        compatibility, #choose only common width / weights
        subset, # keep only the asked glyphs
        version # change the version number
    )

if __name__ == "__main__":
    sys.exit(main())
