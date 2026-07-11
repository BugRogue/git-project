class DriverManager:
    """
    Facade over `SeleniumFactory` and `PlaywrightFactory`. This is the ONLY
    class the rest of the framework should use to obtain or dispose of a
    browser session.
    """

    @staticmethod
    def get_execution_engine() -> EngineName:
        """Read the active engine flag: env var override takes precedence
        over config.yaml, so CI can force a specific engine per test step
        without needing a separate committed config per suite."""
        engine = os.environ.get("EXECUTION_ENGINE")
        if not engine:
            engine = DataReader.read_yaml("config/config.yaml").get(
                "execution_engine", "selenium"
            )
        engine = engine.lower()
        if engine not in ("selenium", "playwright"):
            raise ValueError(
                f"Invalid execution_engine '{engine}'. Must be 'selenium' or 'playwright'."
            )
        return engine  # type: ignore[return-value]

    @classmethod
    def get_driver(cls) -> Union[Any, PlaywrightSession]:
        """
        Create a new driver/session for the configured engine, register it
        thread-locally, and return it.

        Returns:
            - A Selenium `WebDriver` instance, when execution_engine="selenium".
            - A `PlaywrightSession` dataclass (playwright/browser/context/page),
              when execution_engine="playwright".
        """
        engine = cls.get_execution_engine()
        log.info("DriverManager resolving engine: %s", engine)

        if engine == "selenium":
            session = SeleniumFactory.create_driver()
        else:  # playwright
            session = PlaywrightFactory.create_session()

        BrowserManager.set_session(session)
        return session

    @classmethod
    def get_current_session(cls) -> Union[Any, PlaywrightSession]:
        """
        Return the already-created session for the current thread. Raises
        if `get_driver()` was never called on this thread — this is
        intentional so pages/tests fail fast with a clear error rather than
        silently creating an unexpected second browser.
        """
        session = BrowserManager.get_session()
        if session is None:
            raise RuntimeError(
                "No active driver/session found for this thread. "
                "Call DriverManager.get_driver() in a fixture before use."
            )
        return session

    @classmethod
    def quit_driver(cls) -> None:
        """
        Tear down the active session for the current thread, regardless of
        which engine created it, and clear the thread-local registry.
        """
        session = BrowserManager.get_session()
        if session is None:
            log.debug("quit_driver called but no active session found; nothing to do.")
            return

        engine = cls.get_execution_engine()
        try:
            if engine == "selenium":
                session.quit()
            else:  # playwright: PlaywrightSession dataclass
                config = DataReader.read_yaml("config/config.yaml")
                if config.get("reporting", {}).get("trace_on_failure", False):
                    try:
                        session.context.tracing.stop()
                    except Exception as trace_exc:  # pragma: no cover
                        log.warning("Could not stop Playwright trace: %s", trace_exc)
                session.context.close()
                session.browser.close()
                session.playwright.stop()
            log.info("Driver/session torn down successfully for engine '%s'.", engine)
        except Exception as exc:
            log.error("Error while tearing down driver/session: %s", exc)
        finally:
            BrowserManager.clear_session()
