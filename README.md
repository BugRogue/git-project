# Hybrid Automation Framework — SauceDemo

A production-grade, hybrid **Selenium + Playwright** test automation framework built in Python, designed to automate [SauceDemo](https://www.saucedemo.com/) using a single, engine-agnostic Page Object layer. The framework lets you switch the entire execution engine — Selenium or Playwright — by changing **one config flag**, without touching a single test or page object.

---

## 1. Why Hybrid?

Most teams eventually face this question: *"Do we rewrite everything in Playwright, or keep Selenium?"* This framework avoids that binary choice:

- **Selenium** remains available for legacy browser matrix coverage (IE/older Edge, Selenium Grid farms, existing CI infra).
- **Playwright** is available for speed, auto-waiting, and modern browser contexts (parallel isolated contexts, tracing, network interception).
- Both engines share **one Page Object contract**, **one config system**, **one logger**, **one retry/wait strategy**, and **one reporting pipeline**.
- Teams can migrate page-by-page from Selenium to Playwright (see `tests/migration/`) instead of a risky big-bang rewrite.

---

## 2. Architecture Overview

```
                         ┌─────────────────────────┐
                         │      config/*.yaml       │
                         │  execution_engine flag   │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   DriverManager (Facade)  │  <- core/driver_factory/driver_manager.py
                         │  reads execution_engine   │
                         └──────┬─────────────┬─────┘
                                │             │
                 ┌──────────────▼───┐   ┌─────▼───────────────┐
                 │ SeleniumFactory   │   │ PlaywrightFactory    │
                 │ (WebDriver)       │   │ (Browser/Context/Page)│
                 └──────────┬────────┘   └─────────┬────────────┘
                            │                       │
                 ┌──────────▼────────┐   ┌──────────▼────────────┐
                 │ SeleniumActions   │   │ PlaywrightActions      │
                 │ implements        │   │ implements              │
                 │ CommonActions ────┼───┼──── CommonActions       │
                 └──────────┬────────┘   └──────────┬─────────────┘
                            │                       │
                 ┌──────────▼────────┐   ┌──────────▼────────────┐
                 │ SeleniumBasePage  │   │ PlaywrightBasePage      │
                 └──────────┬────────┘   └──────────┬─────────────┘
                            │                       │
                 ┌──────────▼────────┐   ┌──────────▼────────────┐
                 │ pages/selenium/*  │   │ pages/playwright/*      │
                 │ LoginPage, etc.   │   │ LoginPage, etc.          │
                 └──────────┬────────┘   └──────────┬─────────────┘
                            │                       │
                 ┌──────────▼────────┐   ┌──────────▼────────────┐
                 │ tests/selenium/*  │   │ tests/playwright/*      │
                 └───────────────────┘   └─────────────────────────┘
```

**Key idea:** every layer above the factories talks only to the abstraction below it (`CommonActions`, `BasePage`), never to raw `selenium` or `playwright` APIs directly. This is what makes the two verticals swappable and testable in isolation.

---

## 3. The `DriverManager` — How Engine Switching Works

`core/driver_factory/driver_manager.py` is the single entry point for driver creation across the whole framework. Nothing else imports `selenium_factory.py` or `playwright_factory.py` directly.

**Flow:**

1. `config/config.yaml` defines:
   ```yaml
   execution_engine: "playwright"   # or "selenium"
   ```
2. A test (via its base test class) calls `DriverManager.get_driver()`.
3. `DriverManager` reads `execution_engine` and delegates:
   - `"selenium"` → `SeleniumFactory.create_driver()` → returns a `selenium.webdriver.Remote`-family instance.
   - `"playwright"` → `PlaywrightFactory.create_session()` → returns a `PlaywrightSession` dataclass bundling `playwright`, `browser`, `context`, and `page`.
4. The returned object is registered in `BrowserManager` — a **thread-local** registry — so it is retrievable from anywhere in the same test thread (critical for the pytest failure hook capturing a screenshot without needing the driver passed explicitly).
5. `DriverManager.quit_driver()` handles teardown for **both** engines from one call site: `driver.quit()` for Selenium, or the full `context.close() → browser.close() → playwright.stop()` chain for Playwright (plus stopping any active trace).

**Why thread-local?** Because `pytest-xdist` parallel workers and any in-process threading must never share a browser session. Thread-local storage means each thread transparently gets its own isolated slot with zero explicit locking on read/write.

**Why a dataclass for Playwright but a raw object for Selenium?** Selenium's `WebDriver` is already a single object representing the whole session. Playwright's object graph (`playwright → browser → context → page`) has four independently disposable layers, so `PlaywrightSession` exists purely to bundle them for atomic teardown — it is not a design inconsistency, it reflects each library's real object model.

---

## 4. Design Pattern: Page Object Model (POM) + Facade + Factory

| Pattern | Where | Purpose |
|---|---|---|
| **Factory Method** | `driver_manager.py`, `selenium_factory.py`, `playwright_factory.py` | Encapsulate engine-specific construction logic behind one call: `get_driver()`. |
| **Facade** | `driver_manager.py` | Hides the very different Selenium vs. Playwright object graphs behind one uniform `get_driver()` / `quit_driver()` API. |
| **Page Object Model** | `pages/selenium/*`, `pages/playwright/*` | Each page is a class exposing business-readable methods (`login()`, `logout()`) instead of raw locator/action calls in test bodies. |
| **Strategy / Interface Segregation** | `core/wrappers/common_actions.py` (ABC) implemented by `selenium_actions.py` / `playwright_actions.py` | Page objects call `self.click(locator)` without knowing which engine executes it. |
| **Template Method** | `SeleniumBaseTest` / `PlaywrightBaseTest` `setup_method` / `teardown_method` | Common test lifecycle (get driver → resolve env/users → run test → quit driver) is defined once; concrete test classes only add test methods. |
| **Singleton** | `LoggerFactory` (in `logger.py`) | One logger instance per name, thread-safe, no duplicate handlers. |

### BasePage Responsibility
`SeleniumBasePage` / `PlaywrightBasePage` provide the **generic interaction surface**:
`click`, `type_text`, `get_text`, `is_displayed`, `get_elements`, `get_attribute`, `hover`, `select_dropdown_by_value`, `navigate_to`, `get_current_url`, `get_title`, `refresh`, `go_back`.

Concrete pages (e.g. `pages/selenium/login_page.py`) inherit from these and add only page-specific business methods (`login()`, `get_error_message()`), keeping locators and workflow logic together but interaction mechanics fully abstracted.

---

## 5. Directory Structure Reference

```
Hybrid-Automation-Framework/
│
├── config/
│   ├── config.yaml                # execution_engine flag, timeouts, retry, reporting
│   ├── environments.yaml          # base URLs + user credentials per env (qa/staging/prod)
│   └── browser_capabilities.yaml  # per-browser launch args/prefs for both engines
│
├── core/
│   ├── driver_factory/
│   │   ├── selenium_factory.py      # builds selenium WebDriver
│   │   ├── playwright_factory.py    # builds Playwright browser/context/page
│   │   ├── browser_manager.py       # thread-local active-session registry
│   │   └── driver_manager.py        # facade: reads config, switches engine, owns teardown
│   │
│   ├── base/
│   │   ├── selenium_base_page.py     # generic action surface (Selenium-backed)
│   │   ├── playwright_base_page.py   # generic action surface (Playwright-backed)
│   │   ├── selenium_base_test.py     # pytest base test class (Selenium)
│   │   └── playwright_base_test.py   # pytest base test class (Playwright)
│   │
│   ├── utilities/
│   │   ├── logger.py         # thread-safe singleton logger (file + console)
│   │   ├── screenshot.py     # engine-agnostic screenshot capture
│   │   ├── wait.py           # SeleniumWait / PlaywrightWait explicit-wait helpers
│   │   ├── retry.py          # @retry_on_failure decorator, config-driven backoff
│   │   ├── assertions.py     # Assertions (hard) + SoftAssertions (accumulate/raise)
│   │   └── data_reader.py    # cached YAML/JSON/CSV reader, env/browser config helpers
│   │
│   └── wrappers/
│       ├── common_actions.py     # ABC contract: click, type_text, get_text, ...
│       ├── selenium_actions.py   # Selenium implementation of CommonActions
│       └── playwright_actions.py # Playwright implementation of CommonActions
│
├── pages/
│   ├── selenium/     # LoginPage, InventoryPage (Selenium)
│   ├── playwright/   # LoginPage, InventoryPage (Playwright) — mirrored API
│   └── common/       # constants.py: shared URL fragments, titles, error text
│
├── tests/
│   ├── selenium/     # login_test.py — smoke suite, Selenium engine
│   ├── playwright/   # login_test.py — smoke suite, Playwright engine
│   ├── migration/    # parity_test.py — placeholder for Selenium<->Playwright parity checks
│   └── api/          # health_check_test.py — pure `requests`-based checks, no browser
│
├── locators/
│   ├── login_locators.py      # By-tuples (Selenium) + CSS strings (Playwright)
│   └── inventory_locators.py
│
├── testdata/     # place CSV/JSON/YAML data-driven test inputs here
├── reports/      # pytest-html + junitxml output (generated)
├── screenshots/  # failure screenshots (generated)
├── logs/         # rotating execution logs (generated)
│
├── conftest.py    # driver/page fixtures + engine-agnostic failure screenshot hook
├── pytest.ini     # markers, reporting flags, test discovery rules
├── requirements.txt
└── README.md
```

---

## 6. Configuration Reference

### `config/config.yaml`
| Key | Purpose |
|---|---|
| `execution_engine` | `"selenium"` or `"playwright"` — **the single switch** |
| `active_environment` | Must match a key in `environments.yaml` |
| `browser` | `chrome` \| `firefox` \| `edge` \| `webkit` (webkit is Playwright-only) |
| `headless` | Run browser headless |
| `timeouts.*` | Implicit wait, explicit wait, page load timeout, poll frequency |
| `retry.*` | Max attempts, backoff seconds, which exceptions trigger a retry |
| `reporting.*` | Screenshot/log/report directories, log level, Playwright trace/video toggles |
| `parallel.*` | pytest-xdist worker count (enable via `-n` on CLI) |
| `remote.*` | Point at a Selenium Grid hub or remote Playwright server |

### `config/environments.yaml`
Per-environment `base_url`, `api_base_url`, and the full SauceDemo user matrix (`standard_user`, `locked_out_user`, `problem_user`, `performance_glitch_user`) with credentials.

### `config/browser_capabilities.yaml`
Per-browser, per-engine launch arguments (Chrome flags, Firefox preferences, Playwright viewport/args) — kept separate from `config.yaml` so capability tuning doesn't clutter the main execution config.

---

## 7. Getting Started

### Install dependencies
```bash
pip install -r requirements.txt

# Install Playwright browser binaries (one-time)
playwright install
```

### Switch engines
Edit `config/config.yaml`:
```yaml
execution_engine: "selenium"     # or "playwright"
```

### Run the sample login suite
```bash
# Selenium engine
pytest tests/selenium/login_test.py -v

# Playwright engine
pytest tests/playwright/login_test.py -v

# API health checks (no browser)
pytest tests/api/ -v

# Full regression, parallel (4 workers)
pytest -n 4 -m regression

# Smoke suite only
pytest -m smoke
```

### Reports & artifacts
- HTML report: `reports/report.html`
- JUnit XML (CI integration): `reports/junit.xml`
- Failure screenshots: `screenshots/`
- Execution logs: `logs/execution_YYYYMMDD.log`

---

## 8. Extending the Framework

**Add a new page:**
1. Add locators to `locators/<page>_locators.py` — both a `*Selenium` (`By` tuples) and `*Playwright` (CSS string) class.
2. Create `pages/selenium/<page>_page.py` extending `SeleniumBasePage`.
3. Create `pages/playwright/<page>_page.py` extending `PlaywrightBasePage` with an identical public method surface.
4. Write tests in `tests/selenium/` and `tests/playwright/` calling only the page object's business methods.

**Add a new environment:** add a new top-level key to `environments.yaml`, then set `active_environment` in `config.yaml`.

**Migrate a Selenium page to Playwright:** port the locator strings, create the Playwright page object mirroring the Selenium one's public methods, add a parity test under `tests/migration/`, then flip `execution_engine` for that suite once verified.

---

## 9. Known Constraints & Design Trade-offs

- **Sync API only for Playwright.** The framework standardizes on `playwright.sync_api` (not `async_api`) to keep the test-writing model consistent with Selenium's synchronous calls and to avoid mixing asyncio event loops into pytest fixtures. This trades away some raw concurrency performance for consistency and lower onboarding cost.
- **Locators are engine-specific by necessity.** Selenium requires `By` tuples; Playwright uses CSS/text selectors. `locators/*.py` keeps both side-by-side in one file per page rather than trying to force a single locator format, since a unified abstraction here would be leakier than the two-class approach.
- **No cross-engine single test yet.** A given test file targets one engine (its base test class). True side-by-side parity execution belongs in `tests/migration/`, which is currently a documented placeholder — implement per-suite as pages are ported, rather than pre-building speculative parity tests that don't yet map to real page objects.
- **`retry_on_failure` is intentionally conservative.** It retries on a config-driven exception allowlist (stale elements, click interception, timeouts) — it will **not** retry on assertion failures or business-logic errors, to avoid masking real bugs as flakiness.
- **Selenium Manager handles driver binaries.** Selenium 4.6+'s built-in Selenium Manager resolves the correct chromedriver/geckodriver/msedgedriver automatically; no manual driver binary management or `webdriver-manager` dependency is required.
- **Screenshot capture is best-effort.** If no session is registered (e.g. a failure happens before `DriverManager.get_driver()` is called), the hook safely no-ops rather than raising.
- **Remote/Grid execution is scaffolded but not battle-tested here.** `config.yaml -> remote.enabled` wires both factories to a remote endpoint, but grid-specific capability negotiation (node matching, queueing) is left to your Grid/CI provider's own configuration.
