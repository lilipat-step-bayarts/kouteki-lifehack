#!/usr/bin/env python3
"""
公的情報・生活ハック記事の自動生成・蓄積スクリプト
【AdSense審査対策・完全重複排除エンジン搭載】
・過去に公開された全記事のタイトル・IDをチェックし、同一内容・同一タイトルの再生成を100%禁止
・厚労省、国税庁、こども家庭庁、経産省等の実在する公的制度データベースから未執筆テーマのみを追加
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
JSON_PATH = os.path.join(ARTICLES_DIR, "articles.json")

JST = timezone(timedelta(hours=9))
TODAY_STR = datetime.now(JST).strftime("%Y-%m-%d")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()


# 未執筆の公的制度・給付金・税制テーマプール（順次解放・重複絶対禁止）
STORE1_TOPIC_POOL = [
    {
        "id": "kaigo-kyuugyou-kyuufukin-2026",
        "category": "介護支援・休業給付金",
        "title": "【親の介護で離職するな】国から給料の67%が最大93日分支給される『介護休業給付金』と会社を辞めずに親を救う合法的ロードマップ",
        "summary": "親が突然倒れたり要介護になったとき、絶対にやってはいけないのが「会社を辞めて自分で介護すること」です。国から給料の67%が非課税・社保免除で最大93日分支給される『介護休業給付金』を使い、自分が介護するのではなく「プロの介護体制を整える」ための合法的申請手順を整理します。",
        "target_audience": [
            "親や配偶者、祖父母が要介護状態（要介護2以上目安）になり仕事を休む必要がある方",
            "雇用保険に加入しており、過去2年間に12ヶ月以上の被保険者期間がある方",
            "介護のために仕事を辞めようか悩んでいる会社員・公務員・パート"
        ],
        "benefit_amount": "休業前賃金の67%（非課税・社保免除で実質手取り約80%）。家族1人につき通算93日まで最大3回分割受給可能",
        "table_headers": ["休業前月収（額面）", "月額給付額（非課税）", "実質手取りカバー率", "93日間（約3ヶ月）支給総額"],
        "table_rows": [
            ["月収 25万円", "約 16.7万円", "通常手取りの約80%", "約 50.1万円"],
            ["月収 35万円", "約 23.4万円", "通常手取りの約80%", "約 70.2万円"],
            ["月収 45万円", "約 30.1万円", "通常手取りの約80%", "約 90.3万円"]
        ],
        "steps": [
            {"step": "Step 1", "title": "親の主治医や地域包括支援センターに相談し要介護認定を申請", "desc": "ケアマネジャーを選定し、デイサービスやショートステイ等のケアプラン策定を開始します。"},
            {"step": "Step 2", "title": "会社の人事・総務へ休業開始の2週間前までに『介護休業申出書』を提出", "desc": "体制を組むための期間として最大3回に分割して取得できます。"},
            {"step": "Step 3", "title": "ハローワークへ申請書類を提出し、指定口座へ非課税振込", "desc": "雇用保険から直接非課税で振り込まれ、社会保険料も免除されます。"}
        ],
        "faq": [
            {"q": "93日間をまとめて使わないといけませんか？", "a": "対象家族1人につき通算93日を最大3回まで分割して取得できます。"},
            {"q": "休業中に少しだけ出勤した場合は？", "a": "1ヶ月の就業日数が10日以下（または80時間以下）なら全額受給可能です。"}
        ],
        "hoporin_tip": "介護休業は『自分で介護するための休み』ではなく『仕事と介護を両立するプロの体制を組むための期間』です！絶対に離職せず給付金を活用してくださいね🐧！",
        "source_name": "厚生労働省「介護休業給付について」",
        "source_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000158665.html",
        "date": "2026-11-23"
    },
    {
        "id": "kougaku-kaigo-gassan-2026",
        "category": "医療・介護費還付",
        "title": "【年間最大数十万円の還付】医療と介護の両方を払っている世帯は必見！『高額医療・高額介護合算制度』の申請漏れを防ぐ全手順",
        "summary": "1年間に支払った医療保険と介護保険の自己負担額を合算し、自己負担限度額を超えた分が口座に現金で戻ってくる公的制度。役所から自動通知が来ない自治体も多いため、世帯合算の要件と申請方法を解説します。",
        "target_audience": [
            "同じ世帯内に医療費と介護サービス費用の両方を支払っている家族がいる世帯",
            "親のデイサービスやショートステイ代、通院治療費の負担が重い現役世代",
            "自己負担割合が1割〜3割で年間合算額が56万円（所得区分による）を超える世帯"
        ],
        "benefit_amount": "所得区分に応じて年間合算限度額（年34万〜212万円等）を超えた額を全額現金還付（平均数万円〜数十万円）",
        "table_headers": ["所得区分（70歳以上例）", "医療＋介護 年間自己負担限度額", "申請窓口", "必要書類"],
        "table_rows": [
            ["現役並み所得者（年収約770万〜）", "年141万円（世帯合算）", "加入する健康保険組合 / 国保窓口", "支給申請書兼自己負担額証明書"],
            ["一般世帯（年収約370万〜770万）", "年56万円（世帯合算）", "市区町村の後期高齢者医療・国保窓口", "領収書・マイナンバー・振込口座"],
            ["低所得世帯（住民税非課税世帯）", "年31万円（世帯合算）", "市区町村の介護保険窓口", "介護保険自己負担額証明書"],
            ["低所得世帯（年金収入80万円以下）", "年19万円（世帯合算）", "市区町村の福祉・国保担当課", "年金振込通知書等の所得証明"]
        ],
        "steps": [
            {"step": "Step 1", "title": "毎年7月31日時点の医療保険窓口に『介護保険自己負担額証明書』を提出", "desc": "計算期間は毎年8月1日〜翌年7月31日の1年間。介護保険側で証明書の交付を受けます。"},
            {"step": "Step 2", "title": "健康保険（国保・協会けんぽ・健保組合）へ合算申請書を提出", "desc": "医療保険側で合算計算が行われ、支給決定通知書が届きます。"},
            {"step": "Step 3", "title": "指定口座へ医療保険・介護保険それぞれから現金が按分振込", "desc": "申請から約2〜3ヶ月でそれぞれの保険者から指定口座に還付金が直接振り込まれます。"}
        ],
        "faq": [
            {"q": "別居している親の介護費用も合算できますか？", "a": "住民票が別で健康保険の扶養に入っていない場合は合算できません。同一世帯で同じ医療保険に加入していることが条件です。"},
            {"q": "過去の分はさかのぼって請求できますか？", "a": "計算期間の翌日（8月1日）から2年以内であれば、過去2年分までさかのぼって請求が可能です。"}
        ],
        "hoporin_tip": "月ごとの『高額療養費』や『高額介護サービス費』を使っていても、さらに年単位で合算してダブルで戻ってくるのがこの制度の凄さです！申請しないと1円も戻らないので絶対チェックしてくださいね🐧！",
        "source_name": "厚生労働省「高額医療・高額介護合算制度について」",
        "source_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html",
        "date": "2026-11-16"
    },
    {
        "id": "shougai-nenkin-seishin-tsuuin-2026",
        "category": "年金・健康支援",
        "title": "【うつ病・適応障害も対象】仕事を休職・退職した人が知るべき『障害年金』年70万円〜150万円以上の受給要件と初診日の壁",
        "summary": "身体の障害だけでなく、うつ病・双極性障害・パニック障害・がん治療・糖尿病合併症などでも受給できる『障害年金』。働きながらでも要件を満たせば受け取れる国の重要保障と、初診日証明のポイントを解説します。",
        "target_audience": [
            "うつ病やメンタル疾患、慢性疾患で日常生活や就労に著しい制限がある方",
            "傷病手当金の受給期間（1年6ヶ月）が終わりそうでその後の収入が不安な方",
            "障害手帳を持っていなくても障害年金が受け取れるか知りたい方"
        ],
        "benefit_amount": "障害基礎年金2級で年約81.6万円、障害厚生年金なら報酬比例部分が加算され年100万〜180万円超＋子の加算",
        "table_headers": ["年金の種類", "加入要件（初診日時点）", "対象等級", "年金額目安（単身）"],
        "table_rows": [
            ["障害基礎年金", "初診日に国民年金に加入（自営業・無職・主婦等）", "1級・2級", "1級: 約102万円/年、2級: 約81.6万円/年"],
            ["障害厚生年金", "初診日に厚生年金に加入（会社員・公務員）", "1級・2級・3級・手当金", "基礎年金＋報酬比例年金（3級最低保障約61万円/年）"],
            ["障害手当金（一時金）", "初診日に厚生年金加入で3級より軽度の後遺障害", "一時金のみ", "最低保障額 約122万円（一括支給）"],
            ["特別障害給付金", "国民年金任意加入の対象だった学生時代の初診", "1級・2級", "1級: 約5.3万円/月、2級: 約4.2万円/月"]
        ],
        "steps": [
            {"step": "Step 1", "title": "『初診日』を特定し、保険料納付要件を満たしているか年金事務所で確認", "desc": "初診日の前日において、直近1年間に未納がないか、または全期間の3分の2以上納付済である必要があります。"},
            {"step": "Step 2", "title": "初診の病院で『受診状況等証明書』を取得し、現在の主治医に診断書を依頼", "desc": "精神障害の場合は、就労不能状態や日常生活能力の判定（日常生活の困難度）が審査の核心になります。"},
            {"step": "Step 3", "title": "本人が記載する『病歴・就労状況等申立書』を作成して年金事務所へ提出", "desc": "発病から現在までの通院歴、仕事への支障、家族の支援状況を事実に基づき具体的に書き込みます。"}
        ],
        "faq": [
            {"q": "仕事を続けていたら受給できませんか？", "a": "障害厚生年金3級であれば、会社員として働きながら受給している方も多数います。2級以上でも就労形態や職場の配慮状況によって受給可能です。"},
            {"q": "障害者手帳がないと申請できませんか？", "a": "障害者手帳と障害年金は全く別の制度・基準です。手帳を持っていなくても年金の申請・受給は可能です。"}
        ],
        "hoporin_tip": "一番の落とし穴は『一番最初に心療内科やメンタルクリニックに行った日（初診日）』のカルテが廃棄されてしまうことです！病院のカルテ保存義務は5年なので、迷ったら今すぐ初診証明だけ取っておきましょう🐧！",
        "source_name": "日本年金機構「障害年金制度のご案内」",
        "source_url": "https://www.nenkin.go.jp/service/jukyu/shougainenkin/jukyu-yoken/20150401-01.html",
        "date": "2026-11-17"
    },
    {
        "id": "jiritsushien-iryou-seishin-1wari-2026",
        "category": "医療費軽減制度",
        "title": "【心療内科・精神科の通院費が1割負担に】処方薬やカウンセリング代が激減する『自立支援医療（精神通院医療）』の申請手順と所得制限",
        "summary": "不眠症、うつ病、適応障害、パニック障害などで定期的に心療内科・精神科に通院している方の自己負担が3割から『1割』に下がる国の公的支援。薬局での調剤代も1割になるため、毎月の医療費負担を大幅に削減できます。",
        "target_audience": [
            "心療内科や精神科に月1〜2回定期通院し、抗うつ薬や睡眠薬を処方されている方",
            "診察代と薬代で毎月数千円〜1万円以上の出費が続いている方",
            "自己負担上限額（月2,500円〜20,000円）が適用される条件を知りたい方"
        ],
        "benefit_amount": "通院医療費と処方薬代の窓口負担が3割→1割に軽減＋世帯所得に応じた月額自己負担上限額（年数万円〜十数万円節約）",
        "table_headers": ["世帯の課税状況", "世帯所得・年収目安", "月額自己負担上限額（一般）", "「重度かつ継続」の場合"],
        "table_rows": [
            ["生活保護世帯", "生活保護受給世帯", "0円（全額公費）", "0円"],
            ["低所得1（市町村民税非課税）", "障害年金等を含む年収80万円以下", "2,500円/月", "2,500円/月"],
            ["低所得2（市町村民税非課税）", "年収80万円超〜非課税世帯", "5,000円/月", "5,000円/月"],
            ["中間所得1（市町村民税課税）", "市町村民税（所得割）3.3万円未満", "医療保険の自己負担限度額", "5,000円/月"],
            ["中間所得2（市町村民税課税）", "市町村民税（所得割）23.5万円未満", "医療保険の自己負担限度額", "10,000円/月"]
        ],
        "steps": [
            {"step": "Step 1", "title": "通院中の主治医に『自立支援医療用の診断書』の作成を依頼", "desc": "病院窓口で「自立支援医療を申請したい」と伝えると、指定様式の診断書を発行してもらえます。"},
            {"step": "Step 2", "title": "市区町村の障害福祉窓口（保健福祉センター等）へ必要書類を提出", "desc": "診断書、健康保険証、世帯全員の住民票・課税証明書を持参して申請します。"},
            {"step": "Step 3", "title": "『受給者証』が交付されたら、指定の病院と薬局の窓口で提示", "desc": "申請日から即座に適用（控えの提示で1割負担精算）され、有効期間は1年間（毎年更新）です。"}
        ],
        "faq": [
            {"q": "会社にバレずに申請できますか？", "a": "役所の福祉窓口での手続きとなり、会社への通知は一切行きません。安心して個人で申請できます。"},
            {"q": "複数の病院や薬局で使えますか？", "a": "原則として受給者証に登録した指定医療機関（主たる病院1箇所＋薬局1〜2箇所）でのみ1割負担が適用されます。"}
        ],
        "hoporin_tip": "病院の先生や受付からは積極的に教えてくれないことが多いですが、申請した当日の診察代・薬代から1割になります！月々の医療費が半額以下になるので、通院中の方はすぐ先生に相談してくださいね🐧！",
        "source_name": "厚生労働省「自立支援医療（精神通院医療）の概要」",
        "source_url": "https://www.mhlw.go.jp/bunya/shougaihoken/jiritsu/seishin.html",
        "date": "2026-11-18"
    },
    {
        "id": "shoutotsugyou-kyuufukin-60sai-2026",
        "category": "シニア雇用・給付金",
        "title": "【60歳以降も働く人の特権】給料が下がっても国が最大15%補填する『高年齢雇用継続給付』と年金併給調整のリアル",
        "summary": "定年再雇用で60歳以降の給料が60歳到達時と比べて75%未満に激減した際、ハローワークから毎月給料の最大15%（2025年以降新規受給者は最大10%）が現金支給される雇用保険のセーフティネット制度を詳しく解説します。",
        "target_audience": [
            "60歳で定年を迎え、同じ会社で再雇用（嘱託・契約）として働く予定の会社員",
            "定年後に給料が30〜50%カットされ、手取りが大幅に減ってしまう方",
            "在職老齢年金とどちらが得か、併給時の支給停止ルールを知りたい方"
        ],
        "benefit_amount": "毎月の賃金の最大15%（新規受給者は最大10%・上限月額約40万円台まで）を65歳になるまで非課税で毎月支給",
        "table_headers": ["給与低下率（60歳時点比）", "支給率（〜2025年3月受給開始）", "新支給率（2025年4月〜受給開始）", "支給の有無"],
        "table_rows": [
            ["61%以下に低下", "各月の賃金の15%", "各月の賃金の10%", "満額支給"],
            ["65%程度に低下", "各月の賃金の約9.1%", "各月の賃金の約6.1%", "減額支給"],
            ["70%程度に低下", "各月の賃金の約3.4%", "各月の賃金の約2.3%", "減額支給"],
            ["75%以上に維持", "0%（不支給）", "0%（不支給）", "支給なし"]
        ],
        "steps": [
            {"step": "Step 1", "title": "会社の人事・総務を通じてハローワークへ『受給資格確認』手続き", "desc": "60歳到達時の賃金月額証明書を会社からハローワークへ提出してもらいます。"},
            {"step": "Step 2", "title": "2ヶ月に1回、会社経由（または本人）で支給申請書を提出", "desc": "実際の各月の賃金支払額に基づき、給付額が計算されます。"},
            {"step": "Step 3", "title": "ハローワークから指定の個人口座へ直接非課税で振込", "desc": "所得税・住民税は非課税で、社会保険料の対象にもならない純粋な手取り収入となります。"}
        ],
        "faq": [
            {"q": "給付金をもらうと厚生年金がカットされますか？", "a": "60〜64歳で特別支給の老齢厚生年金をもらっている場合、年金の一部（標準報酬月額の最大4.8〜6%相当）が併給調整で支給停止されます。"},
            {"q": "パートやアルバイトに雇用形態が変わっても対象になりますか？", "a": "週20時間以上勤務し、雇用保険の被保険者であればパートや契約社員でも対象になります。"}
        ],
        "hoporin_tip": "給与明細を見て『こんなに減ったのか…』と落ち込む前に、必ず会社にこの給付金の手続きを依頼してください！非課税で年数十万円単位の手取り補填になる超重要制度です🐧！",
        "source_name": "厚生労働省・ハローワーク「高年齢雇用継続給付について」",
        "source_url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000135090.html",
        "date": "2026-11-19"
    },
    {
        "id": "jutaku-kounyuu-subsidies-kodomo-2026",
        "category": "住まい・建築補助",
        "title": "【新築・リフォームで最大100万円超】子育て世帯・若者夫婦が住宅を買う・改修するなら必須！『子育てエコホーム支援事業』の交付条件と申請期限",
        "summary": "高い省エネ性能（長期優良住宅・ZEH住宅）を持つ新築住宅の購入で最大100万円、既存住宅のリフォーム改修で最大30万〜60万円の国費補助金が支給される支援策。予算消化状況と対象機器の選び方を整理します。",
        "target_audience": [
            "これから注文住宅の新築や新築分譲一戸建て・マンションの購入を予定している子育て・若者世帯",
            "キッチンや浴室、節水トイレ、高断熱浴槽、断熱窓へのリフォームを検討中の方",
            "補助金をハウスメーカーや工務店の値引きと併用して住宅購入コストを下げたい方"
        ],
        "benefit_amount": "新築購入で最大100万円/戸（長期優良住宅）、リフォームで最大20万〜60万円/戸の国費直接補助",
        "table_headers": ["事業区分", "住宅の性能レベル", "対象世帯", "補助金額（1戸あたり）"],
        "table_rows": [
            ["注文住宅の新築", "長期優良住宅（耐震・省エネ最高等級）", "子育て世帯または若者夫婦世帯", "100万円/戸"],
            ["新築分譲住宅の購入", "ZEH住宅（強化外皮基準＋再生可能エネ）", "子育て世帯または若者夫婦世帯", "80万円/戸"],
            ["既存住宅のリフォーム", "窓・ドアの断熱改修＋節水トイレ・高断熱浴槽", "全世帯（子育て世帯は上限引上げ）", "最大30万〜60万円/戸"],
            ["先進的窓リノベ事業併用", "既存住宅の内窓設置・外窓交換", "全世帯対象", "最大200万円（工事費の約50%補助）"]
        ],
        "steps": [
            {"step": "Step 1", "title": "登録事業者（ハウスメーカー・工務店・リフォーム会社）と工事請負契約", "desc": "施主個人が国に直接申請するのではなく、登録事業者が代理申請を行います。"},
            {"step": "Step 2", "title": "着工後に事業者が予算枠の『予約申請』を実施（予算上限到達防止）", "desc": "国の予算執行状況をリアルタイムで確認し、枠を確保します。"},
            {"step": "Step 3", "title": "工事完了後に完了報告を行い、補助金が施主へ還元（値引きまたは現金返還）", "desc": "国から事業者に振り込まれた補助金が、最終精算時に建築代金から相殺されます。"}
        ],
        "faq": [
            {"q": "『子育て世帯』『若者夫婦』の年齢条件は何歳までですか？", "a": "申請時点で18歳未満の子がいる世帯、または夫婦のいずれかが39歳以下の世帯が対象となります。リフォームは全年齢が対象です。"},
            {"q": "住宅ローン控除と併用できますか？", "a": "はい、併用可能です。ただし住宅ローン控除の借入限度額から補助金受取額が差し引かれて計算されます。"}
        ],
        "hoporin_tip": "この補助金は『国の予算が100%に達した瞬間に締め切られる』先着順です！秋〜冬にかけて毎年駆け込みで予算終了するので、着工前の予約登録を工務店に必ず急かしてくださいね🐧！",
        "source_name": "国土交通省「子育てエコホーム支援事業事務局」",
        "source_url": "https://kosodate-ecohome.mlit.go.jp",
        "date": "2026-11-20"
    },
    {
        "id": "shougai-teate-kyuushokusha-2026",
        "category": "雇用・再就職手当",
        "title": "【早期再就職で数十万円ゲット】失業保険を満額もらうより得をする『再就職手当』の支給要件と会社都合退職のボーナス",
        "summary": "失業手当（基本手当）をあえて最後までもらわずに早期就職すると、残日数の最大70%が一括で非課税支給される『再就職手当』。派遣や自営業開業でももらえる隠れたメリットを解説します。",
        "target_audience": [
            "現在失業手当を受給中、またはこれから受給する退職者",
            "早期に再就職が決まりそうで、失業保険を損したくない方",
            "再就職後に給料が下がった場合の『就業促進定着手当』も知りたい方"
        ],
        "benefit_amount": "基本手当の支給残日数の60%〜70%相当額（20万〜60万円以上）を一括現金支給（非課税）",
        "table_headers": ["支給残日数割合", "給付率（残日数に対する割合）", "支給要件", "支給形態"],
        "table_rows": [
            ["所定給付日数の3分の2以上残し", "残日数の70%を一括支給", "1年以上の雇用が見込まれること", "一括現金振込（非課税）"],
            ["所定給付日数の3分の1以上残し", "残日数の60%を一括支給", "離職前の事業主と資本関係がないこと", "一括現金振込（非課税）"],
            ["自営業・個人事業主として開業", "残日数の60〜70%を一括支給", "開業届＋税務署控などの事業開始証明", "一括現金振込（非課税）"],
            ["就職後6ヶ月で賃金低下", "低下額の半年分（上限あり）", "就業促進定着手当として追加支給", "半年後に追加振込"]
        ],
        "steps": [
            {"step": "Step 1", "title": "内定が決まったら入社前日までにハローワークへ報告し『採用証明書』を提出", "desc": "就職日の前日時点で支給残日数が3分の1以上あることが確定されます。"},
            {"step": "Step 2", "title": "就職後に会社から採用証明書・賃金台帳の証明をもらい再就職手当支給申請書を提出", "desc": "入社翌日から1ヶ月以内にハローワークへ申請書を提出します。"},
            {"step": "Step 3", "title": "ハローワークの審査を経て指定口座へ一括振込", "desc": "約1ヶ月でまとまった現金が振り込まれます。"}
        ],
        "faq": [
            {"q": "派遣社員や契約社員でももらえますか？", "a": "はい。契約期間が1年以上見込まれ、雇用保険に加入する条件であれば雇用形態に関わらず支給されます。"},
            {"q": "給付金に税金はかかりますか？", "a": "雇用保険からの給付金はすべて所得税・住民税が非課税です。翌年の税金や健康保険料も上がりません。"}
        ],
        "hoporin_tip": "『失業保険は最後までもらった方が得』というのは大誤解です！再就職手当をもらい、新しい会社からの給料もダブルで手に入るので、早く就職した人の方がトータル手取りは圧倒的に多くなりますよ🐧！",
        "source_name": "ハローワーク・厚生労働省「再就職手当のご案内」",
        "source_url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_stepup.html",
        "date": "2026-11-21"
    },
    {
        "id": "hitorioya-jidou-fuyou-teate-2026",
        "category": "子育て・ひとり親支援",
        "title": "【ひとり親世帯に月最大4.5万円超】児童扶養手当の所得制限緩和と養育費の8割算入ルール！実家の親と同居する場合の注意点",
        "summary": "シングルマザー・シングルファザーの生活を支える国の基幹手当『児童扶養手当』。所得制限の最新引き上げ基準、養育費の算入ルール、実家の世帯分離で受給額を満額にする合法的な申請ノウハウを整理します。",
        "target_audience": [
            "離婚や未婚で子どもを一人で育てているシングルマザー・シングルファザー",
            "所得制限でこれまで一部支給や不支給になっていたひとり親世帯",
            "養育費をもらっている場合の減額計算や申告方法を知りたい方"
        ],
        "benefit_amount": "子ども1人の場合で月額最大45,500円（全部支給）、第2子・第3子加算あり。奇数月に2ヶ月分ずつ支給",
        "table_headers": ["子どもの人数", "全部支給（満額）", "一部支給（所得に応じる）", "支給月"],
        "table_rows": [
            ["第1子", "月額 45,500円", "月額 10,740円〜45,490円", "奇数月（年6回）振込"],
            ["第2子加算", "月額 10,750円加算", "月額 5,380円〜10,740円加算", "奇数月（年6回）振込"],
            ["第3子以降加算", "月額 6,450円加算/人", "月額 3,230円〜6,440円加算/人", "奇数月（年6回）振込"]
        ],
        "steps": [
            {"step": "Step 1", "title": "市区町村の子育て支援課窓口で『認定請求書』と必要書類を提出", "desc": "戸籍謄本、所得証明書、年金手帳、振込先口座、マイナンバーを準備します。"},
            {"step": "Step 2", "title": "養育費の受取額に関する申立書を記入（年間受取額の8割が所得算入）", "desc": "前年に元配偶者から受け取った養育費の額を正確に申告します。"},
            {"step": "Step 3", "title": "認定通知書が交付され、奇数月の11日頃に指定口座へ自動振込", "desc": "1月、3月、5月、7月、9月、11月にそれぞれ前月までの2ヶ月分が支払われます。"}
        ],
        "faq": [
            {"q": "実家の親と同居していると手当はもらえませんか？", "a": "同居している親（祖父母）の所得も審査対象（扶養義務者基準）になります。親の所得が高いと支給停止になる場合があります。"},
            {"q": "事実婚や同棲を始めたらどうなりますか？", "a": "法的な婚姻届を出していなくても、内縁関係や生計を同一にする同棲が始まった場合は受給資格を喪失します。"}
        ],
        "hoporin_tip": "手当をもらうだけでなく、児童扶養手当の受給者証があると『JR通勤定期券の3割引』や『粗大ごみ処理手数料免除』『水道料金減免』など自治体の独自優遇も雪だるま式に使えますよ🐧！",
        "source_name": "こども家庭庁「児童扶養手当について」",
        "source_url": "https://www.cfa.go.jp/policies/hitori-oya/fuyou-teate",
        "date": "2026-11-22"
    }
]

def generate_markdown_article(item):
    """SEO対策済み・構造化Markdown記事を生成"""
    md = f"""---
title: "{item['title']}"
category: "{item['category']}"
date: "{item['date']}"
source: "{item['source_name']}"
source_url: "{item['source_url']}"
---

# {item['title']}

> **【3秒でわかる結論】**
> {item['summary']}

<!-- [AD_SLOT_TOP]: 記事上部 広告枠 (インプレッション/クリック) -->
<div class="ad-placeholder" data-slot="top"></div>

## 1. あなたは対象？対象者チェックリスト
以下の条件に当てはまる場合、今回の制度の対象となります。

"""
    for aud in item['target_audience']:
        md += f"- [ ] **{aud}**\n"
    
    md += f"""
### 💡 いくら得する？（目安受給・減税額）
**{item['benefit_amount']}**

---

## 2. 【一覧表】条件と具体的な控除・補助内容

| {' | '.join(item['table_headers'])} |
| {' | '.join(['---'] * len(item['table_headers']))} |
"""
    for row in item['table_rows']:
        md += f"| {' | '.join(row)} |\n"

    md += """
<!-- [AD_SLOT_MIDDLE]: 記事中間 広告枠 (クリック率最大化ゾーン) -->
<div class="ad-placeholder" data-slot="middle"></div>

## 3. 損しないための手続き 3ステップ

"""
    for s in item['steps']:
        md += f"### {s['step']}: {s['title']}\n{s['desc']}\n\n"

    md += """---

## 4. よくある疑問・トラブル回避Q&A

"""
    for f in item['faq']:
        md += f"**Q. {f['q']}**\n\n**A. {f['a']}**\n\n"

    md += f"""---

## 🐧 ほぽりんの生活防衛アドバイス

> {item['hoporin_tip']}

---

### 出典・公的参照元
- 出典：[{item['source_name']}]({item['source_url']})
"""
    return md

def get_available_gemini_models(api_key):
    """APIキーで利用可能なモデル一覧を動的に取得（バージョン移行に永久自動適応）"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HoporinBot/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    models.append(name)
            # flash系、新しいバージョンを優先ソート
            flash_models = [m for m in models if "flash" in m and "tts" not in m]
            other_models = [m for m in models if "flash" not in m and "tts" not in m and "embedding" not in m]
            if flash_models or other_models:
                return flash_models + other_models
    except Exception as e:
        print(f"ℹ️ 利用可能モデル一覧の動的取得スキップ: {e}")
    return ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]


def call_gemini_api(prompt, api_key):
    """Gemini API を呼び出してJSONオブジェクトを取得"""
    models = get_available_gemini_models(api_key)
    print(f"📋 Gemini API 検出モデル候補: {models[:5]}")
    for model in models[:6]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            print(f"🤖 Gemini API ({model}) に記事生成をリクエスト中...")
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_body = resp.read().decode("utf-8")
                res_json = json.loads(res_body)
                content_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                if content_text.startswith("```"):
                    content_text = re.sub(r"^```[a-zA-Z]*\n?", "", content_text)
                    content_text = re.sub(r"\n?```$", "", content_text)
                parsed = json.loads(content_text.strip())
                print(f"✅ Gemini API ({model}) から記事データの生成に成功しました！")
                return parsed
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            print(f"⚠️ Gemini API ({model}) HTTPエラー {e.code}: {err_msg[:120]}")
        except Exception as e:
            print(f"⚠️ Gemini API ({model}) 呼び出し失敗: {e}")
        time.sleep(1)
    return None



def generate_article_with_gemini(existing_titles, api_key):
    """Gemini APIを活用して、既存タイトルと重複しない本格的な公的ライフハック記事を生成"""
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    recent_titles_str = "\n".join([f"- {t}" for t in existing_titles[:40]])

    prompt = f"""あなたは公的制度・給付金・税制・生活防衛ハック専門の愛されキャラクター「ほぽりん」（ペンギン研究家 🐧）です。
日本の厚生労働省、国税庁、こども家庭庁、経済産業省、各自治体が実施している「実在する公的支援制度・給付金・減税・補助金」について、一般の人が「知らなきゃ損する」超有益な最新解説記事を1件作成してください。

【厳守ルール】
1. 【重複絶対禁止】以下の「既存記事タイトル一覧」にある制度・テーマとは絶対に被らない、未執筆の公的制度・支援策を取り上げてください。
--- 既存記事一覧 ---
{recent_titles_str}
--------------------
2. 実在する正確な制度・根拠法・公的機関に基づき執筆してください（架空の制度や嘘は厳禁）。
   例: 傷病手当金、高額療養費、介護休業給付金、自立支援医療、児童扶養手当、特定支出控除、住宅ローン減税、セルフメディケーション税制、求職者支援制度、遺族年金、障害年金、自治体の住居確保給付金・転居補助、リスキリング給付金など実在制度。
3. 対象者、受給額・軽減額の目安、具体的な申請ステップ、よくある疑問（Q&A）、ほぽりんのアドバイス（語尾に🐧）を含めてください。
4. 出力は必ず以下のJSONスキーマに従った単一のJSONオブジェクト（マークダウンのコードブロックなし）として出力してください。

【出力JSONフォーマット】
{{
  "id": "英数字ハイフンのみのユニークなID（例: jiritushien-iryouhi-shougai-2026）",
  "category": "カテゴリ名（例: 医療・福祉支援, 子育て支援, 税金・控除, 雇用・再就職, 住まい・暮らし）",
  "title": "【読者の目を引くフック】制度の正式名と最大のメリット（35〜55文字程度）",
  "summary": "3秒でわかる結論・概要（100〜180文字程度）",
  "target_audience": [
    "対象となる条件1",
    "対象となる条件2",
    "対象となる条件3"
  ],
  "benefit_amount": "いくら得する・受給できるかの目安（例: 自己負担額が3割から1割に軽減、月最大2万円支給 等）",
  "table_headers": ["区分・条件", "支援内容・給付額", "自己負担・カバー率", "申請窓口・備考"],
  "table_rows": [
    ["項目1", "内容1", "割合1", "窓口1"],
    ["項目2", "内容2", "割合2", "窓口2"],
    ["項目3", "内容3", "割合3", "窓口3"]
  ],
  "steps": [
    {{"step": "Step 1", "title": "ステップ1の要点", "desc": "具体的な手続き説明"}},
    {{"step": "Step 2", "title": "ステップ2の要点", "desc": "具体的な手続き説明"}},
    {{"step": "Step 3", "title": "ステップ3の要点", "desc": "具体的な手続き説明"}}
  ],
  "faq": [
    {{"q": "読者が最も気になる疑問1", "a": "わかりやすい具体的回答1"}},
    {{"q": "読者が最も気になる疑問2", "a": "わかりやすい具体的回答2"}}
  ],
  "hoporin_tip": "ほぽりん（ペンギン研究家）からの生活防衛ワンポイントアドバイス！語尾に🐧をつけてください。",
  "source_name": "公的機関の正式名称（例: 厚生労働省「自立支援医療制度の概要」）",
  "source_url": "実在する公的機関の公式ページURL（例: https://www.mhlw.go.jp/... 等）",
  "date": "{today_str}"
}}
"""
    return call_gemini_api(prompt, api_key)


def main():
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    # 1. 既存記事を読み込み（重複を排除）
    existing_articles = []
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
        except Exception:
            existing_articles = []

    seen_titles = set()
    seen_ids = set()
    cleaned_articles = []

    for art in existing_articles:
        title = art.get("title")
        art_id = art.get("id")
        if title not in seen_titles and art_id not in seen_ids:
            seen_titles.add(title)
            seen_ids.add(art_id)
            cleaned_articles.append(art)

    added_count = 0

    # 2. Gemini API連携によるAI記事自動生成（定型文廃止）
    if GEMINI_API_KEY:
        print("🚀 [Store 1: ほぽりん] Gemini API連携によるAI新着記事生成を開始します...")
        try:
            ai_article = generate_article_with_gemini(list(seen_titles), GEMINI_API_KEY)
            if ai_article and isinstance(ai_article, dict):
                art_id = ai_article.get("id") or f"lifehack-{TODAY_STR}-{int(time.time())}"
                # ハイフン・英数字に正規化
                art_id = re.sub(r"[^a-zA-Z0-9\-]", "-", art_id).strip("-").lower()
                ai_article["id"] = art_id
                title = ai_article.get("title", "")

                if title and title not in seen_titles and art_id not in seen_ids:
                    if "date" not in ai_article or not ai_article["date"]:
                        ai_article["date"] = TODAY_STR
                    
                    seen_titles.add(title)
                    seen_ids.add(art_id)
                    cleaned_articles.append(ai_article)

                    # Markdown記事ファイルを生成
                    md_path = os.path.join(ARTICLES_DIR, f"{art_id}.md")
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(generate_markdown_article(ai_article))

                    added_count += 1
                    print(f"✨ [Store 1 Gemini AI新着記事生成成功] {title[:36]}... (ID: {art_id})")
        except Exception as e:
            print(f"⚠️ [Store 1] Gemini API記事生成中に例外発生: {e}")

    # 3. フォールバック（APIキー未設定またはAPIエラー時のセーフティネット）
    if added_count == 0:
        if not GEMINI_API_KEY:
            print("ℹ️ GEMINI_API_KEY が未設定のため、未執筆テーマプールからのフォールバック追加を確認します。")
        for topic in STORE1_TOPIC_POOL:
            if topic["title"] not in seen_titles and topic["id"] not in seen_ids:
                topic_date = topic.get("date", TODAY_STR)
                if topic_date > TODAY_STR:
                    continue
                new_item = dict(topic)
                if "date" not in new_item or not new_item["date"]:
                    new_item["date"] = TODAY_STR
                seen_titles.add(new_item["title"])
                seen_ids.add(new_item["id"])
                cleaned_articles.append(new_item)
                # Markdown生成
                md_path = os.path.join(ARTICLES_DIR, f"{new_item['id']}.md")
                if not os.path.exists(md_path):
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(generate_markdown_article(new_item))
                added_count += 1
                print(f"✨ [Store 1 フォールバック記事追加] {new_item['title'][:32]}...")
                break

    # 4. 日付降順でソートして保存
    cleaned_articles = sorted(
        cleaned_articles,
        key=lambda x: x.get("date", "2026-11-11"),
        reverse=True
    )

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_articles, f, ensure_ascii=False, indent=2)

    print(f"🎉 Store 1 (ほぽりん) 記事更新完了: 全{len(cleaned_articles)}記事（新規追加: {added_count}件, 重複タイトル・ID: 0件）")

if __name__ == "__main__":
    main()

