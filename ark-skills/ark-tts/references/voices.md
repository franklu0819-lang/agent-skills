# 火山豆包语音 · 2.0 音色库（voice_type 速查）

来源：官方音色列表（经第三方镜像整理，2026-09 抓取），共 200+ 音色。
配合 `tts.py --speaker <voice_type>` 使用；`--list-voices [关键词]` 可搜索本表。

**resource-id 自动推断规则（tts.py 内置，2026-09-17 实测）**：
- `S_` 开头（个人复刻）→ `seed-icl-2.0`
- 音色名含 `uranus`（本表全部 2.0 音色，含 `ICL_uranus_*`）→ `seed-tts-2.0`
- 其他 `_bigtts`（1.0 代，如 `zh_male_beijingxiaoye_emo_v2_mars_bigtts`）→ `volc.service_type.10029`
- 配错的症状：HTTP 200 + code 55000000 空音频

**教程/解说场景推荐**：解说小明、广告解说、磁性解说男声、流畅女声、儒雅逸辰、小何、Vivi（多方言）。
`zh_female_vv_uranus_bigtts` 支持 additions.explicit_dialect：dongbei/shaanxi/sichuan（方言）。

## 音色表

| 场景 | 音色名称 | voice_type | 语种 |
|---|---|---|---|
| 通用 | Vivi | zh_female_vv_uranus_bigtts | 中/日/印尼/墨西西；方言川陕东北 |
| 通用 | 小何 | zh_female_xiaohe_uranus_bigtts | 中文 |
| 通用 | 云舟 | zh_male_m191_uranus_bigtts | 中文 |
| 通用 | 小天 | zh_male_taocheng_uranus_bigtts | 中文 |
| 通用 | 刘飞 | zh_male_liufei_uranus_bigtts | 中文 |
| 通用 | 魅力苏菲 | zh_female_sophie_uranus_bigtts | 中文 |
| 通用 | 清新女声 | zh_female_qingxinnvsheng_uranus_bigtts | 中文 |
| 通用 | 甜美小源 | zh_female_tianmeixiaoyuan_uranus_bigtts | 中文 |
| 通用 | 甜美桃子 | zh_female_tianmeitaozi_uranus_bigtts | 中文 |
| 通用 | 爽快思思 | zh_female_shuangkuaisisi_uranus_bigtts | 中文 |
| 通用 | 邻家女孩 | zh_female_linjianvhai_uranus_bigtts | 中文 |
| 通用 | 少年梓辛/Brayan | zh_male_shaonianzixin_uranus_bigtts | 中文 |
| 通用 | 邻家男孩 | zh_male_linjiananhai_uranus_bigtts | 中文 |
| 通用 | 儒雅青年 | zh_male_ruyaqingnian_uranus_bigtts | 中文 |
| 通用 | 温暖阿虎/Alvin | zh_male_wennuanahu_uranus_bigtts | 中文 |
| 通用 | 奶气萌娃 | zh_male_naiqimengwa_uranus_bigtts | 中文 |
| 通用 | 婆婆 | zh_female_popo_uranus_bigtts | 中文 |
| 通用 | 高冷御姐 | zh_female_gaolengyujie_uranus_bigtts | 中文 |
| 通用 | 傲娇霸总 | zh_male_aojiaobazong_uranus_bigtts | 中文 |
| 通用 | 反卷青年 | zh_male_fanjuanqingnian_uranus_bigtts | 中文 |
| 通用 | 温柔淑女 | zh_female_wenroushunv_uranus_bigtts | 中文 |
| 通用 | 活力小哥 | zh_male_huolixiaoge_uranus_bigtts | 中文 |
| 通用 | 萌丫头/Cutey | zh_female_mengyatou_uranus_bigtts | 中文 |
| 通用 | 贴心女声/Candy | zh_female_tiexinnvsheng_uranus_bigtts | 中文 |
| 通用 | 鸡汤妹妹/Hope | zh_female_jitangmei_uranus_bigtts | 中文 |
| 通用 | 磁性解说男声/Morgan | zh_male_cixingjieshuonan_uranus_bigtts | 中文 |
| 通用 | 亮嗓萌仔 | zh_male_liangsangmengzai_uranus_bigtts | 中文 |
| 通用 | 开朗姐姐 | zh_female_kailangjiejie_uranus_bigtts | 中文 |
| 通用 | 高冷沉稳 | zh_male_gaolengchenwen_uranus_bigtts | 中文 |
| 通用 | 深夜播客 | zh_male_shenyeboke_uranus_bigtts | 中文 |
| 通用 | 开朗弟弟 | zh_male_kailangdidi_uranus_bigtts | 中文 |
| 通用 | 亲切女声 | zh_female_qinqienv_uranus_bigtts | 中文 |
| 通用 | 快乐小东 | zh_male_kuailexiaodong_uranus_bigtts | 中文 |
| 通用 | 开朗学长 | zh_male_kailangxuezhang_uranus_bigtts | 中文 |
| 通用 | 悠悠君子 | zh_male_youyoujunzi_uranus_bigtts | 中文 |
| 通用 | 文静毛毛 | zh_female_wenjingmaomao_uranus_bigtts | 中文 |
| 通用 | 知性女声 | zh_female_zhixingnv_uranus_bigtts | 中文 |
| 通用 | 清爽男大 | zh_male_qingshuangnanda_uranus_bigtts | 中文 |
| 通用 | 渊博小叔 | zh_male_yuanboxiaoshu_uranus_bigtts | 中文 |
| 通用 | 阳光青年 | zh_male_yangguangqingnian_uranus_bigtts | 中文 |
| 通用 | 清澈梓梓 | zh_female_qingchezizi_uranus_bigtts | 中文 |
| 通用 | 甜美悦悦 | zh_female_tianmeiyueyue_uranus_bigtts | 中文 |
| 通用 | 心灵鸡汤 | zh_female_xinlingjitang_uranus_bigtts | 中文 |
| 通用 | 温柔小哥 | zh_male_wenrouxiaoge_uranus_bigtts | 中文 |
| 通用 | 柔美女友 | zh_female_roumeinvyou_uranus_bigtts | 中文 |
| 通用 | 东方浩然 | zh_male_dongfanghaoran_uranus_bigtts | 中文 |
| 通用 | 温柔小雅 | zh_female_wenrouxiaoya_uranus_bigtts | 中文 |
| 通用 | 天才童声 | zh_male_tiancaitongsheng_uranus_bigtts | 中文 |
| 通用 | 广告解说 | zh_male_guanggaojieshuo_uranus_bigtts | 中文 |
| 通用 | 解说小明 | zh_male_jieshuoxiaoming_uranus_bigtts | 中文 |
| 通用 | TVB女声 | zh_female_tvbnv_uranus_bigtts | 中文 |
| 通用 | 译制片男 | zh_male_yizhipiannan_uranus_bigtts | 中文 |
| 通用 | 俏皮女声 | zh_female_qiaopinv_uranus_bigtts | 中文 |
| 通用 | 娇喘女声 | zh_female_jiaochuannv_uranus_bigtts | 中文 |
| 通用 | 谄媚女声 | zh_female_chanmeinv_uranus_bigtts | 中文 |
| 通用 | 魅力女友 | zh_female_meilinvyou_uranus_bigtts | 中文 |
| 通用 | 温柔妈妈 | zh_female_wenroumama_uranus_bigtts | 中文 |
| 通用 | 谄媚女声 | zh_female_chanmeinv_uranus_bigtts | 中文 |
| 通用 | 亲切女声 | zh_female_qinqienv_uranus_bigtts | 中文 |
| 视频配音 | 佩奇猪 | zh_female_peiqi_uranus_bigtts | 中文 |
| 视频配音 | 猴哥 | zh_male_sunwukong_uranus_bigtts | 中文 |
| 视频配音 | 大壹 | zh_male_dayi_uranus_bigtts | 中文 |
| 视频配音 | 黑猫侦探社咪仔 | zh_female_mizai_uranus_bigtts | 中文 |
| 视频配音 | 鸡汤女 | zh_female_jitangnv_uranus_bigtts | 中文 |
| 视频配音 | 流畅女声 | zh_female_liuchangnv_uranus_bigtts | 中文 |
| 视频配音 | 儒雅逸辰 | zh_male_ruyayichen_uranus_bigtts | 中文 |
| 有声阅读 | 儿童绘本 | zh_female_xiaoxue_uranus_bigtts | 中文 |
| 有声阅读 | 霸气青叔 | zh_male_baqiqingshu_uranus_bigtts | 中文 |
| 有声阅读 | 悬疑解说 | zh_male_xuanyijieshuo_uranus_bigtts | 中文 |
| 有声阅读 | 少儿故事 | zh_female_shaoergushi_uranus_bigtts | 中文 |
| 有声阅读 | 儒雅公子 | ICL_uranus_zh_male_ruyagongzi_tob | 中文 |
| 有声阅读 | 内敛才俊 | ICL_uranus_zh_male_neiliancaijun_tob | 中文 |
| 有声阅读 | 温暖少年 | ICL_uranus_zh_male_wennuanshaonian_tob | 中文 |
| 教育 | Tina老师 | zh_female_yingyujiaoxue_uranus_bigtts | 中/英式英语 |
| 客服 | 暖阳女声 | zh_female_kefunvsheng_uranus_bigtts | 中文 |
| 客服 | 乖巧可儿 | ICL_uranus_zh_female_guaiqiaokeer_tob | 中文 |
| 客服 | 开朗婷婷 | ICL_uranus_zh_female_kailangtingting_tob | 中文 |
| 客服 | 开心小鸿 | ICL_uranus_zh_female_kaixinxiaohong_tob | 中文 |
| 客服 | 灵动欣欣 | ICL_uranus_zh_female_lingdongxinxin_tob | 中文 |
| 客服 | 理性圆子 | ICL_uranus_zh_female_lixingyuanzi_tob | 中文 |
| 客服 | 暖心茜茜 | ICL_uranus_zh_female_nuanxinqianqian_tob | 中文 |
| 客服 | 清甜莓莓 | ICL_uranus_zh_female_qingtianmeimei_tob | 中文 |
| 客服 | 清甜桃桃 | ICL_uranus_zh_female_qingtiantaotao_tob | 中文 |
| 客服 | 清晰小雪 | ICL_uranus_zh_female_qingxixiaoxue_tob | 中文 |
| 客服 | 软萌糖糖 | ICL_uranus_zh_female_ruanmengtangtang_tob | 中文 |
| 客服 | 软萌团子 | ICL_uranus_zh_female_ruanmengtuanzi_tob | 中文 |
| 客服 | 甜美小橘 | ICL_uranus_zh_female_tianmeixiaoju_tob | 中文 |
| 客服 | 甜美小雨 | ICL_uranus_zh_female_tianmeixiaoyu_tob | 中文 |
| 客服 | 秀丽倩倩 | ICL_uranus_zh_female_xiuliqianqian_tob | 中文 |
| 客服 | 沉稳明仔 | ICL_uranus_zh_male_chenwenmingzai_tob | 中文 |
| 客服 | 清新波波 | ICL_uranus_zh_male_qingxinbobo_tob | 中文 |
| 客服 | 亲切小卓 | ICL_uranus_zh_male_qinqiexiaozhuo_tob | 中文 |
| 客服 | 爽朗小阳 | ICL_uranus_zh_male_shuanglangxiaoyang_tob | 中文 |
| 客服 | 阳光洋洋 | ICL_uranus_zh_male_yangguangyangyang_tob | 中文 |
| 客服 | 清新沐沐 | ICL_uranus_zh_male_qingxinmumu_tob | 中文 |
| 客服 | 温婉珊珊 | ICL_uranus_zh_female_wenwanshanshan_tob | 中文 |
| 客服 | 热情艾娜 | ICL_uranus_zh_female_reqingaina_tob | 中文 |
| 客服 | 轻盈朵朵 | ICL_uranus_zh_female_qingyingduoduo_tob | 中文 |
| 角色 | 知性灿灿 | zh_female_cancan_uranus_bigtts | 中文 |
| 角色 | 撒娇学妹 | zh_female_sajiaoxuemei_uranus_bigtts | 中文 |
| 角色 | 直率英子 | zh_female_zhishuaiyingzi_uranus_bigtts | 中文 |
| 角色 | 四郎 | zh_male_silang_uranus_bigtts | 中文 |
| 角色 | 擎苍 | zh_male_qingcang_uranus_bigtts | 中文 |
| 角色 | 熊二 | zh_male_xionger_uranus_bigtts | 中文 |
| 角色 | 樱桃丸子 | zh_female_yingtaowanzi_uranus_bigtts | 中文 |
| 角色 | 懒音绵宝 | zh_male_lanyinmianbao_uranus_bigtts | 中文 |
| 角色 | 古风少御 | zh_female_gufengshaoyu_uranus_bigtts | 中文 |
| 角色 | 鲁班七号 | zh_male_lubanqihao_uranus_bigtts | 中文 |
| 角色 | 林潇 | zh_female_linxiao_uranus_bigtts | 中文 |
| 角色 | 玲玲姐姐 | zh_female_lingling_uranus_bigtts | 中文 |
| 角色 | 春日部姐姐 | zh_female_chunribu_uranus_bigtts | 中文 |
| 角色 | 唐僧 | zh_male_tangseng_uranus_bigtts | 中文 |
| 角色 | 庄周 | zh_male_zhuangzhou_uranus_bigtts | 中文 |
| 角色 | 猪八戒 | zh_male_zhubajie_uranus_bigtts | 中文 |
| 角色 | 感冒电音姐姐 | zh_female_ganmaodianyin_uranus_bigtts | 中文 |
| 角色 | 女雷神 | zh_female_nvleishen_uranus_bigtts | 中文 |
| 角色 | 武则天 | zh_female_wuzetian_uranus_bigtts | 中文 |
| 角色 | 顾姐 | zh_female_gujie_uranus_bigtts | 中文 |
| 多语种 | Charlie | ICL_uranus_en_female_charlie_tob | 美式英语 |
| 多语种 | Ethan | ICL_uranus_en_male_ethan_tob | 澳洲英语 |
| 多语种 | Alastor | ICL_uranus_en_male_alastor_tob | 英式英语 |
| 多语种 | Chucky | ICL_uranus_en_male_chucky_tob | 美式英语 |
| 多语种 | Noah | ICL_uranus_en_male_noah_tob | 美式英语 |
| 多语种 | Jigsaw | ICL_uranus_en_male_jigsaw_tob | 美式英语 |
| 多语种 | Clown Man | ICL_uranus_en_male_clown_man_tob | 美式英语 |
| 多语种 | Cartoon Chef | ICL_uranus_en_male_cartoon_chef_tob | 美式英语 |
| 多语种 | Frosty Man | ICL_uranus_en_male_frosty_man_tob | 美式英语 |
| 多语种 | The Grinch | ICL_uranus_en_male_the_grinch_tob | 美式英语 |
| 多语种 | Kevin McCallister | ICL_uranus_en_male_kevin_mccallister_tob | 美式英语 |
| 多语种 | Michael | ICL_uranus_en_male_michael_tob | 美式英语 |
| 多语种 | Big Boogie | ICL_uranus_en_male_big_boogie_tob | 美式英语 |
| 多语种 | Xavier | ICL_uranus_en_male_xavier_tob | 美式英语 |
| 多语种 | Zayne | ICL_uranus_en_male_zayne_tob | 美式英语 |
| 角色(ICL) | 傲娇女友 | ICL_uranus_zh_female_aojiaonvyou_tob | 中文 |
| 角色(ICL) | 邪魅女王 | ICL_uranus_zh_female_xiemeinvwang_tob | 中文 |
| 角色(ICL) | 病娇姐姐 | ICL_uranus_zh_female_bingjiaojiejie_tob | 中文 |
| 角色(ICL) | 病娇萌妹 | ICL_uranus_zh_female_bingjiaomengmei_tob | 中文 |
| 角色(ICL) | 成熟温柔 | ICL_uranus_zh_female_chengshuwenrou_tob | 中文 |
| 角色(ICL) | 成熟姐姐 | ICL_uranus_zh_female_chengshujiejie_tob | 中文 |
| 角色(ICL) | 纯真少女 | ICL_uranus_zh_female_chunzhenshaonv_tob | 中文 |
| 角色(ICL) | 纯澈女生 | ICL_uranus_zh_female_chunchenvsheng_tob | 中文 |
| 角色(ICL) | 妩媚可人 | ICL_uranus_zh_female_wumeikeren_tob | 中文 |
| 角色(ICL) | 和蔼奶奶 | ICL_uranus_zh_female_heainainai_tob | 中文 |
| 角色(ICL) | 活泼刁蛮 | ICL_uranus_zh_female_huopodiaoman_tob | 中文 |
| 角色(ICL) | 娇憨女王 | ICL_uranus_zh_female_jiaohannvwang_tob | 中文 |
| 角色(ICL) | 娇弱萝莉 | ICL_uranus_zh_female_jiaoruoluoli_tob | 中文 |
| 角色(ICL) | 假小子 | ICL_uranus_zh_female_jiaxiaozi_tob | 中文 |
| 角色(ICL) | 精灵向导 | ICL_uranus_zh_female_jinglingxiangdao_tob | 中文 |
| 角色(ICL) | 可爱女生 | ICL_uranus_zh_female_keainvsheng_tob | 中文 |
| 角色(ICL) | 邻居阿姨 | ICL_uranus_zh_female_linjuayi_tob | 中文 |
| 角色(ICL) | 甜美娇俏 | ICL_uranus_zh_female_tianmeijiaoqiao_tob | 中文 |
| 角色(ICL) | 清冷高雅 | ICL_uranus_zh_female_qinglenggaoya_tob | 中文 |
| 角色(ICL) | 性感魅惑 | ICL_uranus_zh_female_xingganmeihuo_tob | 中文 |
| 角色(ICL) | 暖心学姐 | ICL_uranus_zh_female_nuanxinxuejie_tob | 中文 |
| 角色(ICL) | 倾心少女 | ICL_uranus_zh_female_qingxinshaonv_tob | 中文 |
| 角色(ICL) | 柔骨魂师 | ICL_uranus_zh_female_rouguhunshi_tob | 中文 |
| 角色(ICL) | 甜美活泼 | ICL_uranus_zh_female_tianmeihuopo_tob | 中文 |
| 角色(ICL) | 调皮公主 | ICL_uranus_zh_female_tiaopigongzhu_tob | 中文 |
| 角色(ICL) | 贴心女友 | ICL_uranus_zh_female_tiexinnvyou_tob | 中文 |
| 角色(ICL) | 温柔女神 | ICL_uranus_zh_female_wenrounvshen_tob | 中文 |
| 角色(ICL) | 温柔文雅 | ICL_uranus_zh_female_wenrouwenya_tob | 中文 |
| 角色(ICL) | 知心姐姐 | ICL_uranus_zh_female_zhixinjiejie_tob | 中文 |
| 角色(ICL) | 妩媚御姐 | ICL_uranus_zh_female_wumeiyujie_tob | 中文 |
| 角色(ICL) | 元气甜妹 | ICL_uranus_zh_female_yuanqitianmei_tob | 中文 |
| 角色(ICL) | 邪魅御姐 | ICL_uranus_zh_female_xiemeiyujie_tob | 中文 |
| 角色(ICL) | 性感御姐 | ICL_uranus_zh_female_xingganyujie_tob | 中文 |
| 角色(ICL) | 贴心闺蜜 | ICL_uranus_zh_female_tiexinguimi_tob | 中文 |
| 角色(ICL) | 贴心妹妹 | ICL_uranus_zh_female_tiexinmeimei_tob | 中文 |
| 角色(ICL) | 温柔白月光 | ICL_uranus_zh_female_wenroubaiyueguang_tob | 中文 |
| 角色(ICL) | 初恋女友 | ICL_uranus_zh_female_chuliannvyou_tob | 中文 |
| 角色(ICL) | 知性温婉 | ICL_uranus_zh_female_zhixingwenwan_tob | 中文 |
| 角色(ICL) | 傲气凌人 | ICL_uranus_zh_male_aoqilingren_tob | 中文 |
| 角色(ICL) | 黯刃秦主 | ICL_uranus_zh_male_anrenqinzhu_tob | 中文 |
| 角色(ICL) | 傲娇公子 | ICL_uranus_zh_male_aojiaogongzi_tob | 中文 |
| 角色(ICL) | 傲娇精英 | ICL_uranus_zh_male_aojiaojingying_tob | 中文 |
| 角色(ICL) | 傲慢青年 | ICL_uranus_zh_male_aomanqingnian_tob | 中文 |
| 角色(ICL) | 傲慢少爷 | ICL_uranus_zh_male_aomanshaoye_tob | 中文 |
| 角色(ICL) | 枕边低语 | ICL_uranus_zh_male_zhenbiandiyu_tob | 中文 |
| 角色(ICL) | 霸道少爷 | ICL_uranus_zh_male_badaoshaoye_tob | 中文 |
| 角色(ICL) | 霸道总裁 | ICL_uranus_zh_male_badaozongcai_tob | 中文 |
| 角色(ICL) | 病娇白莲 | ICL_uranus_zh_male_bingjiaobailian_tob | 中文 |
| 角色(ICL) | 病娇弟弟 | ICL_uranus_zh_male_bingjiaodidi_tob | 中文 |
| 角色(ICL) | 病娇哥哥 | ICL_uranus_zh_male_bingjiaogege_tob | 中文 |
| 角色(ICL) | 病娇男友 | ICL_uranus_zh_male_bingjiaonanyou_tob | 中文 |
| 角色(ICL) | 病娇少年 | ICL_uranus_zh_male_bingjiaoshaonian_tob | 中文 |
| 角色(ICL) | 病弱公子 | ICL_uranus_zh_male_bingruogongzi_tob | 中文 |
| 角色(ICL) | 病弱少年 | ICL_uranus_zh_male_bingruoshaonian_tob | 中文 |
| 角色(ICL) | 不羁青年 | ICL_uranus_zh_male_bujiqingnian_tob | 中文 |
| 角色(ICL) | 醇厚低音 | ICL_uranus_zh_male_chunhoudiyin_tob | 中文 |
| 角色(ICL) | 咆哮小哥 | ICL_uranus_zh_male_paoxiaoxiaoge_tob | 中文 |
| 角色(ICL) | 炀炀 | ICL_uranus_zh_male_yangyang_tob | 中文 |
| 角色(ICL) | 孱弱少爷 | ICL_uranus_zh_male_chanruoshaoye_tob | 中文 |
| 角色(ICL) | 成熟总裁 | ICL_uranus_zh_male_chengshuzongcai_tob | 中文 |
| 角色(ICL) | 清逸苏感 | ICL_uranus_zh_male_qingyisugan_tob | 中文 |
| 角色(ICL) | 纯真学弟 | ICL_uranus_zh_male_chunzhenxuedi_tob | 中文 |
| 角色(ICL) | 磁性男嗓 | ICL_uranus_zh_male_cixingnansang_tob | 中文 |
| 角色(ICL) | 醋精男生 | ICL_uranus_zh_male_cujingnansheng_tob | 中文 |
| 角色(ICL) | 醋精男友 | ICL_uranus_zh_male_cujingnanyou_tob | 中文 |
| 角色(ICL) | 低音沉郁 | ICL_uranus_zh_male_diyinchenyu_tob | 中文 |
| 角色(ICL) | 风发少年 | ICL_uranus_zh_male_fengfashaonian_tob | 中文 |
| 角色(ICL) | 腹黑公子 | ICL_uranus_zh_male_fuheigongzi_tob | 中文 |
| 角色(ICL) | 干净少年 | ICL_uranus_zh_male_ganjingshaonian_tob | 中文 |
| 角色(ICL) | 高冷总裁 | ICL_uranus_zh_male_gaolengzongcai_tob | 中文 |
| 角色(ICL) | 孤傲公子 | ICL_uranus_zh_male_guaogongzi_tob | 中文 |
| 角色(ICL) | 孤高公子 | ICL_uranus_zh_male_gugaogongzi_tob | 中文 |
| 角色(ICL) | 诡异神秘 | ICL_uranus_zh_male_guiyishenmi_tob | 中文 |
| 角色(ICL) | 固执病娇 | ICL_uranus_zh_male_guzhibingjiao_tob | 中文 |
| 角色(ICL) | 憨厚敦实 | ICL_uranus_zh_male_hanhoudunshi_tob | 中文 |
| 角色(ICL) | 活力青年 | ICL_uranus_zh_male_huoliqingnian_tob | 中文 |
| 角色(ICL) | 活泼男友 | ICL_uranus_zh_male_huoponanyou_tob | 中文 |
| 角色(ICL) | 活泼爽朗 | ICL_uranus_zh_male_huoposhuanglang_tob | 中文 |
| 角色(ICL) | 胡子叔叔 | ICL_uranus_zh_male_huzishushu_tob | 中文 |
| 角色(ICL) | 机甲智能 | ICL_uranus_zh_male_jijiazhineng_tob | 中文 |
| 角色(ICL) | 精英青年 | ICL_uranus_zh_male_jingyingqingnian_tob | 中文 |
| 角色(ICL) | 俊逸公子 | ICL_uranus_zh_male_junyigongzi_tob | 中文 |
| 角色(ICL) | 开朗轻快 | ICL_uranus_zh_male_kailangqingkuai_tob | 中文 |
| 角色(ICL) | 开朗青年 | ICL_uranus_zh_male_kailangqingnian_tob | 中文 |
| 角色(ICL) | 蓝银草魂师 | ICL_uranus_zh_male_lanyincaohunshi_tob | 中文 |
| 角色(ICL) | 冷傲总裁 | ICL_uranus_zh_male_lengaozongcai_tob | 中文 |
| 角色(ICL) | 冷淡疏离 | ICL_uranus_zh_male_lengdanshuli_tob | 中文 |
| 角色(ICL) | 冷峻高智 | ICL_uranus_zh_male_lengjungaozhi_tob | 中文 |
| 角色(ICL) | 冷峻上司 | ICL_uranus_zh_male_lengjunshangsi_tob | 中文 |
| 角色(ICL) | 冷酷哥哥 | ICL_uranus_zh_male_lengkugege_tob | 中文 |
| 角色(ICL) | 冷脸兄长 | ICL_uranus_zh_male_lenglianxiongzhang_tob | 中文 |
| 角色(ICL) | 冷脸学霸 | ICL_uranus_zh_male_lenglianxueba_tob | 中文 |
| 角色(ICL) | 冷漠男友 | ICL_uranus_zh_male_lengmonanyou_tob | 中文 |
| 角色(ICL) | 冷漠兄长 | ICL_uranus_zh_male_lengmoxiongzhang_tob | 中文 |
| 角色(ICL) | 凌云青年 | ICL_uranus_zh_male_lingyunqingnian_tob | 中文 |
| 角色(ICL) | 清冷矜贵 | ICL_uranus_zh_male_qinglengjingui_tob | 中文 |
| 角色(ICL) | 绿茶小哥 | ICL_uranus_zh_male_lvchaxiaoge_tob | 中文 |
| 角色(ICL) | 懵懂青年 | ICL_uranus_zh_male_mengdongqingnian_tob | 中文 |
| 角色(ICL) | 闷油瓶小哥 | ICL_uranus_zh_male_menyoupingxiaoge_tob | 中文 |
| 角色(ICL) | 嚣张小哥 | ICL_uranus_zh_male_xiaozhangxiaoge_tob | 中文 |
| 角色(ICL) | 粘人男友 | ICL_uranus_zh_male_nianrennanyou_tob | 中文 |
| 角色(ICL) | 暖心体贴 | ICL_uranus_zh_male_nuanxintitie_tob | 中文 |
| 角色(ICL) | 翩翩公子 | ICL_uranus_zh_male_pianpiangongzi_tob | 中文 |
| 角色(ICL) | 沉稳优雅 | ICL_uranus_zh_male_chenwenyouya_tob | 中文 |
| 角色(ICL) | 青涩小生 | ICL_uranus_zh_male_qingsexiaosheng_tob | 中文 |
| 角色(ICL) | 青涩青年 | ICL_uranus_zh_male_qingseqingnian_tob | 中文 |
| 角色(ICL) | 清爽少年 | ICL_uranus_zh_male_qingshuangshaonian_tob | 中文 |
| 角色(ICL) | 亲切青年 | ICL_uranus_zh_male_qinqieqingnian_tob | 中文 |
| 角色(ICL) | 清朗温润 | ICL_uranus_zh_male_qinglangwenrun_tob | 中文 |
| 角色(ICL) | 热血少年 | ICL_uranus_zh_male_rexueshaonian_tob | 中文 |
| 角色(ICL) | 儒雅才俊 | ICL_uranus_zh_male_ruyacaijun_tob | 中文 |
| 角色(ICL) | 儒雅君子 | ICL_uranus_zh_male_ruyajunzi_tob | 中文 |
| 角色(ICL) | 儒雅总裁 | ICL_uranus_zh_male_ruyazongcai_tob | 中文 |
| 角色(ICL) | 撒娇男生 | ICL_uranus_zh_male_sajiaonansheng_tob | 中文 |
| 角色(ICL) | 撒娇男友 | ICL_uranus_zh_male_sajiaonanyou_tob | 中文 |
| 角色(ICL) | 撒娇粘人 | ICL_uranus_zh_male_sajiaonianren_tob | 中文 |
| 角色(ICL) | 洒脱青年 | ICL_uranus_zh_male_satuoqingnian_tob | 中文 |
| 角色(ICL) | 少年将军 | ICL_uranus_zh_male_shaonianjiangjun_tob | 中文 |
| 角色(ICL) | 深沉总裁 | ICL_uranus_zh_male_shenchenzongcai_tob | 中文 |
| 角色(ICL) | 机灵小伙 | ICL_uranus_zh_male_jilingxiaohuo_tob | 中文 |
| 角色(ICL) | 神秘法师 | ICL_uranus_zh_male_shenmifashi_tob | 中文 |
| 角色(ICL) | 率真小伙 | ICL_uranus_zh_male_shuaizhenxiaohuo_tob | 中文 |
| 角色(ICL) | 低沉缱绻 | ICL_uranus_zh_male_dichenqianquan_tob | 中文 |
| 角色(ICL) | 斯文青年 | ICL_uranus_zh_male_siwenqingnian_tob | 中文 |
| 角色(ICL) | 甜系男友 | ICL_uranus_zh_male_tianxinanyou_tob | 中文 |
| 角色(ICL) | 贴心男友 | ICL_uranus_zh_male_tiexinnanyou_tob | 中文 |
| 角色(ICL) | 温柔男同桌 | ICL_uranus_zh_male_wenrounantongzhuo_tob | 中文 |
| 角色(ICL) | 温柔男友 | ICL_uranus_zh_male_wenrounanyou_tob | 中文 |
| 角色(ICL) | 温柔学长 | ICL_uranus_zh_male_wenrouxuezhang_tob | 中文 |
| 角色(ICL) | 温润学者 | ICL_uranus_zh_male_wenrunxuezhe_tob | 中文 |
| 角色(ICL) | 温顺少年 | ICL_uranus_zh_male_wenshunshaonian_tob | 中文 |
| 角色(ICL) | 寡言小哥 | ICL_uranus_zh_male_guayanxiaoge_tob | 中文 |
| 角色(ICL) | 小侯爷 | ICL_uranus_zh_male_xiaohouye_tob | 中文 |
| 角色(ICL) | 奶气小生 | ICL_uranus_zh_male_naiqixiaosheng_tob | 中文 |
| 角色(ICL) | 潇洒随性 | ICL_uranus_zh_male_xiaosasuixing_tob | 中文 |
| 角色(ICL) | 温柔内敛 | ICL_uranus_zh_male_wenrouneilian_tob | 中文 |
| 角色(ICL) | 学霸男同桌 | ICL_uranus_zh_male_xuebanantongzhuo_tob | 中文 |
| 角色(ICL) | 学霸同桌 | ICL_uranus_zh_male_xuebatongzhuo_tob | 中文 |
| 角色(ICL) | 意气少年 | ICL_uranus_zh_male_yiqishaonian_tob | 中文 |
| 角色(ICL) | 油腻大叔 | ICL_uranus_zh_male_younidashu_tob | 中文 |
| 角色(ICL) | 幽默大爷 | ICL_uranus_zh_male_youmodaye_tob | 中文 |
| 角色(ICL) | 幽默叔叔 | ICL_uranus_zh_male_youmoshushu_tob | 中文 |
| 角色(ICL) | 优柔帮主 | ICL_uranus_zh_male_youroubangzhu_tob | 中文 |
| 角色(ICL) | 优柔公子 | ICL_uranus_zh_male_yourougongzi_tob | 中文 |
| 角色(ICL) | 元气少年 | ICL_uranus_zh_male_yuanqishaonian_tob | 中文 |
| 角色(ICL) | 仗剑君子 | ICL_uranus_zh_male_zhangjianjunzi_tob | 中文 |
| 角色(ICL) | 仗剑侠客 | ICL_uranus_zh_male_zhangjianxiake_tob | 中文 |
| 角色(ICL) | 正直青年 | ICL_uranus_zh_male_zhengzhiqingnian_tob | 中文 |
| 角色(ICL) | 直率青年 | ICL_uranus_zh_male_zhishuaiqingnian_tob | 中文 |
| 角色(ICL) | 中二青年 | ICL_uranus_zh_male_zhongerqingnian_tob | 中文 |
| 角色(ICL) | 自负青年 | ICL_uranus_zh_male_zifuqingnian_tob | 中文 |
| 角色(ICL) | 自信青年 | ICL_uranus_zh_male_zixinqingnian_tob | 中文 |
| 角色(ICL) | 天才同桌 | ICL_uranus_zh_male_tiancaitongzhuo_tob | 中文 |
| 角色(ICL) | 爽朗少年 | ICL_uranus_zh_male_shuanglangshaonian_tob | 中文 |

## 1.0 常用音色（volc.service_type.10029，实测通过）

| 场景 | 音色名称 | voice_type |
|---|---|---|
| 情感男声 | 北京小爷 | zh_male_beijingxiaoye_emo_v2_mars_bigtts |
| 有声书 | 弯曲大树 | zh_female_wanqudashu_moon_bigtts |

> 1.0 完整列表见官方发音人文档；本表仅收实测款。1.0 情感音色支持 `--emotion`。
