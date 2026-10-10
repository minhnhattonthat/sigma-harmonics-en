"""Generate font/screens_credits.json + work/qa/credits_names.tsv from the show_*.png line boxes (run from repo root).
Needs work/qa/gfx/credits/show_ID.png for every id (`tools/scredit.py show ID ...`). Fix a name in SRC/tables, rerun."""
import collections, json
from PIL import Image, ImageFont

MOBY = 'https://www.mobygames.com/game/73451/sigma-harmonics/'
DISCOGS = 'https://www.discogs.com/release/15332931'
OST = 'https://vgmdb.net/album/9769'
R3B = 'https://raido.moe/staff/psp/psp_3rd_birthday.html'
BTVA = 'https://www.behindthevoiceactors.com/video-games/Sigma-Harmonics/'
ITA = 'https://www.mariowiki.com/List_of_Itadaki_Street_DS_staff'
HOOPS = 'https://www.mariowiki.com/List_of_Mario_Hoops_3-on-3_staff'
GLOSS = 'glossary.md'
DOC = 'user-supplied credits.docx (MobyGames credits page)'
G = 'Hepburn guess'
V, U = 'VERIFIED', 'UNVERIFIED'
SRC = {  # english -> (source, status)
    'Yoshinori Kitase': (MOBY, V), 'Hiroki Chiba': (MOBY, V), 'Yusaku Nakaaki': (MOBY, V),
    'Takatsugu Nakazawa': (MOBY, V), 'Yasuhiro Sato': (MOBY, V), 'Masahiro Ishihara': (MOBY, V),
    'Masanori Hoshino': (MOBY, V), 'Tomohiko Goto': (MOBY, V), 'Takuji Sasaki': (MOBY, V),
    'Kenichi Shida': (MOBY, V), 'Takayuki Naito': (MOBY, V), 'Makoto Ota': (MOBY + ' (Ota with macron; ASCII per glossary)', V),
    'Sho Okamura': (MOBY, V), 'Sachiko Tanabe': (MOBY, V), 'Masahiko Dairaku': (MOBY, V), 'Airi Yoshioka': (MOBY, V),
    'Toshiyuki Momose': (MOBY, V), 'Tomoko Sekii': (MOBY, V),
    'Daisuke Ono': (BTVA, V), 'Aya Hirano': (BTVA, V), 'Jun Fukuyama': ('https://en.wikipedia.org/wiki/Jun_Fukuyama', V),
    'Tetsu Inada': (BTVA, V), 'Mamiko Noto': (BTVA, V), 'Rikiya Koyama': (BTVA, V),
    'Yu Kobayashi': (BTVA + ' (Yu with macron; ASCII per glossary)', V), 'Keiji Fujiwara': (BTVA, V),
    'Kazunori Sato': (DOC, V), 'Yoshiyuki Tsuchida': (DOC, V),
    'Hideyasu Enami': ('https://www.mobygames.com/person/872738/hideyasu-enami/', V), 'Hiroyuki Oda': (DOC, V),
    'Daisuke Karasawa': ('https://mobygames.com/developer/sheet/view/developerId,484296 (alias 柄沢 大介); ' + ITA, V),
    'Naoki Kojima': (DOC, V), 'Seiya Hasegawa': (DOC, V), 'Yoshihiro Ogawa': (DOC, V),
    'Tomo Iijima': (DOC, V), 'Masayuki Jinbo': (DOC, V), 'Fumika Hasegawa': (DOC, V),
    'Masahiro Endo': (DOC, V), 'Takashi Sawada': (DOC, V),
    'Takehiro Aoto': (DOC, V), 'Yoshinori Kato': (DOC, V),
    'Fumihiko Mori': (ITA + ' (Think Garage staff)', V), 'Nobuyoshi Kamezaki': (ITA + ' (Think Garage staff)', V),
    'Yukinori Akiyama': (ITA + ' (Think Garage staff)', V),
    'Takehiko Ono': ('https://www.mobygames.com/person/317495/takehiko-ono/ (credits Sigma Harmonics event painting & motion)', V),
    'Jisaku Hamada': ('https://www.mobygames.com/person/317495/takehiko-ono/ (frequent collaborator Jisaku Hamada)', V),
    'Hiroyuki Shimazu': ('https://www.mobygames.com/person/69681/hiroyuki-shimazu/ (aka 島津 裕行)', V),
    'Todama': (DOC, V),
    'Masashi Hamauzu': (DISCOGS, V), 'Mitsuto Suzuki': (DISCOGS, V), 'Kazuhiro Hosoe': (DISCOGS, V), 'Jota Goto': (DISCOGS, V),
    'Masashi Kitagawa': (HOOPS + ' (Square Enix sound coordinator)', V),
    'Kazuki Hamamoto': (R3B, V), 'Saeko Kanazawa': (DOC, V),
    'Satoshi Akamatsu': (DISCOGS + ' (guitar on the OST)', V), 'Keiji Kawamori': (DISCOGS + ' (bass on the OST)', V),
    'Yuji Isogawa': (OST + '; ' + R3B, V), 'Hijiri Kuwano': (DISCOGS, V), 'Akira Kobayashi': (DISCOGS + ' (recording engineer)', V),
    'Fumio Takano': ('https://vgmdb.net/artist/36830', V),
    'Masaya Hojo': (R3B, V), 'Keiichiro Miyoshi': ('https://vgmdb.net/artist/40363', V),
    'Takuya Ono': (DOC + ' (Ōno with macron; ASCII per glossary)', V), 'Yuta Nakagawa': (DOC, V),
    'Yasuhiko Miyasaka': ('https://vgmdb.net/artist/31052', V), 'Tomoki Kagami': ('https://vgmdb.net/artist/29818', V),
    'Shinya Saito': (OST, V), 'Aki Hata': (OST, V),
    'Yoshiyuki Ito': ('https://vgmdb.net/album/65132', V), 'Junnosuke Sato': ('https://vgmdb.net/album/65132 (Lantis)', V),
    'Yuka Sakurai': ('https://vgmdb.net/album/65132', V), 'Tomomi Kudo': (DOC, V),
    'Hideki Imaizumi': (OST + '; ' + R3B, V), 'Makoto Esaki': (DOC, V),
    'Reiko Kondo': (R3B, V), 'Sueko Kogai': ('https://www.mobygames.com/person/189832/sueko-kogai/ (SE ratings advisor)', V),
    'Masashi Hiramatsu': (R3B, V), 'Toshirou Tsuchida': (DOC, V),
    'Akio Ohfuji': (OST + ' (raido spells Ofuji)', V), 'Advertiser Y': (DOC, V),
    'Kakuko Obinata': (R3B, V), 'Masato Kogure': ('https://finalfantasy.fandom.com/wiki/On_the_Way_to_a_Smile_-Episode:_Denzel-_Final_Fantasy_VII (thanked with Obinata/Murakami/Inoue)', V),
    'Yohei Murakami': (R3B, V), 'Noriko Inoue': (R3B, V), 'Koji Taguchi': (R3B, V),
    'Tetsuya Hiraoka': (HOOPS + ' (Square Enix debug)', V), 'Toshihiro Takemoto': (R3B, V),
    'Kazuya Okamoto': (ITA + ' (QA technical engineer)', V), 'Toshimitsu Umezawa': (ITA + ' (QA technical engineer)', V),
    'Kunihiko Matsumoto': (DOC, V), 'Akira Morishita': (DOC, V), 'Mao Fujimura': (DOC, V),
    'Akira Ebisawa': (DOC, V), 'Akira Minagawa': (DOC, V),
    'Hideyuki Kato': (R3B, V), 'Yukihiro Shibuya': (R3B, V), 'Koji Yamashita': (R3B, V),
    'Tsutomu Yamada': (ITA + ' (SE sales manager)', V), 'Koji Takada': (ITA + ' (SE sales manager)', V), 'Makoto Tsuda': (R3B, V),
    'Satoshi Kashiwazaki': (ITA + ' (SE sales manager)', V), 'Tomoyoshi Osaki': ('https://www.crunchbase.com/person/tomoyoshi-osaki (大崎智義)', V),
    'Shinji Hashimoto': (R3B, V),
    'Jiyu Oogi': (DOC, V), 'Sachiya Sakikawa': (DOC, V),
    'Isao Nakajima': (R3B, V), 'Shunji Matsutani': (R3B, V), 'Yukihiko Kono': (R3B, V),
    'Kentaro Kawai': (DOC, V), 'Daisuke Atarashi': (DOC, V),
    'Yoichi Seki': (DOC, V), 'Takashi Arai': (DOC, V),
    'Tatsuya Kando': (R3B, V), 'Ayako Hino': (R3B, V),
    'Hiroshi Harada': ('https://www.mobygames.com/game/43866/final-fantasy-xiii/credits/ps3/ (SE legal, listed with Ayako Hino)', V),
    'Saori Shibano': (DOC, V), 'Tetsuya Nomura': (R3B, V), 'Tatsuya Nonaka': (R3B, V),
    'Taketo Nozawa': (R3B, V), 'Ichiro Hazama': (R3B, V), 'Tomohiko Hirano': (R3B, V), 'Izumi Tsukushi': (R3B + '; ' + DISCOGS, V),
    'Yasuhiro Takamatsu': (R3B, V), 'Soshi Yoshida': ('https://vgmdb.net/org/112 (Soshi Yoshida / 吉田宗司)', V),
    'Akio Shiraishi': ('https://vgmdb.net/org/112 (Akio Shiraishi / 白石明生)', V),
    'Nozomi Miyazawa': ('https://vgmdb.net/org/112 (Nozomi Miyazawa / 宮澤望)', V),
    'Chizuru Abumiya': ('https://vgmdb.net/org/112 (Chizuru Abumiya / 鐙谷千鶴)', V),
    'Tetsuya Okamoto': (DOC, V), 'Shingo Niwano': (R3B, V), 'Ryuhei Ozai': (DOC, V),
    'Takako Naganuma': (R3B, V), 'Takashi Fuchigami': (DOC, V),
    'Yoichi Wada': (R3B, V), 'Keiji Honda': (R3B, V),
    # characters (glossary) and companies
    'Sigma Kurogami': (GLOSS, V), 'Neon Tsukiyumi': (GLOSS, V), 'Housui': (GLOSS + ' (ruling: 法水 = Housui)', V),
    'Dickson': ('script/ (ディクソン -> Dickson)', V), 'Christie': ('script/ (クリスティ -> Christie)', V),
    'Head of the Kurogami (Yuu)': (GLOSS, V), 'Yoshiko Kurogami': (GLOSS, V), 'Ranpo Morito': (GLOSS, V),
    'Think Garage Co., Ltd.': ('https://www.mobygames.com/company/18017/think-garage-co-ltd/', V),
    '(Platinum Egg)': ('https://www.mobygames.com/company/9430/platinum-egg-inc/', V),
    '(Elements)': (DOC, V),
    '(Crest Works)': (DOC, V),
    'Nenet Inc.': ('https://www.mobygames.com/person/317495/takehiko-ono/ (Nenet, Inc.)', V),
    "(Mixer's Lab)": (DOC, V),
    '(Tokyo Chamber Music Society)': ('https://vgmdb.net/artist/36830', V),
    'Tohokushinsha Film Corporation': ('https://vgmdb.net/artist/40363', V),
    'Hitokuchi-zaka Studios': ('https://vgmdb.net/artist/31052 (HITOKUCHI-ZAKA STUDIOS); same as on-screen English', V),
    '(Space Craft Entertainment)': ('https://vgmdb.net/album/64448', V), 'Space Craft Entertainment': ('https://vgmdb.net/album/64448', V),
    'Aoni Production': ('https://www.mariowiki.com/List_of_Mario_Sports_Mix_staff (AONI PRODUCTION)', V),
    'Office Osawa': ('https://video-game-audio.fandom.com/wiki/Office_Osawa', V),
    'Haiyuza Theater Company': ('https://seiyuwiki.fandom.com/wiki/Category:Voice_actors_by_agency', V),
    'Holy Peak': ('https://video-game-audio.fandom.com/wiki/Holy_Peak', V),
    'Production Baobab': ('https://en.wikipedia.org/wiki/Production_Baobab', V),
    'Mausu Promotion': ('https://en.wikipedia.org/wiki/Kenji_Hamada (affiliated with Mausu Promotion)', V),
    '(Dentsu)': (DOC, V),
    'Root Co. Ltd.': (DOC, V),
}

N, L, A, H, S = 'name', 'label', 'affil', 'head', 'list'
CAST = {'Sigma Kurogami': '黒上シグマ', 'Neon Tsukiyumi': '月弓ネオン', 'Housui': '法水', 'Dickson': 'ディクソン',
        'Christie': 'クリスティ', 'Head of the Kurogami (Yuu)': '黒上頭首（ゆう）', 'Yoshiko Kurogami': '黒上 佳子',
        'Ranpo Morito': '守人 乱歩'}
# id: [(line index, english, kind, role, japanese)]
c = lambda i, lab, name, jl, jn, role='VOICE ACTORS': [(i, lab, L, role + ' (character)', jl), (i + 1, name, N, role + ' / ' + lab, jn)]
SPEC = {
    '00191': [(1, 'Yoshinori Kitase', N, 'PRODUCER', '北瀬 佳範')],
    '00194': [(1, 'Hiroki Chiba', N, 'DIRECTOR', '千葉 広樹')],
    '00197': [(2, 'Yusaku Nakaaki', N, 'CHARACTER DESIGNER & ART DIRECTOR', '仲秋 勇作')],
    '00200': [(2, 'Hiroki Chiba', N, 'SCENARIO & EVENT PLANNING DIRECTOR', '千葉 広樹'),
              (5, 'Takatsugu Nakazawa', N, 'BATTLE PLANNING DIRECTOR', '中澤 孝継')],
    '00203': [(1, 'Yasuhiro Sato', N, 'BATTLE PLANNER', '佐藤 泰弘'), (3, 'Masahiro Ishihara', N, 'EVENT PLANNER', '石原 誠弘'),
              (5, 'Masanori Hoshino', N, 'MAP PLANNER', '星野 雅紀')],
    '00206': [(2, 'Tomohiko Goto', N, 'CHARACTER MODELING DIRECTOR', '後藤 智彦'),
              (5, 'Takuji Sasaki', N, 'CHARACTER TEXTURE DIRECTOR', '佐々木 拓史')],
    '00209': [(1, 'Kenichi Shida', N, 'MOTION DIRECTOR', '志田 健一'), (3, 'Takayuki Naito', N, 'MOTION DESIGNER', '内藤 貴之'),
              (5, 'Makoto Ota', N, 'VFX DIRECTOR', '太田 真')],
    '00212': [(2, 'Sho Okamura', N, 'MENU & BG MODELING DIRECTOR', '岡村 礁'), (4, 'Sachiko Tanabe', N, 'MONSTER & BG DESIGNER', '田邉 幸子')],
    '00215': [(1, 'Masahiko Dairaku', N, 'BG & EVENT ART DESIGNER', '大楽 昌彦'), (3, 'Airi Yoshioka', N, 'BG ART DESIGNER', '吉岡 愛理')],
    '00218': [(2, 'Toshiyuki Momose', N, 'EVENT CHARACTER SUPERVISOR', '百瀬 季之'), (4, 'Tomoko Sekii', N, 'PROJECT MANAGER', '関井 朋子')],
    '00221': c(2, 'Sigma Kurogami', 'Daisuke Ono', CAST['Sigma Kurogami'], '小野 大輔') + c(4, 'Neon Tsukiyumi', 'Aya Hirano', CAST['Neon Tsukiyumi'], '平野 綾'),
    '00224': c(2, 'Sigma Kurogami', 'Daisuke Ono', CAST['Sigma Kurogami'], '小野 大輔'),
    '00227': c(2, 'Sigma Kurogami', 'Daisuke Ono', CAST['Sigma Kurogami'], '小野 大輔') + c(4, 'Neon Tsukiyumi', 'Aya Hirano', CAST['Neon Tsukiyumi'], '平野 綾'),
    '00230': c(0, 'Housui', 'Jun Fukuyama', '法水', '福山 潤') + c(2, 'Dickson', 'Tetsu Inada', 'ディクソン', '稲田 徹') + c(4, 'Christie', 'Mamiko Noto', 'クリスティ', '能登 麻美子'),
    '00233': c(0, 'Housui', 'Jun Fukuyama', '法水', '福山 潤') + c(2, 'Dickson', 'Tetsu Inada', 'ディクソン', '稲田 徹') + c(4, 'Christie', 'Mamiko Noto', 'クリスティ', '能登 麻美子'),
    '00236': c(0, 'Housui', 'Jun Fukuyama', '法水', '福山 潤') + c(2, 'Dickson', 'Tetsu Inada', 'ディクソン', '稲田 徹'),
    '00239': c(0, 'Dickson', 'Tetsu Inada', 'ディクソン', '稲田 徹') + c(2, 'Christie', 'Mamiko Noto', 'クリスティ', '能登 麻美子'),
    '00242': c(0, 'Head of the Kurogami (Yuu)', 'Rikiya Koyama', CAST['Head of the Kurogami (Yuu)'], '小山 力也') + c(2, 'Yoshiko Kurogami', 'Yu Kobayashi', '黒上 佳子', '小林 ゆう') + c(4, 'Ranpo Morito', 'Keiji Fujiwara', '守人 乱歩', '藤原 啓治'),
    '00245': c(0, 'Head of the Kurogami (Yuu)', 'Rikiya Koyama', CAST['Head of the Kurogami (Yuu)'], '小山 力也'),
    '00248': c(0, 'Head of the Kurogami (Yuu)', 'Rikiya Koyama', CAST['Head of the Kurogami (Yuu)'], '小山 力也') + c(2, 'Yoshiko Kurogami', 'Yu Kobayashi', '黒上 佳子', '小林 ゆう'),
    '00251': c(0, 'Yoshiko Kurogami', 'Yu Kobayashi', '黒上 佳子', '小林 ゆう') + c(2, 'Ranpo Morito', 'Keiji Fujiwara', '守人 乱歩', '藤原 啓治'),
    '00254': [(0, 'Think Garage Co., Ltd.', H, '(company heading)', '有限会社シンクガレージ'), (4, 'Kazunori Sato', N, 'MAIN PROGRAMMER', '佐藤 一宣')],
    '00257': [(1, 'Yoshiyuki Tsuchida', N, 'PROGRAMMERS', '土田 由之'), (2, 'Hideyasu Enami', N, 'PROGRAMMERS', '榎並 英康'),
              (3, 'Hiroyuki Oda', N, 'PROGRAMMERS', '小田 裕之'), (4, '(Platinum Egg)', A, 'PROGRAMMERS (affiliation)', '(プラチナエッグ)')],
    '00260': [(1, 'Daisuke Karasawa', N, 'DESIGN DIRECTOR', '柄沢 大介'), (3, 'Naoki Kojima', N, 'BG MODELING DESIGNERS', '小島 直樹'),
              (4, '(Elements)', A, 'BG MODELING DESIGNERS (affiliation)', '(エレメンツ)'), (5, 'Seiya Hasegawa', N, 'BG MODELING DESIGNERS', '長谷川 誠也'),
              (6, '(Crest Works)', A, 'BG MODELING DESIGNERS (affiliation)', '(クレスト・ワークス)')],
    '00263': [(1, 'Yoshihiro Ogawa', N, 'VFX & 2D DESIGNER', '小川 佳宏'), (2, '(Elements)', A, 'VFX & 2D DESIGNER (affiliation)', '(エレメンツ)'),
              (5, 'Tomo Iijima', N, 'CHARACTER MOTION DESIGNERS', '飯島 智'), (6, '(Crest Works)', A, 'CHARACTER MOTION DESIGNERS (affiliation)', '(クレスト・ワークス)'),
              (7, 'Masayuki Jinbo', N, 'CHARACTER MOTION DESIGNERS', '新保 昌弘'), (8, '(Crest Works)', A, 'CHARACTER MOTION DESIGNERS (affiliation)', '(クレスト・ワークス)'),
              (9, 'Fumika Hasegawa', N, 'CHARACTER MOTION DESIGNERS', '長谷川 史佳'), (10, '(Crest Works)', A, 'CHARACTER MOTION DESIGNERS (affiliation)', '(クレスト・ワークス)')],
    '00266': [(2, 'Masahiro Endo', N, 'CHARACTER MODELING DESIGNERS', '遠藤 真宏'),
              (4, 'Seiya Hasegawa', N, 'CHARACTER MODELING DESIGNERS', '長谷川 誠也'), (5, '(Crest Works)', A, 'CHARACTER MODELING DESIGNERS (affiliation)', '(クレスト・ワークス)'),
              (6, 'Takashi Sawada', N, 'CHARACTER MODELING DESIGNERS', '澤田 尊志'), (7, '(Crest Works)', A, 'CHARACTER MODELING DESIGNERS (affiliation)', '(クレスト・ワークス)'),
              (8, 'Takehiro Aoto', N, 'CHARACTER MODELING DESIGNERS', '青砥 岳大'), (9, '(Crest Works)', A, 'CHARACTER MODELING DESIGNERS (affiliation)', '(クレスト・ワークス)')],
    '00269': [(0, 'Yoshinori Kato', N, 'CHARACTER MODELING DESIGNERS', '加藤 善教'), (1, '(Crest Works)', A, 'CHARACTER MODELING DESIGNERS (affiliation)', '(クレスト・ワークス)'),
              (2, 'Yoshihiro Ogawa', N, 'CHARACTER MODELING DESIGNERS', '小川 佳宏'), (3, '(Elements)', A, 'CHARACTER MODELING DESIGNERS (affiliation)', '(エレメンツ)'),
              (5, 'Fumihiko Mori', N, 'SPECIAL THANKS', '森 文彦'), (6, 'Nobuyoshi Kamezaki', N, 'SPECIAL THANKS', '亀崎 信義'),
              (7, 'Yukinori Akiyama', N, 'SPECIAL THANKS', '秋山 幸範')],
    '00272': [(2, 'Nenet Inc.', H, 'EVENT CHARACTER PAINTING & MOTION DESIGNERS (company)', '株式会社 ネネット'),
              (3, 'Takehiko Ono', N, 'EVENT CHARACTER PAINTING & MOTION DESIGNERS', '小野 雄彦'),
              (4, 'Jisaku Hamada', N, 'EVENT CHARACTER PAINTING & MOTION DESIGNERS', '濱田 治策'),
              (7, 'Hiroyuki Shimazu', N, 'EVENT CHARACTER DESIGNERS', '島津 裕行'), (8, 'Todama', N, 'EVENT CHARACTER DESIGNERS', 'とだま')],
    '00275': [(2, 'Masashi Hamauzu', N, 'COMPOSER & ARRANGER', '浜渦 正志'), (4, 'Mitsuto Suzuki', N, 'ARRANGER & MIXER', '鈴木 光人')],
    '00278': [(1, 'Kazuhiro Hosoe', N, 'SOUND DESIGNER', '細江 一博'), (3, 'Jota Goto', N, 'SOUND & DIALOGUE EDITOR', '後藤 譲太'),
              (5, 'Masashi Kitagawa', N, 'PROJECT COORDINATOR', '北川 雅')],
    '00281': [(1, 'Kazuki Hamamoto', N, 'PROJECT ASSISTANTS', '濱本 一希'), (2, 'Saeko Kanazawa', N, 'PROJECT ASSISTANTS', '金澤 佐衣子'),
              (4, 'Satoshi Akamatsu', N, 'SPECIAL THANKS', '赤松 智'), (5, 'Keiji Kawamori', N, 'SPECIAL THANKS', '河盛 慶次'),
              (6, 'Yuji Isogawa', N, 'SPECIAL THANKS', '五十川 祐次')],
    '00284': [(1, 'Hijiri Kuwano', N, 'VIOLINIST', '桑野 聖'), (3, 'Akira Kobayashi', N, 'RECORDING ENGINEER', '小林 彰'),
              (4, "(Mixer's Lab)", A, 'RECORDING ENGINEER (affiliation)', '(ミキサーズ・ラボ)'),
              (6, 'Fumio Takano', N, 'RECORDING COORDINATOR', '高野 文男'),
              (7, '(Tokyo Chamber Music Society)', A, 'RECORDING COORDINATOR (affiliation)', '(東京室内楽協会)')],
    '00287': [(1, 'Tohokushinsha Film Corporation', H, 'VOICE RECORDING (company)', '株式会社 東北新社'),
              (4, 'Masaya Hojo', N, 'VOICE RECORDING MANAGER', '北條 雅也'), (6, 'Keiichiro Miyoshi', N, 'VOICE DIRECTOR', '三好 慶一郎'),
              (9, 'Takuya Ono', N, 'VOICE RECORDING COORDINATORS', '大野 拓也'), (10, 'Yuta Nakagawa', N, 'VOICE RECORDING COORDINATORS', '中川 裕太')],
    '00290': [(0, 'Hitokuchi-zaka Studios', H, '(company heading)', '株式会社 一口坂スタジオ'),
              (3, 'Yasuhiko Miyasaka', N, 'VOICE RECORDING ENGINEERS', '宮坂 保彦'), (4, 'Tomoki Kagami', N, 'VOICE RECORDING ENGINEERS', '加賀美 喬貴')],
    '00293': [(1, 'Aya Hirano', N, 'THEME SONG', '平野 綾')],
    '00296': [(2, 'Aya Hirano', N, 'VOCALIST', '平野 綾'), (4, 'Shinya Saito', N, 'COMPOSER & ARRANGER', '齋藤 真也'), (6, 'Aki Hata', N, 'LYRICIST', '畑 亜貴')],
    '00299': [(1, 'Yoshiyuki Ito', N, 'PRODUCER', '伊藤 善之'), (3, 'Junnosuke Sato', N, 'DIRECTOR', '佐藤 純之介'),
              (6, 'Yuka Sakurai', N, 'A & R', '櫻井 優香'), (9, 'Tomomi Kudo', N, 'ARTIST MANAGER', '工藤 智美'),
              (10, '(Space Craft Entertainment)', A, 'ARTIST MANAGER (affiliation)', '(スペースクラフト・エンタテインメント)')],
    '00302': [(1, 'Aoni Production', H, 'ACTOR MANAGEMENT', '青二プロダクション'), (3, 'Office Osawa', H, 'ACTOR MANAGEMENT', '大沢事務所'),
              (4, 'Space Craft Entertainment', H, 'ACTOR MANAGEMENT', 'スペースクラフト・エンタテインメント'),
              (5, 'Haiyuza Theater Company', H, 'ACTOR MANAGEMENT', '劇団俳優座'), (6, 'Holy Peak', H, 'ACTOR MANAGEMENT', 'ホーリーピーク'),
              (7, 'Production Baobab', H, 'ACTOR MANAGEMENT', 'ぷろだくしょんバオバブ'), (8, 'Mausu Promotion', H, 'ACTOR MANAGEMENT', 'マウスプロモーション')],
    '00305': [(2, 'Hideki Imaizumi', N, 'ASSOCIATE PRODUCER', '今泉 英樹'), (4, 'Makoto Esaki', N, 'PROJECT ASSISTANT', '江嵜 誠')],
    '00308': [(1, 'Reiko Kondo', N, 'RATING ADVISORS', '近藤 玲子'), (2, 'Sueko Kogai', N, 'RATING ADVISORS', '小貝 壽恵子'),
              (4, 'Masashi Hiramatsu', N, 'RATING SECTION MANAGER', '平松 正嗣'), (6, 'Toshirou Tsuchida', N, 'GENERAL MANAGER', '土田 俊郎')],
    '00311': [(2, 'Akio Ohfuji', N, 'PUBLICITY PRODUCER', '大藤 昭夫'), (5, 'Advertiser Y', N, 'PUBLICITY ASSISTANT PRODUCER', '宣伝担当 Y')],
    '00314': [(1, 'Kakuko Obinata', N, 'PUBLICITY STAFF', '大日方 可功子'), (2, 'Masato Kogure', N, 'PUBLICITY STAFF', '木暮 昌人'),
              (3, 'Yohei Murakami', N, 'PUBLICITY STAFF', '村上 洋平'), (4, 'Noriko Inoue', N, 'PUBLICITY STAFF', '井上 紀子'),
              (6, 'Koji Taguchi', N, 'GENERAL PRODUCER', '田口 浩司')],
    '00317': [(2, 'Tetsuya Hiraoka', N, 'COORDINATOR', '平岡 徹也'), (4, 'Toshihiro Takemoto', N, 'PLANNER', '竹本 敏裕'),
              (6, 'Kazuya Okamoto', N, 'TECHNICAL ENGINEERS', '岡本 一彌'), (7, 'Toshimitsu Umezawa', N, 'TECHNICAL ENGINEERS', '梅澤 俊充')],
    '00320': [(1, 'Kunihiko Matsumoto', N, 'SENIOR TESTERS', '松本 邦彦'), (2, 'Akira Morishita', N, 'SENIOR TESTERS', '森下 晃'),
              (4, 'Mao Fujimura', N, 'TESTERS', '藤村 麻央'), (5, 'Akira Ebisawa', N, 'TESTERS', '海老澤 瑛'), (6, 'Akira Minagawa', N, 'TESTERS', '皆川 明')],
    '00323': [(1, 'Hideyuki Kato', N, 'MANAGER', '加藤 英之'), (3, 'Yukihiro Shibuya', N, 'SENIOR MANAGER', '渋谷 幸弘'),
              (5, 'Koji Yamashita', N, 'GENERAL MANAGER', '山下 弘二')],
    '00326': [(2, 'Tsutomu Yamada', N, 'MANAGERS', '山田 勉'), (3, 'Koji Takada', N, 'MANAGERS', '高田 浩二'), (4, 'Makoto Tsuda', N, 'MANAGERS', '津田 真')],
    '00329': [(1, 'Satoshi Kashiwazaki', N, 'SENIOR MANAGER', '柏崎 聡'), (3, 'Tomoyoshi Osaki', N, 'GENERAL MANAGER', '大崎 智義'),
              (7, 'Shinji Hashimoto', N, 'CORPORATE EXECUTIVE', '橋本 真司')],
    '00332': [(1, 'Jiyu Oogi', S, 'SPECIAL THANKS', '黄樹 弐悠'), (3, 'Sachiya Sakikawa', S, 'SPECIAL THANKS', '先川 幸矢'),
              (5, 'Isao Nakajima', S, 'SPECIAL THANKS', '中島 功'), (7, 'Shunji Matsutani', S, 'SPECIAL THANKS', '松谷 春司'),
              (9, 'Yukihiko Kono', S, 'SPECIAL THANKS', '河野 幸彦'), (11, 'Kentaro Kawai', S, 'SPECIAL THANKS', '河合 謙太郎'),
              (12, '(Dentsu)', A, 'SPECIAL THANKS (affiliation)', '(電通)'), (13, 'Daisuke Atarashi', S, 'SPECIAL THANKS', '新 大輔'),
              (14, '(Dentsu)', A, 'SPECIAL THANKS (affiliation)', '(電通)'), (15, 'Root Co. Ltd.', S, 'SPECIAL THANKS', '株式会社ルート')],
    '00335': [(i, e, S, 'SPECIAL THANKS', j) for i, (e, j) in enumerate([
        ('Yoichi Seki', '関 洋一'), ('Takashi Arai', '新井 隆'), ('Tatsuya Kando', '神藤 辰也'), ('Ayako Hino', '日野 綾子'),
        ('Hiroshi Harada', '原田 弘'), ('Saori Shibano', '柴野 さお里'), ('Tetsuya Nomura', '野村 哲也'), ('Tatsuya Nonaka', '能仲 達也')])],
    '00338': [(i, e, S, 'SPECIAL THANKS', j) for i, (e, j) in enumerate([
        ('Taketo Nozawa', '野澤 武人'), ('Ichiro Hazama', '間 一朗'), (None, None), ('Tomohiko Hirano', '平野 智彦'),
        ('Izumi Tsukushi', '筑紫 泉'), ('Yasuhiro Takamatsu', '高松 康弘'), ('Soshi Yoshida', '吉田 宗司'), ('Akio Shiraishi', '白石 明生')]) if e],
    '00341': [(i, e, S, 'SPECIAL THANKS', j) for i, (e, j) in enumerate([
        ('Nozomi Miyazawa', '宮澤 望'), ('Chizuru Abumiya', '鐙谷 千鶴'), ('Tetsuya Okamoto', '岡本 哲也'), ('Shingo Niwano', '庭野 慎吾'),
        ('Ryuhei Ozai', '小材 龍平'), ('Takako Naganuma', '長沼 貴子'), ('Takashi Fuchigami', '渕上 貴史')])],
    '00344': [(1, 'Yoichi Wada', N, 'PRODUCTION EXECUTIVES', '和田 洋一'), (2, 'Keiji Honda', N, 'PRODUCTION EXECUTIVES', '本多 圭司')],
}
STIX = 'font/STIXGeneral.ttf'
SIZE = {N: 18, L: 13, A: 11, H: 15, S: 15}
WHITE, GREY = [255, 255, 255], [189, 180, 180]


def lines(i):
    im = Image.open(f'work/qa/gfx/credits/show_{i}.png').convert('RGB')
    im = im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    W, Hh = im.size
    px = im.load()
    lit = lambda p: max(p) > 60
    rows = [any(lit(px[x, y]) for x in range(W)) for y in range(Hh)]
    out, y = [], 0
    while y < Hh:
        if rows[y]:
            y0 = y
            while y < Hh and rows[y]:
                y += 1
            pts = [(x, yy) for x in range(W) for yy in range(y0, y) if lit(px[x, yy])]
            xs = [p[0] for p in pts]
            bright = collections.Counter(px[p] for p in pts if max(px[p]) >= 100)
            out.append((min(xs), y0, max(xs), y - 1, list(max((c for c, _ in bright.most_common(3)), key=sum))))
        y += 1
    return out, W


def width(text, size):
    f = ImageFont.truetype(STIX, size)
    l, _, r, _ = f.getbbox(text)
    return r - l


recipes, rows = {}, []
for i, items in SPEC.items():
    ls, W = lines(i)
    wipe, text = [], []
    for k, en, kind, role, jp in items:
        x0, y0, x1, y1, col = ls[k]
        panel = x0 // 192 * 192  # wide scroll strips: each item sits in its own 192-wide panel
        wipe.append([panel, y0 - 1, panel + 192, y1 + 2])  # full width: black stays the row's most common dark colour
        size = SIZE[kind]
        if kind == L:
            box, fill, al = [x0, y0 - 3, panel + 187, y1 + 3], GREY, 'left'
        elif kind == A:
            w = min(width(en, size), x1 - panel - 4)
            box, fill, al = [x1 - w - 1, y0 - 2, x1 + 1, y1 + 2], col, 'center'
        else:
            cx = (x0 + x1) // 2
            half = min(cx - panel - 4, panel + 188 - cx)
            pad = 1 if kind == S else 3
            box, fill, al = [cx - half, y0 - pad, cx + half, y1 + pad], WHITE, 'center'
        t = {'text': en, 'box': box, 'size': size, 'font': 'STIXGeneral.ttf', 'fill': fill}
        if al != 'center':
            t['align'] = al
        text.append(t)
        src, st = SRC[en]
        rows.append([i, role, jp, en, src, st])
    recipes[i] = {'wipe': wipe, 'text': text}

with open('font/screens_credits.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(recipes, ensure_ascii=False, indent=1) + '\n')
with open('work/qa/credits_names.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('id\trole\tjapanese\tenglish\tsource\tstatus\n')
    for r in rows:
        f.write('\t'.join(r) + '\n')
uniq = {(r[2], r[3]): r[5] for r in rows}
print(len(recipes), 'ids;', len(rows), 'rows;', sum(v == U for v in uniq.values()), 'unique UNVERIFIED')
