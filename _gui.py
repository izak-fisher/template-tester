"""Playwright GUI driver for a Pneumatic web client. Credentials come from env
(PNEU_GUI_EMAIL / PNEU_GUI_PASSWORD) and are never written to disk.

The web client is on 443, not the API's 8001, so HOST is the API base minus its port.
Override with PNEU_GUI_HOST."""
import os, sys
import pneumatic as P
from playwright.sync_api import sync_playwright

# 'https://<instance>:8001' -> 'https://<instance>'
HOST = os.environ.get('PNEU_GUI_HOST') or P.BASE.rsplit(':', 1)[0]
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shots')

def login(page):
    page.goto(HOST + '/auth/signin/', wait_until='networkidle')
    page.fill('input[type="email"], input[name="email"]', os.environ['PNEU_GUI_EMAIL'])
    page.fill('input[type="password"], input[name="password"]', os.environ['PNEU_GUI_PASSWORD'])
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    return page.url

def shot(page, name):
    p = os.path.join(SHOTS, name + '.png')
    page.screenshot(path=p, full_page=True)
    print('   shot ->', p)
    return p

if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width':1500,'height':1000})
        url = login(pg)
        print('after login url:', url)
        print('title:', pg.title())
        shot(pg, 'login')
        b.close()
