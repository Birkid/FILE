import csv
import time
import random
import os
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import undetected_chromedriver as uc


class EnhancedOkoooSpider:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.existing_ids = set()
        self.csv_file = 'okooo_matches.csv'
        self.session_cookies = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.setup_driver()
        self.load_existing_ids()

    def setup_driver(self):
        """设置更强的反检测Chrome驱动"""
        try:
            # 使用undetected_chromedriver，它能更好地绕过检测
            chrome_options = uc.ChromeOptions()

            if self.headless:
                chrome_options.add_argument('--headless')

            # 更全面的反检测设置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins-discovery')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')

            # 随机用户代理
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f'--user-agent={user_agent}')

            # 窗口大小随机化
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            chrome_options.add_argument(f'--window-size={width},{height}')

            # 创建驱动
            self.driver = uc.Chrome(options=chrome_options, version_main=None)

            # 执行反检测脚本
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
            """)

            print("增强版Chrome驱动已启动")

        except Exception as e:
            print(f"undetected_chromedriver启动失败，尝试普通Chrome: {e}")
            # 如果undetected_chromedriver失败，回退到普通Chrome
            self.setup_regular_chrome()

    def setup_regular_chrome(self):
        """设置普通Chrome驱动作为备选"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        # 基本反检测设置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 随机用户代理
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f'--user-agent={user_agent}')

        # 随机窗口大小
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        chrome_options.add_argument(f'--window-size={width},{height}')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def load_existing_ids(self):
        """加载已存在的比赛ID"""
        if os.path.exists(self.csv_file):
            try:
                df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
                if '序号' in df.columns:
                    self.existing_ids = set(df['序号'].astype(str).tolist())
                    print(f"已加载 {len(self.existing_ids)} 个现有比赛ID")
            except Exception as e:
                print(f"加载现有ID时出错: {e}")

    def save_session(self):
        """保存会话信息"""
        try:
            cookies = self.driver.get_cookies()
            session_data = {
                'cookies': cookies,
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'timestamp': time.time()
            }
            with open('session_data.json', 'w') as f:
                json.dump(session_data, f)
            print("会话信息已保存")
        except Exception as e:
            print(f"保存会话失败: {e}")

    def load_session(self):
        """加载会话信息"""
        try:
            if os.path.exists('session_data.json'):
                with open('session_data.json', 'r') as f:
                    session_data = json.load(f)

                # 检查会话是否过期（24小时）
                if time.time() - session_data.get('timestamp', 0) < 24 * 3600:
                    # 先访问网站主页
                    self.driver.get("https://www.okooo.com")
                    time.sleep(2)

                    # 加载cookies
                    for cookie in session_data['cookies']:
                        try:
                            self.driver.add_cookie(cookie)
                        except:
                            pass

                    print("已加载保存的会话信息")
                    return True
        except Exception as e:
            print(f"加载会话失败: {e}")
        return False

    def human_like_mouse_movement(self, element):
        """模拟人类鼠标移动"""
        try:
            action = ActionChains(self.driver)

            # 先移动到随机位置
            action.move_by_offset(random.randint(-100, 100), random.randint(-100, 100))
            action.perform()
            time.sleep(random.uniform(0.5, 1.0))

            # 移动到元素附近
            action = ActionChains(self.driver)
            action.move_to_element_with_offset(element,
                                               random.randint(-5, 5),
                                               random.randint(-5, 5))
            action.perform()
            time.sleep(random.uniform(0.3, 0.8))

            # 最终移动到元素
            action = ActionChains(self.driver)
            action.move_to_element(element)
            action.perform()
            time.sleep(random.uniform(0.2, 0.5))

        except Exception as e:
            print(f"鼠标移动模拟失败: {e}")

    def simulate_human_behavior(self):
        """模拟人类浏览行为"""
        try:
            # 随机滚动页面
            scroll_height = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(random.uniform(1, 2))

            # 随机点击空白区域（模拟用户查看页面）
            body = self.driver.find_element(By.TAG_NAME, "body")
            action = ActionChains(self.driver)
            action.move_to_element_with_offset(body,
                                               random.randint(100, 500),
                                               random.randint(100, 300))
            action.click()
            action.perform()
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"模拟人类行为失败: {e}")

    def handle_slider_captcha(self):
        """处理滑块验证码"""
        try:
            print("检测到滑块验证码，尝试处理...")

            # 常见的滑块验证码选择器
            slider_selectors = [
                '.geetest_slider_button',
                '.slide-verify-slider-mask-item',
                '.slider-button',
                '.captcha-slider-btn',
                '#slider'
            ]

            slider_element = None
            for selector in slider_selectors:
                try:
                    slider_element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue

            if slider_element:
                # 模拟人类滑动
                action = ActionChains(self.driver)

                # 先模拟鼠标移动到滑块
                self.human_like_mouse_movement(slider_element)

                # 按下鼠标
                action.click_and_hold(slider_element)
                action.perform()
                time.sleep(random.uniform(0.2, 0.5))

                # 分段滑动，模拟人类行为
                total_distance = random.randint(250, 300)
                segments = random.randint(8, 15)

                for i in range(segments):
                    segment_distance = total_distance // segments
                    # 添加随机扰动
                    x_move = segment_distance + random.randint(-3, 3)
                    y_move = random.randint(-2, 2)

                    action.move_by_offset(x_move, y_move)
                    action.perform()

                    # 随机停顿
                    time.sleep(random.uniform(0.05, 0.15))

                # 释放鼠标
                action.release()
                action.perform()

                print("滑块操作完成，等待验证结果...")
                time.sleep(3)

                return True

        except Exception as e:
            print(f"处理滑块验证码失败: {e}")

        return False

    def check_anti_crawler(self):
        """检查反爬验证 - 修复关键词误判"""
        try:
            current_url = self.driver.current_url
            page_text = self.driver.page_source
            title = self.driver.title if self.driver.title else ""

            # 优先检查页面标题 - 这是最准确的判断方式
            if title:
                title_lower = title.lower()
                verification_titles = [
                    "滑动验证",
                    "访问验证",
                    "安全验证",
                    "验证失败",
                    "blocked",
                    "403",
                    "404",
                    "405",
                    "error"
                ]

                for verify_title in verification_titles:
                    if verify_title in title_lower:
                        print(f"🚨 标题显示验证页面: {title}")
                        return True

            # 检查URL重定向
            error_url_patterns = ["error", "blocked", "verify", "captcha", "security"]
            current_url_lower = current_url.lower()
            for pattern in error_url_patterns:
                if pattern in current_url_lower:
                    print(f"🚨 URL重定向到错误页面: {current_url}")
                    return True

            # 检查页面中的明确验证提示（需要同时出现多个关键词才判定）
            strong_verification_phrases = [
                "很抱歉，由于您询问的URL有可能对网站造成安全威胁",
                "请完成安全验证",
                "滑动下方滑块完成验证",
                "拖动滑块完成验证",
                "点击完成验证",
                "ac11000117543290780328834e65d1"  # 您提到的具体ID
            ]

            for phrase in strong_verification_phrases:
                if phrase in page_text:
                    print(f"🚨 检测到明确验证提示: {phrase[:20]}...")
                    return True

            # 检查页面是否异常短（明显错误页面）
            if len(page_text.strip()) < 1000:
                print(f"🚨 页面内容过短: {len(page_text)} 字符")
                return True

            # 检查是否包含滑块验证的DOM结构（而不是仅仅包含geetest库）
            captcha_dom_indicators = [
                'class="geetest_panel"',
                'class="geetest_slider"',
                'id="captcha"',
                'class="slide-verify"',
                'class="captcha-container"'
            ]

            captcha_dom_count = sum(1 for indicator in captcha_dom_indicators if indicator in page_text)
            if captcha_dom_count >= 2:  # 需要多个指标同时存在
                print(f"🚨 检测到验证码DOM结构 (匹配: {captcha_dom_count})")
                return True

            # 如果以上都没问题，认为页面正常
            print("✅ 页面状态检查通过，无验证码")
            return False

        except Exception as e:
            print(f"❌ 检查页面状态时出错: {e}")
            return False

    def is_normal_page(self):
        """判断是否为正常的澳客网页面"""
        try:
            page_source = self.driver.page_source
            current_url = self.driver.current_url

            # 检查URL是否正常
            if "okooo.com" not in current_url:
                print(f"⚠️ URL异常: {current_url}")
                return False

            # 检查页面必要元素
            required_elements = [
                "澳客网",
                "www.okooo.com",
                "livecenter"
            ]

            found_elements = sum(1 for element in required_elements if element in page_source)

            if found_elements < 2:
                print(f"⚠️ 缺少必要页面元素 (找到 {found_elements}/{len(required_elements)})")
                return False

            # 检查页面长度
            if len(page_source) < 1000:
                print(f"⚠️ 页面内容过短: {len(page_source)} 字符")
                return False

            print(f"✅ 页面状态正常 (长度: {len(page_source)} 字符)")
            return True

        except Exception as e:
            print(f"❌ 判断页面状态时出错: {e}")
            return False

    def has_match_data(self):
        """检查是否有比赛数据 - 改进版"""
        try:
            # 方法1: 检查比赛行元素
            match_elements = self.driver.find_elements(By.CLASS_NAME, "each_match")
            if match_elements:
                print(f"✅ 找到 {len(match_elements)} 个比赛元素")
                return True

            # 方法2: 检查比赛相关的关键元素
            key_selectors = [
                "a.ctrl_homename",  # 主队链接
                "a.ctrl_awayname",  # 客队链接
                "b.ctrl_homescore",  # 主队比分
                "tr[id*='match_detail_']"  # 比赛详情行
            ]

            for selector in key_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ 通过选择器 '{selector}' 找到 {len(elements)} 个比赛相关元素")
                    return True

            # 方法3: 检查页面源码中的比赛指标
            page_source = self.driver.page_source
            match_indicators = [
                "match_detail_",
                "ctrl_homename",
                "ctrl_awayname",
                "each_match"
            ]

            for indicator in match_indicators:
                if indicator in page_source:
                    print(f"✅ 在页面源码中找到比赛指标: {indicator}")
                    return True

            print("ℹ️ 未找到比赛数据，可能当天无比赛")
            return False

        except Exception as e:
            print(f"❌ 检查比赛数据时出错: {e}")
            return False

    def handle_verification_enhanced(self):
        """增强版验证处理"""
        print("\n" + "🔒" * 20 + " 遇到验证页面 " + "🔒" * 20)

        # 首先尝试自动处理滑块
        if self.handle_slider_captcha():
            time.sleep(3)
            if self.has_match_data():
                print("✅ 自动滑块验证成功！")
                return 'continue'

        # 如果自动处理失败，进行人工处理
        print("🤖 自动处理失败，需要人工干预")
        print(f"📄 当前页面: {self.driver.current_url}")
        print(f"📋 页面标题: {self.driver.title}")

        print("\n🛠️ 处理选项:")
        print("1. 回车 - 手动完成验证后继续")
        print("2. s + 回车 - 跳过当前页面")
        print("3. r + 回车 - 刷新页面重试")
        print("4. c + 回车 - 清除cookies重新开始")
        print("5. q + 回车 - 退出程序")

        choice = input("\n选择操作: ").strip().lower()

        if choice == 's':
            return 'skip'
        elif choice == 'r':
            self.driver.refresh()
            time.sleep(3)
            return 'continue'
        elif choice == 'c':
            self.driver.delete_all_cookies()
            print("Cookies已清除")
            return 'continue'
        elif choice == 'q':
            return 'quit'
        else:
            return 'continue'

    def debug_page_status(self):
        """调试页面状态 - 显示详细信息"""
        try:
            print(f"\n{'=' * 50}")
            print("🔍 页面状态调试信息:")
            print(f"📄 URL: {self.driver.current_url}")
            print(f"📋 标题: {self.driver.title}")

            # 检查比赛数据
            match_elements = self.driver.find_elements(By.CLASS_NAME, "each_match")
            print(f"🏈 比赛行数量: {len(match_elements)}")

            # 检查关键元素
            key_elements = {
                "主队链接": "a.ctrl_homename",
                "客队链接": "a.ctrl_awayname",
                "比分元素": "b.ctrl_homescore"
            }

            for name, selector in key_elements.items():
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"🔍 {name}: {len(elements)} 个")

            # 页面内容长度
            page_length = len(self.driver.page_source)
            print(f"📏 页面长度: {page_length} 字符")

            # 检查可能的验证码指标
            page_text = self.driver.page_source
            verification_checks = {
                "标题包含验证": any(word in (self.driver.title or "").lower()
                                    for word in ["验证", "blocked", "error"]),
                "URL异常": any(word in self.driver.current_url.lower()
                               for word in ["error", "blocked", "verify"]),
                "页面过短": page_length < 1000,
                "包含验证提示": "滑动下方滑块" in page_text or "完成验证" in page_text
            }

            print("🚨 验证码检查:")
            for check, result in verification_checks.items():
                status = "❌" if result else "✅"
                print(f"   {status} {check}: {result}")

            print(f"{'=' * 50}\n")

        except Exception as e:
            print(f"❌ 调试信息获取失败: {e}")

    def get_page_enhanced(self, url, max_retries=3):
        """增强版页面获取 - 添加调试信息"""
        for attempt in range(max_retries):
            try:
                print(f"🌐 访问: {url} (尝试 {attempt + 1}/{max_retries})")

                # 重试前的等待
                if attempt > 0:
                    wait_time = random.uniform(5, 10)
                    print(f"⏳ 等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)

                # 访问页面前的随机延迟
                time.sleep(random.uniform(2, 4))

                # 访问页面
                self.driver.get(url)

                # 等待页面加载完成
                WebDriverWait(self.driver, 20).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )

                # 额外等待动态内容加载
                time.sleep(3)

                # 模拟人类浏览行为
                self.simulate_human_behavior()

                # 🔍 显示调试信息（可选，调试时开启）
                # self.debug_page_status()

                # 🔥 关键修改：优先检查是否有比赛数据
                has_matches = self.has_match_data()
                if has_matches:
                    print("🏆 发现比赛数据，页面正常")
                    self.save_session()
                    return self.driver.page_source

                # 如果没有比赛数据，再检查是否为正常页面
                if not self.is_normal_page():
                    print("❌ 页面异常，将重试")
                    continue

                # 只有在页面正常但无比赛数据时，才检查是否遇到验证码
                if self.check_anti_crawler():
                    print("🚨 检测到验证码页面")
                    # 显示详细调试信息
                    self.debug_page_status()

                    action = self.handle_verification_enhanced()

                    if action == 'quit':
                        raise KeyboardInterrupt("用户选择退出")
                    elif action == 'skip':
                        return None
                    elif action == 'continue':
                        time.sleep(3)
                        # 验证后重新检查
                        if self.has_match_data():
                            print("✅ 验证后发现比赛数据")
                            self.save_session()
                            return self.driver.page_source
                        elif self.is_normal_page() and not self.check_anti_crawler():
                            print("✅ 验证后页面正常，但当天无比赛")
                            self.save_session()
                            return self.driver.page_source
                        else:
                            print("❌ 验证后问题仍存在，将重试")
                            continue
                else:
                    # 页面正常但无比赛数据（可能当天就是没有比赛）
                    print("📅 页面正常，当天无比赛安排")
                    self.save_session()
                    return self.driver.page_source

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ 访问失败 (尝试 {attempt + 1}): {e}")

        print(f"❌ 所有尝试均失败: {url}")
        return None

    def parse_match_data(self, html_content):
        """解析比赛数据（保持原有逻辑）"""
        soup = BeautifulSoup(html_content, 'html.parser')
        matches = []

        match_rows = soup.find_all('tr', class_='each_match')
        print(f"🏈 找到 {len(match_rows)} 个比赛行")

        for tr in match_rows:
            try:
                match_data = {}

                # 提取序号
                match_id = tr.get('id')
                if match_id and match_id.startswith('match_detail_'):
                    match_id_num = match_id.replace('match_detail_', '')
                    match_data['序号'] = match_id_num

                    if match_id_num in self.existing_ids:
                        continue

                # 提取赛事
                league_link = tr.find('a', class_='ssname')
                if league_link:
                    match_data['赛事'] = league_link.get_text(strip=True)

                # 提取时间
                time_cells = tr.find_all('td', class_='graytx')
                for cell in time_cells:
                    cell_text = cell.get_text(strip=True)
                    if ':' in cell_text and ('-' in cell_text or '/' in cell_text):
                        match_data['时间'] = cell_text
                        break

                # 提取主队
                home_link = tr.find('a', class_='ctrl_homename')
                if home_link:
                    home_name = home_link.get_text(strip=True)
                    home_td = home_link.find_parent('td')
                    if home_td:
                        rq_span = home_td.find('span', class_='rqObj')
                        if not rq_span:
                            rq_span = home_td.find('span', class_='ctrl_rq')

                        if rq_span:
                            rq_text = rq_span.get_text(strip=True)
                            if rq_text:
                                match_data['主队'] = f"{home_name}{rq_text}"
                            else:
                                match_data['主队'] = home_name
                        else:
                            match_data['主队'] = home_name

                # 提取客队
                away_link = tr.find('a', class_='ctrl_awayname')
                if away_link:
                    match_data['客队'] = away_link.get_text(strip=True)

                # 提取比分
                home_score = tr.find('b', class_='ctrl_homescore')
                away_score = tr.find('b', class_='ctrl_awayscore')

                if home_score and away_score:
                    home_score_text = home_score.get_text(strip=True)
                    away_score_text = away_score.get_text(strip=True)
                    match_data['比分'] = f"{home_score_text}-{away_score_text}"

                # 提取赔率
                odds_cell = tr.find('td', class_='blockbox')
                if not odds_cell:
                    odds_cell = tr.find('td', class_='ctrl_self_betopt')

                if odds_cell:
                    odds_spans = odds_cell.find_all('span')
                    odds_values = []

                    for span in odds_spans:
                        span_text = span.get_text(strip=True)
                        try:
                            if span_text and '.' in span_text:
                                odds_value = float(span_text)
                                if 1.0 < odds_value < 50.0:
                                    odds_values.append(span_text)
                        except ValueError:
                            continue

                    if len(odds_values) >= 1:
                        match_data['胜赔'] = odds_values[0]
                    if len(odds_values) >= 2:
                        match_data['平赔'] = odds_values[1]
                    if len(odds_values) >= 3:
                        match_data['负赔'] = odds_values[2]

                # 验证数据并添加
                if (match_data.get('主队') and match_data.get('客队') and
                        match_data.get('序号') and match_data.get('序号') not in self.existing_ids):
                    matches.append(match_data)
                    self.existing_ids.add(match_data['序号'])
                    print(f"📝 新增: {match_data.get('序号')} - {match_data.get('主队')} vs {match_data.get('客队')}")

            except Exception as e:
                print(f"❌ 解析行数据时出错: {e}")
                continue

        return matches

    def append_to_csv(self, matches):
        """追加数据到CSV文件（保持原有逻辑）"""
        if not matches:
            return

        fieldnames = ['序号', '赛事', '时间', '主队', '客队', '比分', '胜赔', '平赔', '负赔']
        file_exists = os.path.exists(self.csv_file)

        with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            for match in matches:
                row = {}
                for field in fieldnames:
                    row[field] = match.get(field, '')
                writer.writerow(row)

            print(f"💾 成功保存 {len(matches)} 场比赛到 {self.csv_file}")

    def generate_date_range(self, start_date, end_date):
        """生成日期范围（保持原有逻辑）"""
        try:
            start_num = int(start_date)
            end_num = int(end_date)

            start_year_code = int(str(start_date)[:2])
            end_year_code = int(str(end_date)[:2])

            if start_year_code != end_year_code:
                print("⚠️ 暂不支持跨年份爬取")
                return []

            dates = []
            current_num = start_num

            while current_num <= end_num:
                dates.append(str(current_num))
                current_num += 1

            return dates

        except Exception as e:
            print(f"❌ 生成日期范围时出错: {e}")
            return []

    def crawl_date_range(self, start_date, end_date, base_url="https://www.okooo.com/livecenter/danchang/?date="):
        """爬取日期范围数据"""
        print(f"🚀 开始爬取日期范围: {start_date} 到 {end_date}")

        # 尝试加载已保存的会话
        if self.load_session():
            print("✅ 使用已保存的会话信息")

        dates = self.generate_date_range(start_date, end_date)
        if not dates:
            return

        print(f"📅 总共需要爬取 {len(dates)} 天的数据")

        total_new_matches = 0
        skipped_dates = []
        failed_dates = []

        for i, date in enumerate(dates, 1):
            try:
                url = f"{base_url}{date}"
                print(f"\n{'🏆' * 30}")
                print(f"📊 进度: {i}/{len(dates)} - 日期参数: {date}")

                html_content = self.get_page_enhanced(url)

                if html_content is None:
                    skipped_dates.append(date)
                    continue

                matches = self.parse_match_data(html_content)

                if matches:
                    self.append_to_csv(matches)
                    total_new_matches += len(matches)
                    print(f"✅ 日期 {date}: 新增 {len(matches)} 场比赛")
                else:
                    print(f"⚠️ 日期 {date}: 无新增比赛数据")

                # 智能延迟
                if i < len(dates):
                    delay = random.uniform(3, 8)
                    print(f"⏱️ 等待 {delay:.1f} 秒...")
                    time.sleep(delay)

            except KeyboardInterrupt:
                print(f"\n⏹️ 用户中断，已爬取到日期: {date}")
                break
            except Exception as e:
                print(f"❌ 爬取日期 {date} 时出错: {e}")
                failed_dates.append(date)
                continue

        # 显示总结
        print(f"\n{'🎉' * 30}")
        print("📊 爬取完成统计:")
        print(f"✅ 总共新增: {total_new_matches} 场比赛")
        print(f"✅ 成功爬取: {len(dates) - len(skipped_dates) - len(failed_dates)} 天")
        if skipped_dates:
            print(f"⚠️ 跳过日期: {len(skipped_dates)} 天")
        if failed_dates:
            print(f"❌ 失败日期: {len(failed_dates)} 天")
        print(f"📁 数据保存至: {self.csv_file}")

    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("🔒 浏览器已关闭")


def main():
    print("🤖 澳客网增强版反爬虫爬虫启动")
    print("📝 安装依赖: pip install undetected-chromedriver")
    print("🛡️ 支持自动滑块验证和会话保持")
    print("-" * 50)

    spider = None
    try:
        spider = EnhancedOkoooSpider(headless=False)

        start_date = "25011"
        end_date = "25081"

        spider.crawl_date_range(start_date, end_date)

    except KeyboardInterrupt:
        print("\n⏹️ 用户主动停止")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if spider:
            spider.close()


if __name__ == "__main__":
    main()