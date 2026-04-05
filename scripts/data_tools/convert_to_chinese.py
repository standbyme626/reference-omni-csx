"""
Olist 数据集中文转换脚本
将葡萄牙语数据转换为中文
"""
import os
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_DATA_OLIST",
        str(REPO_ROOT / "data" / "raw" / "olist"),
    )
)
OUTPUT_DIR = Path(
    os.getenv(
        "PLATFORM_SIM_DATA_OLIST_CN",
        str(REPO_ROOT / "data" / "processed" / "olist_cn"),
    )
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_CATEGORY_CN = {
    "health_beauty": "健康美容",
    "computers_accessories": "电脑配件",
    "auto": "汽车用品",
    "bed_bath_table": "床浴桌布",
    "furniture_decor": "家具装饰",
    "sports_leisure": "运动休闲",
    "housewares": "家居用品",
    "watches_gifts": "手表礼品",
    "telephony": "电话通讯",
    "garden_tools": "园艺工具",
    "toys": "玩具",
    "cool_stuff": "创意商品",
    "perfumery": "香水",
    "baby": "母婴用品",
    "electronics": "电子产品",
    "stationery": "文具",
    "fashion_bags_accessories": "时尚箱包",
    "pet_shop": "宠物用品",
    "office_furniture": "办公家具",
    "consoles_games": "游戏机",
    "luggage_accessories": "行李箱包",
    "construction_tools_construction": "建筑工具",
    "audio": "音响设备",
    "small_appliances": "小家电",
    "fashion_shoes": "时尚鞋履",
    "air_conditioning": "空调",
    "fashion_underwear_beach": "时尚内衣泳装",
    "kitchen_dining_laundry_garden_furniture": "厨房餐厅家具",
    "costruction_tools_tools": "建筑工具",
    "fashion_male_clothing": "男装",
    "furniture_living_room": "客厅家具",
    "costruction_tools_garden": "园艺工具",
    "fashion_sport": "运动服饰",
    "market_place": "市场",
    "home_appliances": "家用电器",
    "home_comfort": "家居舒适",
    "small_appliances_home_oven_and_coffee": "小家电烤箱咖啡机",
    "cds_dvds_musicals": "CD DVD音乐",
    "fashion_childrens_clothes": "童装",
    "la_cuisine": "厨房用品",
    "music": "音乐",
    "home_comfort_2": "家居舒适",
    "books_general_interest": "大众读物",
    "construction_tools_safety": "安全工具",
    "furniture_bedroom": "卧室家具",
    "home_appliances_2": "家用电器",
    "books_technical": "技术书籍",
    "signaling_and_security": "信号安全",
    "christmas_supplies": "圣诞用品",
    "furniture_mattress_and_upholstery": "床垫家具",
    "party_supplies": "派对用品",
    "tablets_printing_image": "平板打印",
    "arts_and_craftmanship": "工艺品",
    "cine_photo": "电影摄影",
    "dvds_blu_ray": "DVD蓝光",
    "books_imported": "进口书籍",
    "flowers": "鲜花",
    "food_drink": "食品饮料",
    "drinks": "饮料",
    "agro_industry_and_commerce": "农工商",
    "industry_commerce_and_business": "工商业",
    "security_and_services": "安全服务",
    "fixed_telephony": "固定电话",
    "diapers_and_hygiene": "纸尿裤卫生用品",
    "fashio_female_clothing": "女装",
    "home_construction": "家装建材",
    "audio": "音响",
    "food": "食品",
    "art": "艺术",
    "fashio_female_clothing": "女装",
    "portateis_cozinha_e_preparadores_de_alimentos": "便携厨房设备",
    "pcs": "电脑",
    "esporte_lazer": "运动休闲",
    "perfumaria": "香水",
    "artes": "艺术",
    "bebes": "婴儿用品",
    "moveis_decoracao": "家具装饰",
    "utilidades_domesticas": "家居用品",
    "brinquedos": "玩具",
    "relogios_presentes": "手表礼品",
    "beleza_saude": "美容健康",
    "informatica_acessorios": "电脑配件",
    "automotivo": "汽车用品",
    "cama_mesa_banho": "床浴桌布",
    "moveis_escritorio": "办公家具",
    "instrumentos_musicais": "乐器",
    "consoles_games": "游戏机",
    "cool_stuff": "创意商品",
    "malas_acessorios": "行李箱包",
    "climatizacao": "空调",
    "telefonia": "电话",
    "eletronicos": "电子产品",
    "eletrodomesticos": "家用电器",
    "fashion_bolsas_e_acessorios": "时尚箱包",
    "papelaria": "文具",
    "ferramentas_jardim": "园艺工具",
    "pet_shop": "宠物用品",
    "moveis_sala": "客厅家具",
    "sinalizacao_e_seguranca": "信号安全",
    "eletroportateis": "小家电",
    "casa_conforto": "家居舒适",
    "construcao_ferramentas_construcao": "建筑工具",
    "moveis_quarto": "卧室家具",
    "livros_interesse_geral": "大众读物",
    "construcao_ferramentas_jardim": "园艺工具",
    "fashion_calcados": "时尚鞋履",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "厨房餐厅家具",
    "industria_comercio_e_negocios": "工商业",
    "agro_industria_e_comercio": "农工商",
    "bebidas": "饮料",
    "alimentos": "食品",
    "artes_e_oficios": "工艺品",
    "pcs": "电脑",
    "tablets_impressao_imagem": "平板打印",
    "fashion_roupa_masculina": "男装",
    "fashion_roupa_feminina": "女装",
    "fashion_roupa_infanto_juvenil": "童装",
    "fashion_esporte": "运动服饰",
    "fashion_underwear_e_moda_praia": "时尚内衣泳装",
    "livros_tecnicos": "技术书籍",
    "construcao_ferramentas_ferramentas": "建筑工具",
    "construcao_ferramentas_seguranca": "安全工具",
    "seguros_e_servicos": "安全服务",
    "cds_dvds_musicais": "CD DVD音乐",
    "dvds_blu_ray": "DVD蓝光",
    "musica": "音乐",
    "cine_foto": "电影摄影",
    "livros_importados": "进口书籍",
    "flores": "鲜花",
    "artigos_de_natal": "圣诞用品",
    "artigos_de_festas": "派对用品",
    "fraldas_higiene": "纸尿裤卫生用品",
    "la_cuisine": "厨房用品",
    "casa_conforto_2": "家居舒适",
    "portateis_casa_forno_e_cafe": "便携厨房设备",
    "eletrodomesticos_2": "家用电器",
}

STATE_CN = {
    "SP": "圣保罗州",
    "RJ": "里约热内卢州",
    "MG": "米纳斯吉拉斯州",
    "RS": "南里奥格兰德州",
    "PR": "巴拉那州",
    "SC": "圣卡塔琳娜州",
    "BA": "巴伊亚州",
    "GO": "戈亚斯州",
    "PE": "伯南布哥州",
    "DF": "联邦区",
    "ES": "圣埃斯皮里图州",
    "CE": "塞阿拉州",
    "PA": "帕拉州",
    "MT": "马托格罗索州",
    "MA": "马拉尼昂州",
    "AM": "亚马逊州",
    "RN": "北里奥格兰德州",
    "PB": "帕拉伊巴州",
    "AL": "阿拉戈斯州",
    "PI": "皮奥伊州",
    "RO": "朗多尼亚州",
    "SE": "塞尔希培州",
    "TO": "托坎廷斯州",
    "AC": "阿克里州",
    "AP": "阿马帕州",
    "RR": "罗赖马州",
}

CITY_CN = {
    "sao paulo": "圣保罗",
    "rio de janeiro": "里约热内卢",
    "belo horizonte": "贝洛奥里藏特",
    "brasilia": "巴西利亚",
    "curitiba": "库里蒂巴",
    "porto alegre": "阿雷格里港",
    "salvador": "萨尔瓦多",
    "fortaleza": "福塔莱萨",
    "recife": "累西腓",
    "manaus": "马瑙斯",
    "belem": "贝伦",
    "goiania": "戈亚尼亚",
    "guarulhos": "瓜鲁柳斯",
    "campinas": "坎皮纳斯",
    "sao luis": "圣路易斯",
    "sao goncalo": "圣贡萨洛",
    "maceio": "马塞约",
    "natal": "纳塔尔",
    "teresina": "特雷西纳",
    "campo grande": "大坎普",
    "joao pessoa": "若昂佩索阿",
    "cuiaba": "库亚巴",
    "aracaju": "阿拉卡茹",
    "florianopolis": "弗洛里亚诺波利斯",
    "itapevi": "伊塔佩维",
    "jundiai": "容迪亚伊",
    "ribeirao preto": "里贝朗普雷图",
    "uberlandia": "乌贝兰迪亚",
    "sorocaba": "索罗卡巴",
    "osasco": "奥萨斯库",
    "santos": "桑托斯",
    "franca": "弗兰卡",
    "sao bernardo do campo": "圣贝尔纳多-杜坎普",
    "mogi das cruzes": "莫日达斯克鲁济斯",
    "diadema": "迪亚德马",
    "carapicuiba": "卡拉皮库伊巴",
    "maua": "毛阿",
    "santo andre": "圣安德烈",
    "sao jose dos campos": "圣若泽杜斯坎普斯",
    "taboao da serra": "塔博昂达塞拉",
    "embu das artes": "恩布达斯阿尔特斯",
    "barueri": "巴鲁埃里",
    "sao vicente": "圣维森特",
    "itaquaquecetuba": "伊塔夸克塞图巴",
    "praia grande": "大海滩",
    "guaruja": "瓜鲁雅",
    "taubate": "陶巴特",
    "bauru": "包鲁",
    "jacarei": "雅卡雷伊",
    "marilia": "马里利亚",
    "sumare": "苏马雷",
    "presidente prudente": "普鲁登特总统城",
    "sao jose do rio preto": "圣若泽杜里奥普雷图",
    "londrina": "隆德里纳",
    "ponta grossa": "蓬塔格罗萨",
    "cascavel": "卡斯卡韦尔",
    "foz do iguacu": "伊瓜苏",
    "colombo": "科伦坡",
    "maringa": "马林加",
    "sao jose dos pinhais": "圣若泽多斯皮尼艾斯",
    "caxias do sul": "南卡西亚斯",
    "pelotas": "佩洛塔斯",
    "canoas": "卡诺阿斯",
    "santa maria": "圣玛丽亚",
    "vitoria": "维多利亚",
    "vila velha": "维拉韦利亚",
    "cariacica": "卡里亚西卡",
    "serra": "塞拉",
    "niteroi": "尼泰罗伊",
    "nova iguacu": "新伊瓜苏",
    "duque de caxias": "迪克卡西亚斯",
    "sao goncalo": "圣贡萨洛",
    "belford roxo": "贝尔福德罗舒",
    "petropolis": "彼得罗波利斯",
    "volta redonda": "沃尔塔雷东达",
    "macae": "马卡埃",
    "campos dos goytacazes": "戈伊塔卡泽斯坎普斯",
    "cabo frio": "卡布弗里乌",
    "teresopolis": "特雷索波利斯",
    "resende": "雷森迪",
    "barra mansa": "巴拉曼萨",
    "ananindeua": "阿南因德瓦",
    "abreu e lima": "阿布雷乌利马",
    "olinda": "奥林达",
    "jaboatao dos guararapes": "雅博阿唐多斯瓜拉拉皮斯",
    "paulista": "保利斯塔",
    "cabo de santo agostinho": "圣阿戈斯蒂纽角",
    "camaragibe": "卡马拉吉比",
    "garanhuns": "加拉纽斯",
    "caruaru": "卡鲁阿鲁",
    "vitoria de santo antao": "圣安东尼奥维多利亚",
    "petrolina": "彼得罗利纳",
    "aracaju": "阿拉卡茹",
    "nossa senhora do socorro": "圣母苏科罗",
    "lages": "拉热斯",
    "itajai": "伊塔雅伊",
    "balneario camboriu": "巴尔内阿里奥坎博里乌",
    "chapeco": "沙佩科",
    "blumenau": "布卢梅瑙",
    "joinville": "若因维利",
    "sao jose": "圣若泽",
    "criciuma": "克里西乌马",
    "tubarao": "图巴朗",
    "itapema": "伊塔佩马",
    "brusque": "布鲁斯基",
    "rio branco": "里奥布兰库",
    "manaus": "马瑙斯",
    "boa vista": "博阿维斯塔",
    "macapa": "马卡帕",
    "port velho": "波多韦柳",
    "rio branco": "里奥布兰库",
    "palmas": "帕尔马斯",
    "araguaina": "阿拉瓜伊纳",
    "gurupi": "古鲁皮",
    "porto nacional": "国家港",
    "belem": "贝伦",
    "ananindeua": "阿南因德瓦",
    "maraba": "马拉巴",
    "parauepebas": "帕拉韦佩巴斯",
    "castanhal": "卡斯坦阿尔",
    "abaetetuba": "阿巴埃特图巴",
    "cuiaba": "库亚巴",
    "varzea grande": "大瓦尔泽亚",
    "rondonopolis": "龙多诺波利斯",
    "sinop": "西诺普",
    "tangara da serra": "塞拉坦加拉",
    "barra do garcas": "加萨斯港",
    "goiania": "戈亚尼亚",
    "aparecida de goiania": "阿帕雷西达-迪戈亚尼亚",
    "anapolis": "阿纳波利斯",
    "rio verde": "里奥韦尔迪",
    "luziania": "卢齐亚尼亚",
    "aguas lindas de goias": "戈亚斯美丽水域",
    "trindade": "特林达迪",
    "formosa": "福尔摩沙",
    "itumbiara": "伊图姆比亚拉",
    "senador canedo": "卡内多参议员城",
    "catalao": "卡塔劳",
    "jatai": "雅塔伊",
    "planaltina": "普拉纳尔蒂纳",
    "caldas novas": "新卡尔达斯",
    "brasilia": "巴西利亚",
    "ceilandia": "塞兰迪亚",
    "taguatinga": "塔古阿廷加",
    "samambaia": "萨曼拜亚",
    "planaltina": "普拉纳尔蒂纳",
    "nucleo bandeirante": "先锋核心",
    "guara": "瓜拉",
    "sobradinho": "索布拉迪纽",
    "gama": "加马",
    "santa maria": "圣玛丽亚",
    "recanto das emas": "艾马斯角落",
    "sao sebastiao": "圣塞巴斯蒂昂",
    "paranoa": "帕拉诺阿",
    "brazlandia": "布拉兹兰迪亚",
    "riacho fundo": "丰杜溪",
    "vicente pires": "维森特皮雷斯",
    "estrutural": "埃斯特鲁图拉尔",
    "sudoeste octogonal": "西南八角",
    "aguas claras": "清水",
    "varjao": "瓦尔雅翁",
    "park way": "公园路",
    "scia": "斯科亚",
    "arniqueira": "阿尼凯拉",
    "jardim botanico": "植物园",
    "itapoa": "伊塔波阿",
    "cruzeiro": "克鲁塞罗",
    "lago sul": "南湖",
    "lago norte": "北湖",
}

ORDER_STATUS_CN = {
    "delivered": "已送达",
    "shipped": "已发货",
    "canceled": "已取消",
    "invoiced": "已开票",
    "processing": "处理中",
    "created": "已创建",
    "approved": "已批准",
    "unavailable": "不可用",
}

PAYMENT_TYPE_CN = {
    "credit_card": "信用卡",
    "boleto": "银行汇票",
    "voucher": "代金券",
    "debit_card": "借记卡",
    "not_defined": "未定义",
}


def translate_city(city: str) -> str:
    if pd.isna(city):
        return city
    city_lower = str(city).lower().strip()
    return CITY_CN.get(city_lower, city)


def translate_category(cat: str) -> str:
    if pd.isna(cat):
        return cat
    cat_lower = str(cat).lower().strip()
    return PRODUCT_CATEGORY_CN.get(cat_lower, PRODUCT_CATEGORY_CN.get(cat, cat))


def convert_customers():
    print("转换客户数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset.csv")
    df["customer_city"] = df["customer_city"].apply(translate_city)
    df["customer_state"] = df["customer_state"].map(STATE_CN).fillna(df["customer_state"])
    df.to_csv(f"{OUTPUT_DIR}/olist_customers_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_orders():
    print("转换订单数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv")
    df["order_status"] = df["order_status"].map(ORDER_STATUS_CN).fillna(df["order_status"])
    df.to_csv(f"{OUTPUT_DIR}/olist_orders_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_order_items():
    print("转换订单明细数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset.csv")
    df.to_csv(f"{OUTPUT_DIR}/olist_order_items_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_products():
    print("转换产品数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_products_dataset.csv")
    df["product_category_name"] = df["product_category_name"].apply(translate_category)
    df.to_csv(f"{OUTPUT_DIR}/olist_products_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_sellers():
    print("转换卖家数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_sellers_dataset.csv")
    df["seller_city"] = df["seller_city"].apply(translate_city)
    df["seller_state"] = df["seller_state"].map(STATE_CN).fillna(df["seller_state"])
    df.to_csv(f"{OUTPUT_DIR}/olist_sellers_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_payments():
    print("转换支付数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset.csv")
    df["payment_type"] = df["payment_type"].map(PAYMENT_TYPE_CN).fillna(df["payment_type"])
    df.to_csv(f"{OUTPUT_DIR}/olist_order_payments_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_reviews():
    print("转换评价数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_order_reviews_dataset.csv")
    df.to_csv(f"{OUTPUT_DIR}/olist_order_reviews_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def convert_geolocation():
    print("转换地理位置数据...")
    df = pd.read_csv(f"{DATA_DIR}/olist_geolocation_dataset.csv")
    df["geolocation_city"] = df["geolocation_city"].apply(translate_city)
    df["geolocation_state"] = df["geolocation_state"].map(STATE_CN).fillna(df["geolocation_state"])
    df.to_csv(f"{OUTPUT_DIR}/olist_geolocation_dataset_cn.csv", index=False, encoding="utf-8-sig")
    print(f"  完成: {len(df)} 条记录")
    return df


def main():
    print("=" * 50)
    print("Olist 数据集中文转换")
    print("=" * 50)
    
    convert_customers()
    convert_orders()
    convert_order_items()
    convert_products()
    convert_sellers()
    convert_payments()
    convert_reviews()
    convert_geolocation()
    
    print("\n" + "=" * 50)
    print(f"转换完成！输出目录: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
