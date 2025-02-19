from xulbux import FormatCodes
import re


class RX:
    sep: str = r"[-_.~x@\s]+(?:[0-9]+|[0-9]+$)?"
    patterns: dict[str, str] = {
        "number": r"-?[a-fA-F0-9]{4,}",
        "short_rand": r"(?:[a-zA-Z][0-9]{2}|[0-9][a-zA-Z]|[a-z]{2}|[A-Z]{2})",
        "rand{4,6}": r"(?!(?:[A-Z][a-z]{3,5}))(?:(?=.*[A-Z])(?=.*[a-z])|(?=.*[0-9])(?=.*[a-zA-Z]))[-_a-zA-Z0-9]{4,6}",
        "date": r"[12][0-9]{3}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])",
        "delimited_date": r"(?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})[-.](?:[0-9]{2}|[0-9]{4})",
        "version": r"[0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9]{1,2}){0,2}",
        "domain": r"[-a-z]+(?:\.[-a-z]+){2,}",
        "base64": r"[_+/0-9A-Za-z]{8,}={0,2}",
        "uuid": r"\{?[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}\}?",
        "sid": r"S-[0-9]+-[0-9]+(?:-[0-9]+){2,}",
    }


IGNORE_PATTERN = re.compile(rf"^(?:(?:{RX.sep})?(?:{'|'.join(RX.patterns.values())})?)+(?:[-_.~x@]+[a-zA-Z0-9]*)*$")

test_cases = {
    # SHOULD MATCH
    '-39779064': True,
    '-3f97e4e': True,
    '6e63774a': True,
    '7c22c062': True,
    'b5308ceb': True,
    'o2pkgHS50qE': True,
    'oIFY0uDheoT': True,
    '15716_62223974': True,
    '27176_468819926': True,
    '14432_1990004478': True,
    '20241128100052EF4': True,
    '202409050712125718': True,
    '35408-amQdiDa1gbeg': True,
    '35504-4AyzMv8Z08xg': True,
    'd5f2bf203372bb37_0': True,
    '9662febe7d103932_1': True,
    '11a1739cabbca8c3be33': True,
    'dd2a8225bd7697739e24': True,
    'F95BA787499AB4FA9EFFF472CE383A14': True,
    'hbasgnffgozojthzs5akkphsm0f2lbuk': True,
    '09eac60514b283f673fc96e34bdbc6c8': True,
    '1724699712889685100_8953961870769336601': True,
    '1724699922771022900_7996927162999794177': True,
    'child_lock_1731688659248623500_1950236675694990981': True,
    'language_server_stderr_1727698386477824600_428104938001459090': True,
    '170540185939602997400506234197983529371': True,
    '33fc5a94a3f99ebe7087e8fe79fbe1d37a251016': True,
    '4C7C2E87F0BC79A039D39B05F899A1CC521FDE99': True,
    'D1DF7F06B769BCCB3F4479041EC1F06E9CD3CB1A': True,
    '048b4b9befe81b96382c85907ed263ff8bbae79d792ad742181a3fa6f83e': True,
    'c6e81f130f8c1876969d3b5404212649ec056c7f49b2fc3b246bafa78ff7': True,
    'alpjnmnfbgfkmmpcfpejmmoebdndedno_1.98D784E8E77112DF1B4E935BA63D9D887E1D1663AFE53D5FB947F7345801092A': True,
    'kpfehajjjbbcifeehjgfgnabifknmdad_1.00AF3F07B5ABB71F6D30337E1EEF62FA280F06EF19485C0CF6B72171F92CCC0A': True,
    'ohckeflnhegojcjlcpbfpciadgikcohk_1.95FD9D48E4FC245A3F3A99A3A16ECD1355050BA3F4AFC555F19A97C7F9B49677': True,
    '50d04566b0e64e9409f1a053863aad5240358007b0ba6aa3064b6decbd602595f39ac5bb85bdc4fc0f58bccf71b29fc7eb69579934d98de9ef5bc715e42b': True,
    'b99e90ea8c322bf7aedc3127152875c9b3bae8badd6afadb79d229f20423e4c99f0ac5e23a77e1886d20534ffc3ff5676558339e8f757d1c4e4b824e7b83': True,
    'tJmo_JYGE+wbLDHHklSgyg==': True,
    'RQBuAHQAaQB0AGwAZQBtAGUAbgB0AA==': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8AVwBvAHIAZAA=': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8ARQB4AGMAZQBsAA==': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8ATwBuAGUATgBvAHQAZQA=': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8AUABvAHcAZQByAFAAbwBpAG4AdAA=': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8ARQB4AGMAZQBsAF8ARQB4AEUAbgB0AGkAdABsAGUAbQBlAG4AdABEAGUAdABhAGkAbABzAA==': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8ATwBuAGUATgBvAHQAZQBfAEUAeABFAG4AdABpAHQAbABlAG0AZQBuAHQARABlAHQAYQBpAGwAcwA=': True,
    'RQBYAEMAYQB0AGEAbABvAGcAVwBpAG4AMwAyAF8AUABvAHcAZQByAFAAbwBpAG4AdABfAEUAeABFAG4AdABpAHQAbABlAG0AZQBuAHQARABlAHQAYQBpAGwAcwA=': True,
    '9E583566-522F-47F6-BE0C-9E390B331291': True,
    '34003c9f-54e9-43ea-b2d6-ed396a98b4b7': True,
    'caf98285-2d28-4843-915f-64564369de4b': True,
    '16706293-5eec-4a9d-bc14-98539375887f_ADAL': True,
    '70a8005e-b05c-4253-a475-85cc2115c267.jpeg': True,
    'ffd09902-53a7-4f9b-b669-8c68968729f3.tmp.ico': True,
    '{E9CA1E27-FB80-47C7-92CB-881BA4DB4985}': True,
    '{17B244C7-C395-44AC-88ED-1F58CE22F21D}.db': True,
    '{6FF671FF-7D1A-472A-8F80-9920ED0426E7}.': True,
    'de-CH{43B63E4B-3499-43DB-A3AF-D3CAD6F9B0A9}': True,
    '{01006E22-695B-4299-B525-61B986E8E8F0}mt00546271.png': True,
    '{CBE919F5-4A7C-48A2-BDC3-4211F88326B7}mt10002117.jpeg': True,
    'S-1-12-1-4155301451-1239930137-2575335607-2413053183': True,
    '41jF': True,
    'y35u': True,
    'stFT.py': True,
    'SPt6.py': True,
    'vIzu.py': True,
    '0pzZ.md': True,
    '59UW.vue': True,
    '7NUL.vue': True,
    'gV00.toml': True,
    '000003.log': True,
    '000004.log': True,
    '934576.log': True,
    'UI_n1.0000': True,
    'L1FKS.0000': True,
    'KIF_n1.0000': True,
    'T4FK_n2.0000': True,
    'L5FKKL_n2.0000': True,
    'CFG85D4.tmp': True,
    'cheB5FF.tmp': True,
    'MSI5D5E.tmp-': True,
    'MSIAB61.tmp-': True,
    '4.8.0.20220524': True,
    '092410-111214-p30515 10': True,
    '092410-080828-p25215 00': True,
    '092380-090924-a15048 r00': True,
    '092380-090917-a15066 l01': True,
    '12-05_07-40-18_460900.log': True,
    '01-12_18-22-36_077786.log': True,
    '2024-10-17_22-59-59_021088.log': True,
    '2024-10-31_07-22-13_154004.log': True,
    '1b-4197.JPG': True,
    '29a-4180.JPG': True,
    'A001525_1.jpg': True,
    'A001642_9.jpg': True,
    'A001789_10.jpg': True,
    'A002176_11.jpg': True,
    '31819008341.ttf': True,
    '19673e1257214fff.toc': True,
    '2A2430AA21A30F9F.dat': True,
    'Apps_13376051597352960': True,
    '1380790193167760279.C4': True,
    'rc_B9NVNQPISMFG2QJD.bin': True,
    'Session_13373894090983896': True,
    'topTraffic_638004170464094982': True,
    '9o58g6e2fusvrjjjxfyosuv6g.jar': True,
    '3ojl5djkjbd9oq0ryc78s5tdt.argfile': True,
    'e_D2F7ERDTFKFHAPEFGPD7E6GEANDUHXHX.R': True,
    'bd9316bb4be37311ee3c824dd12b7e26.png': True,
    '9pe6fqebbm5r020baaa0bt5i019h43bg.jpg': True,
    'cbdm2a8ce924fu7n6f3j41622b43bn08.JPG': True,
    'SP_E7E59208AC0B433F879CC159397058DA.dat': True,
    'main_a302540edd1575ed934c3fac5dafd261.js': True,
    'ChromeExtMalware.store.32_13383402620845450': True,
    'index_7c3a20eaab153c4226389058ff87f67c.html': True,
    'b334923d66f5252ea5fb930ef5e3b481ab352382.zip': True,
    '0bd5cf23c1a78fdd98ccbf96a05645392c65305c.qmlc': True,
    'MNJGGCDMJOCBBBHAEPDHCHNCAHNBGONE_5_11_5_0.crx': True,
    '986b372398a105671e6c79dae1e20963_ocr_v0.0.1.py': True,
    'wallet-webui-560.da6c8914bf5007e1044c.chunk.js': True,
    '01c5cb21ab1d4fd56e65159d6c36cd5db1f647e1.tbres': True,
    'welcome@2x_1718fc4583db7e7c62105b5612b64050.png': True,
    'excel_96x1_e1a9a7b457251e8202ef260f24447221.png': True,
    'GuidedWalkthrough_1d39592aecc6c37bfca06e69bf40c653': True,
    'favicon-32x32_17b8c7d7b31e05ff94a88ddc1878e13d.png': True,
    'exclamationmark_aac501f800a6a84efc69ece05762b495.png': True,
    'font-awesome.min_cff276076075408b2a3fcb2054648bee.css': True,
    'gl-es-ui-strings-json_0861ab052548d03508e72c866d11b0b7.js': True,
    'hub.supsign.tech_c0f0afae5c3b4a008b4b3a44ea79c32e67cf3d08': True,
    '_PrivateProjects__4809110087a33fb9978fce72dafe850b20b54e78': True,
    'fb55ad9945e00c9b229f7aac9173de5a595a7306312ce17bf9c93f68.body': True,
    'officeaicopilot-strings.min_cf3fa8b228beccd9d754c476dbbe76e3.js': True,
    'vendors~eu-es-ui-strings-json_14eb0e0a49746832d5e52375d86520b4.js': True,
    'ASlmN2FjZGU0Yi1kNTE5LTQ5ZTctYjc4MC04MDk5ZmY0NGQ0OGZfQURBTAA.88.97.SA': True,
    'ASlmN2FjZGU0Yi1kNTE5LTQ5ZTctYjc4MC04MDk5ZmY0NGQ0OGZfQURBTAQ.1.1924.SA': True,
    '776AE126CA6F732EE80FA63284D37070132917094B3A695BAE04E9B088643DCD.json': True,
    'powerpoint-narrative-builder-strings.min_762cb36eb2cf6c3daf56dfff735f7822.js': True,
    'edgeSettings_2.0-48b11410dc937a1723bf4c5ad33ecdb286d8ec69544241bc373f753e64b396c1': True,
    # SHOULD NOT MATCH
    'main.py': False,
    'test.py': False,
    'util.js': False,
    'code.cpp': False,
    'data.json': False,
    'temp.py': False,
    'word.doc': False,
    'page.htm': False,
    'Main.java': False,
    'Home.jsx': False,
    'Page.tsx': False,
    'Test.vue': False,
    'MAIN.PY': False,
    'TEST.PY': False,
    'UTIL.JS': False,
    'CODE.CPP': False,
    'DATA.JSON': False,
    'welcome@2x.bmp': False,
    'excel_96x1.png': False,
    'edgeSettings_2.0': False,
    'AppxBlockMap.xml': False,
    'favicon-32x32.png': False,
    'gl-es-ui-strings-json.js': False,
    'vendors~eu-es-ui-strings-json.js': False,
    'list-code-extensions.exe': False,
    'get_user_data.bat': False,
    'start_main_script.sh': False,
}

if __name__ == '__main__':
    print(f"\n{IGNORE_PATTERN.pattern}\n")
    for filename, should_match in test_cases.items():
        FormatCodes.print(f"[{'br:green' if bool(IGNORE_PATTERN.match(filename)) == should_match else 'br:red'}]{filename}[_]")
