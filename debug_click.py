from playwright.sync_api import sync_playwright
import time

pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled','--no-sandbox'])
ctx = browser.new_context(
    viewport={'width':1920,'height':1080},
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    locale='en-US'
)
ctx.add_init_script("""Object.defineProperty(navigator,'webdriver',{get:()=>undefined}); window.chrome={runtime:{}};""")
page = ctx.new_page()
page.goto('https://www.google.com/maps/search/salons+in+ahmedabad', wait_until='domcontentloaded', timeout=30000)
time.sleep(8)

links = page.query_selector_all('a[href*="/maps/place/"]')
print(f'Found {len(links)} place links')

if links:
    link = links[0]
    aria = link.get_attribute('aria-label') or 'unknown'
    print(f'Clicking: {aria}')
    link.click()
    time.sleep(4)
    page.screenshot(path='E:/work_space/scrapper/debug_after_click.png')

    h1s = page.query_selector_all('h1')
    for h in h1s:
        print(f'H1: {h.inner_text().strip()}')

    btns = page.query_selector_all('button[data-item-id]')
    for b in btns:
        did = b.get_attribute('data-item-id') or ''
        aria2 = b.get_attribute('aria-label') or ''
        print(f'  btn: id=[{did[:50]}] aria=[{aria2[:80]}]')

    aitems = page.query_selector_all('a[data-item-id]')
    for a in aitems:
        did = a.get_attribute('data-item-id') or ''
        aria2 = a.get_attribute('aria-label') or ''
        href = a.get_attribute('href') or ''
        print(f'  a: id=[{did[:50]}] aria=[{aria2[:80]}] href=[{href[:100]}]')

browser.close()
pw.stop()
