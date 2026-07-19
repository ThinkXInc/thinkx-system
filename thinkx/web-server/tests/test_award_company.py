# web-server/tests/test_award_company.py
#
# 受賞企業ページ(/truetechjapan/<lang>/award/<company_key>)の検証。
# route_sweep はプレースホルダを 'x' に潰すため 404 しか観測できない。実在キーで
# 200 を引き、JSON の値が実際にページへ入ることをここで担保する。
# award_companies/ に JSON を1枚足せば、その企業も自動でこのテストの対象になる。

import json
import os

import pytest
from markupsafe import escape

_WEBSERVER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AWARD_COMPANIES_ROOT = os.path.join(
    _WEBSERVER, 'views/templates/truetechjapan/award_companies')


def _company_keys():
    return sorted(
        file_name[:-len('.json')]
        for file_name in os.listdir(AWARD_COMPANIES_ROOT)
        if file_name.endswith('.json')
    )


def _localized(value, lang):
    """本番 main.localize_award_company と同じフォールバック規則(訳が無ければ ja)。"""
    return value.get(lang) or value['ja']


def _as_rendered(text):
    """テンプレートが出力する形(Jinja のオートエスケープ後)に揃える。

    アポストロフィが &#39; になるため、生の JSON 値をそのまま部分一致に使えない。
    """
    return str(escape(text))


@pytest.fixture(scope='module')
def client():
    from main import app as flask_app
    flask_app.testing = False
    return flask_app.test_client()


def test_award_companies_exist():
    """1社も無い状態は設定ミス(このテスト自体が空回りする)。"""
    assert _company_keys()


@pytest.mark.parametrize('company_key', _company_keys())
@pytest.mark.parametrize('lang', ['ja', 'en'])
def test_award_company_page_renders(client, company_key, lang):
    with open(os.path.join(AWARD_COMPANIES_ROOT, f'{company_key}.json'),
              encoding='utf-8') as company_file:
        company = json.load(company_file)

    response = client.get(f'/truetechjapan/{lang}/award/{company_key}')
    assert response.status_code == 200

    html = response.data.decode('utf-8')
    assert _as_rendered(_localized(company['company_name'], lang)) in html
    assert company['url'] in html
    assert str(company['award_year']) in html
    assert company['logo']['src'] in html
    assert _as_rendered(_localized(company['business'], lang)) in html
    for founder in _localized(company['founders'], lang):
        assert _as_rendered(founder) in html
    for reason in _localized(company['award_reasons'], lang):
        assert _as_rendered(reason) in html

    # ティアは任意。未設定の企業ではチップごと出さない。
    if company['tier']:
        assert company['tier'] in html
    else:
        assert 'class="tier-chip"' not in html

    # インタビュー節は申込企業のみ。未申込(null)なら節ごと出さない。
    if company['interview_url']:
        assert company['interview_url'] in html
    else:
        assert 'class="award-section interview"' not in html


@pytest.mark.parametrize('company_key', _company_keys())
def test_untranslated_fields_fall_back_to_japanese(client, company_key):
    """英訳が未供給のフィールドは /en でも日本語が出る(空欄にしない)。"""
    with open(os.path.join(AWARD_COMPANIES_ROOT, f'{company_key}.json'),
              encoding='utf-8') as company_file:
        company = json.load(company_file)

    html = client.get(f'/truetechjapan/en/award/{company_key}').data.decode('utf-8')
    for field in ('company_name', 'business'):
        if not company[field].get('en'):
            assert _as_rendered(company[field]['ja']) in html
    if not company['founders'].get('en'):
        for founder in company['founders']['ja']:
            assert _as_rendered(founder) in html


def test_unknown_company_key_is_404(client):
    assert client.get('/truetechjapan/ja/award/no-such-company').status_code == 404
