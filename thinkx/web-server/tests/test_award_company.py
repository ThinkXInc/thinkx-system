# web-server/tests/test_award_company.py
#
# 受賞企業ページ(/truetechjapan/<lang>/award/<company_key>)の検証。
# route_sweep はプレースホルダを 'x' に潰すため 404 しか観測できない。実在キーで
# 200 を引き、JSON の値が実際にページへ入ることをここで担保する。
# award_companies/ に JSON を1枚足せば、その企業も自動でこのテストの対象になる。

import json
import os

import pytest

_WEBSERVER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AWARD_COMPANIES_ROOT = os.path.join(
    _WEBSERVER, 'views/templates/truetechjapan/award_companies')


def _company_keys():
    return sorted(
        file_name[:-len('.json')]
        for file_name in os.listdir(AWARD_COMPANIES_ROOT)
        if file_name.endswith('.json')
    )


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
    assert company['company_name'] in html
    assert company['url'] in html
    assert company['tier'] in html
    assert str(company['award_year']) in html
    assert company['logo']['src'] in html
    assert company['business'] in html
    for founder in company['founders']:
        assert founder in html
    for reason in company['award_reasons']:
        assert reason in html

    # インタビュー節は申込企業のみ。未申込(null)なら節ごと出さない。
    if company['interview_url']:
        assert company['interview_url'] in html
    else:
        assert 'class="award-section interview"' not in html


def test_unknown_company_key_is_404(client):
    assert client.get('/truetechjapan/ja/award/no-such-company').status_code == 404
