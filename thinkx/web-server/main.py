import sys
import os
import re
import socket
import json
from os.path import abspath, join
from urllib.parse import quote
import atexit
from jinja2 import TemplateNotFound
from flask import abort, Flask, render_template, request, g, jsonify, url_for, redirect
from libcommon.discord import send_discord

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'DEFAULT_LANG',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

# Locale
from libcommon.language import Language
from libcommon.locale import Locale, COMMON_LOCALES_FILE_PATHS

# Set logger
from libcommon.logger import Logger
logger = Logger('main.py')
logger.setLevel(logger.DEBUG)
from libcommon.color import *
from libcommon.validator import Validator, ValidationType

# Web API tools
from libcommon.web.validation_errors import RequiredFieldsNotSatisfiedFormat
from libcommon.web.http_errors import InvalidContentTypeAPIErrorFormat, \
    UnexpectedAPIErrorFormat, ForbiddenAPIErrorFormat, ResourceNotFoundAPIErrorFormat, \
    BadRequestAPIErrorFormat, UnauthorizedAPIErrorFormat, RateLimitExceededAPIErrorFormat
from libcommon.web.http_successes import OKAPISuccessFormat, CreatedAPISuccessFormat, \
    AcceptedAPISuccessFormat
from flask_helper import language_wrapper, handle_error, LANG_NAME_MAP


# Local files
COMMON_LOCALES_ROOT = join(abspath(__file__), 'libcommon/locales')
LOCALES_ROOT = Config.LOCALES_ROOT
METADATA_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/page_metadata.json'
HEADER_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/header.json'
TOP_PAGE_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/top.json'
MESSAGE_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/message.json'
HISTORY_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/history.json'
ABOUT_PAGE_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/about.json'
VOICEOS_PAGE_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/products/voiceos.json'
LSH_PAGE_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/products/LSH.json'
APPLY_PAGES_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/apply.json'
INQUIRY_PAGES_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/inquiry_pages.json'
IR_PAGES_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/ir_pages.json'
ERROR_PAGES_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/error_pages.json'
locale = Locale([
    ERROR_PAGES_LOCALE_FILE_PATH,
    METADATA_LOCALE_FILE_PATH,
    HEADER_LOCALE_FILE_PATH,
])

## Page metadata
#PAGE_METADATA_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/page_metadata.json'
#def metadata(file_path, page_id, lang, default_page_id="home"):
#    try:
#        with open(fil_path, 'r', encoding='utf-8') as file:
#            metadata = json.load(file)
#            return metadata
#    except FileNotFoundError:
#        logger.error(red(f"The file {file_path} was not found."))
#        return {}
#    except json.JSONDecodeError:
#        logger.error(red("Error decoding JSON from the file."))
#        return {}

# Email
from mails.send_mail import (
    send_inquiry_confirm_email,
    MailSendError
)

# Initialize flask app
from init_flask_app import app

DEFAULT_LANG = Config.DEFAULT_LANG

# basic handlers
@app.route('/')
@app.route('/<lang>/')
@language_wrapper
def top_handler(lang, lang_name):
    logger.info(magenta(f'=> / [GET]'))
    locale.add_locale_file(TOP_PAGE_LOCALE_FILE_PATH)
    locale.add_locale_file(MESSAGE_LOCALE_FILE_PATH)
    return render_template(
        'index.html',
        page_id='home',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_home"][lang]
    )



# product page
@app.route('/products/Quantz-Voice-AI-OS')
@app.route('/<lang>/products/Quantz-Voice-AI-OS')
@language_wrapper
def products_voiceos_handler(lang, lang_name):
    logger.info(magenta(f'=> /products/Quantz-Voice-AI-OS [{request.method}]'))
    locale.add_locale_file(VOICEOS_PAGE_LOCALE_FILE_PATH)
    return render_template(
        '/products/voiceos.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_product_voiceos"][lang]
    )

# TODO:
@app.route('/products/CITYWALK')
@app.route('/<lang>/products/CITYWALK')
@language_wrapper
def products_citywalk_handler(lang, lang_name):
    logger.info(magenta(f'=> /products/CITYWALK [{request.method}]'))
    locale.add_locale_file(VOICEOS_PAGE_LOCALE_FILE_PATH)
    return render_template(
        '/products/citywalk.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_product_citywalk"][lang]
    )

# TODO:
@app.route('/products/LSH')
@app.route('/<lang>/products/LSH')
@language_wrapper
def products_lsh_handler(lang, lang_name):
    logger.info(magenta(f'=> /products/LSH [{request.method}]'))
    locale.add_locale_file(LSH_PAGE_LOCALE_FILE_PATH)
    return render_template(
        '/products/lsh.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_product_LSH"][lang]
    )


# mission
@app.route('/mission')
@app.route('/<lang>/mission')
@language_wrapper
def mission_handler(lang, lang_name):
    logger.info(magenta(f'=> /mission [{request.method}]'))
    locale.add_locale_file(MESSAGE_LOCALE_FILE_PATH)
    return render_template(
        '/about/mission.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_mission"][lang]
    )

# philosophy 
@app.route('/philosophy')
@app.route('/<lang>/philosophy')
@language_wrapper
def philosophy_handler(lang, lang_name):
    logger.info(magenta(f'=> /philosophy [{request.method}]'))
    locale.add_locale_file(MESSAGE_LOCALE_FILE_PATH)
    return render_template(
        '/about/philosophy.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_philosophy"][lang]
    )

# about us
@app.route('/about')
@app.route('/<lang>/about')
@language_wrapper
def about_handler(lang, lang_name):
    logger.info(magenta(f'=> /about [{request.method}]'))
    locale.add_locale_file(ABOUT_PAGE_LOCALE_FILE_PATH)
    return render_template(
        '/about/about.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_aboutus"][lang]
    )

@app.route('/history')
@app.route('/<lang>/history')
@language_wrapper
def history_handler(lang, lang_name):
    logger.info(magenta(f'=> /history [{request.method}]'))
    locale.add_locale_file(HISTORY_LOCALE_FILE_PATH)
    return render_template(
        '/about/history.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_history"][lang]
    )


# blog news
@app.route('/blognews')
@app.route('/<lang>/blognews')
@language_wrapper
def blognews_handler(lang, lang_name):
    logger.info(magenta(f'=> /blognews [{request.method}]'))
    page = request.args.get('page', default=1, type=int)  # Get 'page' from query parameters, default is 1

    template_name = f'/blognews/blogtop_p{page}_ja.html' if lang == "ja" else f"/blognews/blogtop_p{page}_en.html"

    is_last_page = True if page == 3 else False

    return render_template(
        template_name,
        page=page,
        is_last_page=is_last_page,
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_blognews"][lang]
    )

@app.route('/blognews/<news_id>')
@app.route('/<lang>/blognews/<news_id>')
@language_wrapper
def blognews_article_handler(lang, lang_name, news_id):
    logger.info(magenta(f'=> /blognews news_id: {news_id} [{request.method}]'))

    article_lang = 'ja' if lang == 'ja' else 'en'

    year = int(news_id[:4])
    month = int(news_id.split('-')[1])
    if len(news_id) >= 4 and news_id[:4].isdigit() and ((year >= 2024 and month >= 8) or (year >= 2025)):
        if news_id.endswith('talk'):
            html_path = f'blognews/talk.html'
        else:
            html_path = f'blognews/article.html'
        
        json_path = f'{LOCALES_ROOT}/articles/{news_id}.json'
        
        logger.info(cyan(f'html path {html_path}'))
        logger.info(cyan(f'json path {json_path}'))

        # Check if files exist
        json_exists = os.path.exists(json_path)
        
        if not json_exists:
            logger.error(red(f'{json_path} not exists.'))
            abort(404)
            
        locale.add_locale_file(json_path)
    else:
        html_path = f'blognews/articles/{article_lang}/{news_id}.html'
        logger.info(f'html path {html_path}')
        
    metadata_key = f"metadata_blog_{news_id}"
    metadata_default = locale.dict()["metadata_blognews"][lang]
    metadata = locale.dict()[metadata_key][lang] \
        if f"metadata_blog_{news_id}" in locale.dict() else metadata_default

    try:
        return render_template(
            html_path,
            lang=lang,
            lang_name=lang_name,
            locale_dict=locale.dict(),
            news_id=news_id,
            metadata=metadata
        )
    except TemplateNotFound:
        logger.error(red(f'{html_path} not exists.'))
        abort(404)

# apply
@app.route('/apply/regular')
@app.route('/<lang>/apply/regular')
@language_wrapper
def apply_regular_handler(lang, lang_name):
    logger.info(magenta(f'=> /apply/regular [{request.method}]'))
    locale.add_locale_file(APPLY_PAGES_LOCALE_FILE_PATH)
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/apply/apply_regular.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_apply_regular"][lang]
    )

@app.route('/apply/collaborator')
@app.route('/<lang>/apply/collaborator')
@language_wrapper
def apply_collaborator_handler(lang, lang_name):
    logger.info(magenta(f'=> /apply/collaborator [{request.method}]'))
    locale.add_locale_file(APPLY_PAGES_LOCALE_FILE_PATH)
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/apply/apply_collaborator.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_apply_collaborator"][lang]
    )

@app.route('/apply/intern')
@app.route('/<lang>/apply/intern')
@language_wrapper
def apply_intern_handler(lang, lang_name):
    logger.info(magenta(f'=> /apply/intern [{request.method}]'))
    locale.add_locale_file(APPLY_PAGES_LOCALE_FILE_PATH)
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/apply/apply_intern.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_apply_intern"][lang]
    )

# IR
@app.route('/ir/investor')
@app.route('/<lang>/ir/investor')
@language_wrapper
def ir_investor_handler(lang, lang_name):
    logger.info(magenta(f'=> /ir/investor [{request.method}]'))
    locale.add_locale_file(IR_PAGES_LOCALE_FILE_PATH)
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/ir/investor.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_ir_investor"][lang]
    )

# event page(独立ページ: 共通テンプレート・locale・多言語ルートに依存しない)
@app.route('/event/philsemi2609.html')
def event_philsemi2609_handler():
    logger.info(magenta(f'=> /event/philsemi2609.html [{request.method}]'))
    return render_template('/event/philsemi2609.html')

# inquiry
def _submit_handler(lang, source):
    """Common submission handler. source: 'inquiry' or 'apply'."""
    logger.info(magenta(f'=> /{source}/submit [POST]'))

    name = request.json['name']
    email = request.json['email']
    phone = request.json['phone']
    job_title = request.json['job_title']
    company_name = request.json['company_name']
    message = request.json['message']

    logger.info(name)
    logger.info(email)
    logger.info(phone)
    logger.info(job_title)
    logger.info(company_name)
    logger.info(message)

    # Discord通知: source ごとに webhook と表示を切り替え
    DISCORD_CONFIG = {
        'apply':   (Config.DISCORD_APPLY_WEBHOOK_URL,   'ThinkX Apply',   '📝 **新規応募**'),
        'inquiry': (Config.DISCORD_INQUIRY_WEBHOOK_URL, 'ThinkX Inquiry', '📩 **新規問い合わせ**'),
    }
    webhook_url, username, header = DISCORD_CONFIG.get(source, (None, None, None))

    logger.info(cyan(f'[discord] source={source}, webhook_set={bool(webhook_url)}'))

    if webhook_url:
        try:
            truncated = message if len(message) <= 1500 else message[:1500] + '…(truncated)'
            content = (
                f"{header} [{lang}]\n"
                f"**氏名**: {name}\n"
                f"**メール**: {email}\n"
                f"**電話**: {phone or '-'}\n"
                f"**役職**: {job_title or '-'}\n"
                f"**会社**: {company_name or '-'}\n"
                f"---\n{truncated}"
            )
            logger.info(cyan(f'[discord] sending to {username} (content {len(content)} chars)'))
            send_discord(webhook_url, username, content)
            logger.info(green(f'[discord] sent successfully to {username}'))
        except Exception as e:
            logger.error(red(f'[discord] notify failed: {e}'))
    else:
        logger.warn(yellow(f'[discord] skipped: source={source}, webhook URL not configured'))

    try:
        send_inquiry_confirm_email(
            lang, name, email, phone, job_title, company_name, message)
    except MailSendError as e:
        logger.error(red(str(e)))
    except Exception as e:
        logger.error(red(str(e)))
        return json.dumps({'success': False, 'error': '{0}'.format(e)}), 500
    else:
        return json.dumps({'success': True}), 200

@app.route('/inquiry/product')
@app.route('/<lang>/inquiry/product')
@language_wrapper
def inquiry_product_handler(lang, lang_name):
    logger.info(magenta(f'=> /inquiry/product [{request.method}]'))
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/inquiry/inquiry_product.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_inquiry_product"][lang]
    )

@app.route('/inquiry/collaboration')
@app.route('/<lang>/inquiry/collaboration')
@language_wrapper
def inquiry_collaboration_handler(lang, lang_name):
    logger.info(magenta(f'=> /inquiry/collaboration [{request.method}]'))
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/inquiry/inquiry_collaboration.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_inquiry_collaboration"][lang]
    )

@app.route('/inquiry/others')
@app.route('/<lang>/inquiry/others')
@language_wrapper
def inquiry_others_handler(lang, lang_name):
    logger.info(magenta(f'=> /inquiry/others [{request.method}]'))
    locale.add_locale_file(INQUIRY_PAGES_LOCALE_FILE_PATH)
    return render_template(
        '/inquiry/inquiry_others.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_inquiry_others"][lang]
    )

@app.route('/inquiry/submit', methods=['POST'])
@app.route('/<lang>/inquiry/submit', methods=['POST'])
@language_wrapper
def inquiry_submit_handler(lang, lang_name):
    logger.info(magenta(f'=> /inquiry/submit [{request.method}]'))
    return _submit_handler(lang, source='inquiry')

@app.route('/apply/submit', methods=['POST'])
@app.route('/<lang>/apply/submit', methods=['POST'])
@language_wrapper
def apply_submit_handler(lang, lang_name):
    logger.info(magenta(f'=> /apply/submit [{request.method}]'))
    return _submit_handler(lang, source='apply')

# TODO: blueprint
#################### NNTM
@app.route("/nntm/")
@app.route("/nntm/<lang>/")
@language_wrapper
def nntm_index(lang, lang_name):
    logger.info(magenta(f'=> /nntm [GET] (lang: {lang})'))
    locale.add_locale_file(f'{LOCALES_ROOT}/NNTM/top.json')
    locale.add_locale_file(f'{LOCALES_ROOT}/NNTM/metadata.json')
    return render_template(
        '/NNTM/top.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_top"][lang]
    )

@app.route("/nntm/blog/<blog_id>")
@app.route("/nntm/<lang>/blog/<blog_id>")
@language_wrapper
def nntm_blog(lang, lang_name, blog_id):
    logger.info(magenta(f'=> /nntm/{lang}/{blog_id}/ [GET] (lang: {lang})'))
    locale.add_locale_file(f'{LOCALES_ROOT}/NNTM/top.json')
    locale.add_locale_file(f'{LOCALES_ROOT}/NNTM/blog/{blog_id}.json')
    return render_template(
        '/NNTM/blog.html',
        lang=lang,
        lang_name=lang_name,
        blog_id=blog_id,
        locale_dict=locale.dict(),
        metadata=locale.dict()[f"metadata_blog_{blog_id}"][lang]
    )



@app.route("/nntm/privacy_policy/")
@app.route("/nntm/<lang>/privacy_policy/")
@language_wrapper
def nntm_privacy(lang, lang_name):
    logger.info(magenta(f'=> /nntm/{lang}/privacy_policy/ [GET] (lang: {lang})'))
    locale.add_locale_file(f'{LOCALES_ROOT}/NNTM/privacy_policy.json')
    locale.add_locale_file(f'{LOCALES_ROOT}/NNTM/metadata.json')
    return render_template(
        '/NNTM/privacy_policy.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_privacy"][lang]
    )

@app.route("/nntm/conversion_redirect/")
def nntm_conversion_redirect():
    logger.info(magenta(f'=> /nntm/conversion_redirect [GET])'))
    return render_template(
        '/NNTM/conversion_redirect.html'
    )


####################  True Tech

from functools import wraps

def truetech_lang(func):
    @wraps(func)
    def wrapper(lang=None, *args, **kwargs):
        lang = lang if lang in ["en", "ja"] else "ja"
        lang_name = LANG_NAME_MAP.get(lang, LANG_NAME_MAP["ja"])
        return func(lang=lang, lang_name=lang_name, *args, **kwargs)
    return wrapper

def truetech_locale(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        locale = Locale([
            ERROR_PAGES_LOCALE_FILE_PATH,
            f'{LOCALES_ROOT}/truetechjapan/metadata.json',
            f'{LOCALES_ROOT}/truetechjapan/common.json',
        ])
        return func(locale=locale, *args, **kwargs)
    return wrapper


# 受賞企業データ。1企業 = 1 JSON、ファイル名(拡張子なし)がそのまま URL キーになる。
AWARD_COMPANIES_ROOT = join(Config.SRC_ROOT, 'views/templates/truetechjapan/award_companies')
AWARD_COMPANY_KEY_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]*$')


# 企業固有の値のうち多言語で持つフィールド。JSON では {"ja": ..., "en": ...} 形式。
# tier / url / award_year / logo は言語に依らないので対象外。
LOCALIZED_AWARD_COMPANY_FIELDS = ('company_name', 'founders', 'business', 'award_reasons')


def load_award_company(company_key):
    """受賞企業 JSON を読んで返す。キーが不正、または未登録なら None。"""
    if not AWARD_COMPANY_KEY_PATTERN.match(company_key):
        return None
    company_file_path = join(AWARD_COMPANIES_ROOT, f'{company_key}.json')
    if not os.path.isfile(company_file_path):
        return None
    with open(company_file_path, encoding='utf-8') as company_file:
        return json.load(company_file)


def localize_award_company(company, lang):
    """多言語フィールドを lang の値に潰した dict を返す。

    訳が未供給の言語は ja へフォールバックする。企業から訳が届く前でも
    ページを落とさないため(空文字も未供給として扱う)。
    """
    localized_company = dict(company)
    for field in LOCALIZED_AWARD_COMPANY_FIELDS:
        localized_company[field] = company[field].get(lang) or company[field]['ja']
    return localized_company


@app.route("/truetechjapan/")
@app.route("/truetechjapan/<lang>/")
@truetech_lang
@truetech_locale
def truetechjapan_top(locale, lang=None, lang_name=None):
    logger.info(magenta(f'=> /truetechjapan [GET] (lang: {lang})'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/top.json')
    
    return render_template(
        '/truetechjapan/top.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_top"][lang]
    )

@app.route("/truetechjapan/about")
@app.route("/truetechjapan/<lang>/about")
@truetech_lang
@truetech_locale
def truetechjapan_about(locale, lang=None, lang_name=None):
    logger.info(magenta(f'=> /truetechjapan/about [GET] (lang: {lang})'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/about.json')

    return render_template(
        '/truetechjapan/about.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_about"][lang]
    )

@app.route("/truetechjapan/philosophy")
@app.route("/truetechjapan/<lang>/philosophy")
@truetech_lang
@truetech_locale
def truetechjapan_philosophy(locale, lang=None, lang_name=None):
    logger.info(magenta(f'=> /truetechjapan/philosophy [GET] (lang: {lang})'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/philosophy.json')
    
    return render_template(
        '/truetechjapan/philosophy.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_philosophy"][lang]
    )

@app.route("/truetechjapan/organization")
@app.route("/truetechjapan/<lang>/organization")
@truetech_lang
@truetech_locale
def truetechjapan_organization(locale, lang=None, lang_name=None):
    logger.info(magenta(f'=> /truetechjapan/organization [GET] (lang: {lang})'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/organization.json')
    
    return render_template(
        '/truetechjapan/organization.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_organization"][lang]
    )

@app.route("/truetechjapan/privacy")
@app.route("/truetechjapan/<lang>/privacy")
@truetech_lang
@truetech_locale
def truetechjapan_privacy(locale, lang=None, lang_name=None):
    logger.info(magenta(f'=> /truetechjapan/privacy [GET] (lang: {lang})'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/privacy.json')
    
    return render_template(
        '/truetechjapan/privacy.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_privacy"][lang]
    )

@app.route("/truetechjapan/award/<company_key>")
@app.route("/truetechjapan/<lang>/award/<company_key>")
@truetech_lang
@truetech_locale
def truetechjapan_award_company(locale, company_key, lang=None, lang_name=None):
    logger.info(magenta(f'=> /truetechjapan/award/{company_key} [GET] (lang: {lang})'))

    company = load_award_company(company_key)
    if company is None:
        abort(404)
    company = localize_award_company(company, lang)

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/award_company.json')

    metadata = dict(locale.dict()["metadata_award_company"][lang])
    metadata["title"] = f'{company["company_name"]} | {metadata["title"]}'

    # SNS シェア用 OGP を企業ごとに設定する。base.html は og_* が無ければサイト
    # 共通値へフォールバックするので、この上書きを受けるのは award ページだけ。
    public_base = "https://truetechjapan.com"
    summary = company["business"]
    if len(summary) > 110:
        summary = summary[:110].rstrip() + "…"
    metadata["description"] = summary
    metadata["og_title"] = metadata["title"]
    metadata["og_description"] = summary
    metadata["og_url"] = f'{public_base}/{lang}/award/{company_key}'
    metadata["og_image"] = f'{public_base}/img/truetechjapan/award_companies/ogp/{company_key}.png'
    metadata["twitter_card"] = "summary_large_image"

    return render_template(
        '/truetechjapan/award_company_page.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=metadata,
        company=company
    )

@app.route('/truetechjapan/entry')
@app.route('/truetechjapan/<lang>/entry')
@truetech_lang
@truetech_locale
def truetechjapan_entry_handler(locale, lang, lang_name):
    logger.info(magenta(f'=> /truetechjapan/entry [{request.method}]'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/entry.json')

    return render_template(
        '/truetechjapan/entry.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_entry"][lang]
    )

@app.route('/truetechjapan/inquiry')
@app.route('/truetechjapan/<lang>/inquiry')
@truetech_lang
@truetech_locale
def truetechjapan_inquiry_handler(locale, lang, lang_name):
    logger.info(magenta(f'=> /truetechjapan/inquiry [{request.method}]'))

    locale.add_locale_file(f'{LOCALES_ROOT}/truetechjapan/inquiry.json')

    return render_template(
        '/truetechjapan/inquiry.html',
        lang=lang,
        lang_name=lang_name,
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_inquiry"][lang]
    )



@app.route('/truetechjapan/inquiry/submit', methods=['POST'])
@app.route('/truetechjapan/<lang>/inquiry/submit', methods=['POST'])
@language_wrapper
def truetechjapan_inquiry_submit_handler(lang, lang_name):
    logger.info(magenta(f'=> /truetechjapan/inquiry/submit [{request.method}]'))
    name = request.json['name']
    email = request.json['email']
    phone = request.json['phone']
    job_title = request.json['job_title']
    company_name = request.json['company_name']
    message = request.json['message']

    logger.info(name)
    logger.info(email)
    logger.info(phone)
    logger.info(job_title)
    logger.info(company_name)
    logger.info(message)

    try:
        send_inquiry_confirm_email(
            lang, name, email, phone, job_title, company_name, message)
    except MailSendError as e:
        logger.error(red(str(e)))
    except Exception as e:
        logger.error(red(str(e)))
        return json.dumps({'success': False, 'error': '{0}'.format(e)}), 500
    else:
        return json.dumps({'success': True}), 200



@app.errorhandler(400)
@language_wrapper
def bad_request(error, lang, lang_name):
    return handle_error(error, BadRequestAPIErrorFormat, lang)

@app.errorhandler(404)
@language_wrapper
def page_not_found(error, lang, lang_name):
    logger.error(red(f"404 Page Not Found: {request.url}"))
    return render_template(
        '/errors/404.html',
        message=locale.get("404", lang),
        locale_dict=locale.dict(),
        metadata=locale.dict()["metadata_home"][lang]
        ), 404

@app.errorhandler(500)
@language_wrapper
def internal_server_error(error, lang, lang_name):
    return handle_error(error, UnexpectedAPIErrorFormat, lang)

@app.errorhandler(502)
@language_wrapper
def bad_gateway(error, lang, lang_name):
    return handle_error(error, RateLimitExceededAPIErrorFormat, lang)

#################### filedrop (staging 専用の素材受け取り)
# 判定は .env でなくホスト名(D-46: staging の hostname は -stg 接尾辞)。
# staging の .env も ENV=production で動いているため Config.ENV では区別できない
FILEDROP_DIR = '/src/thinkx-system/Downloads'

@app.route('/filedrop', methods=['GET', 'POST'])
def filedrop_handler():
    logger.info(magenta(f'=> /filedrop [{request.method}]'))
    if not socket.gethostname().endswith('-stg'):
        abort(404)
    os.makedirs(FILEDROP_DIR, exist_ok=True)
    if request.method == 'POST':
        saved = 0
        for f in request.files.getlist('file'):
            if not f or not f.filename:
                continue
            name = os.path.basename(f.filename).replace('/', '_').replace('\\', '_').strip()
            if name:
                f.save(os.path.join(FILEDROP_DIR, name))
                saved += 1
        logger.info(f'filedrop: saved {saved} file(s)')
        return redirect('/filedrop')
    files = sorted(
        (e for e in os.scandir(FILEDROP_DIR) if e.is_file()),
        key=lambda e: e.stat().st_mtime, reverse=True)
    return render_template(
        '/filedrop.html',
        files=[{'name': e.name, 'kb': max(1, e.stat().st_size // 1024)} for e in files],
    )


# Register a function to run after the app closes
@atexit.register
def cleanup():
    print("Cleaning up resources...")
    #if connection_pool:
    #    connection_pool.close_all()

if __name__ == '__main__':
    app.run(
        debug=True,
    )