## [1.0.4](https://github.com/yamshy/resume-assistant/compare/v1.0.3...v1.0.4) (2025-09-21)


### Bug Fixes

* prevent vector store tie comparison errors ([e6af807](https://github.com/yamshy/resume-assistant/commit/e6af80781c704c5a1cd49e2aa3d02f3ada67ba0f))

## [1.0.3](https://github.com/yamshy/resume-assistant/compare/v1.0.2...v1.0.3) (2025-09-21)


### Bug Fixes

* avoid redundant routing for cached resumes ([c632555](https://github.com/yamshy/resume-assistant/commit/c632555cce90c151f9d0a551ce6d09e254e882a8))

## [1.0.2](https://github.com/yamshy/resume-assistant/compare/v1.0.1...v1.0.2) (2025-09-21)


### Bug Fixes

* **deps:** update dependency fastapi to v0.117.1 ([77c3aff](https://github.com/yamshy/resume-assistant/commit/77c3affd1a20f2539e7abb483c9f68802a5680d6))

## [1.0.1](https://github.com/yamshy/resume-assistant/compare/v1.0.0...v1.0.1) (2025-09-21)


### Bug Fixes

* **deps:** update dependency redis to v5.3.1 ([6d93836](https://github.com/yamshy/resume-assistant/commit/6d93836f5e3b749f00120f5e6c3ba13c1727b030))
* remove unsupported uv pip frozen flag ([f7f7121](https://github.com/yamshy/resume-assistant/commit/f7f712171a8401a95122dac0c4f350eb2ed8581b))

# 1.0.0 (2025-09-20)


### Bug Fixes

* **deps:** update dependency openai to v1.108.1 ([8e28144](https://github.com/yamshy/resume-assistant/commit/8e28144ab911575c2d98e79a6fc7ed3a3efd1dce))
* **deps:** update dependency openai to v1.108.1 ([#19](https://github.com/yamshy/resume-assistant/issues/19)) ([e566f96](https://github.com/yamshy/resume-assistant/commit/e566f96852c5eda71edba7d509df02006bcae750))
* **deps:** update dependency pydantic to v2.11.9 ([bfc201e](https://github.com/yamshy/resume-assistant/commit/bfc201e474acfe40473202e997f39ba5c049a2e9))
* resolve CI issues with uv.lock and dependencies ([9402642](https://github.com/yamshy/resume-assistant/commit/94026424b96e1f6118b37018743451bfc44a9f0b))
* resolve merge conflicts in app_factory.py and test_api.py ([28c6382](https://github.com/yamshy/resume-assistant/commit/28c63825a0fc196cbe666c8fc510f500182e6810))
* resolve merge conflicts with main ([7cdfecf](https://github.com/yamshy/resume-assistant/commit/7cdfecf3c974e1fc4739d9ee598671b679b4d399))
* resolve ruff configuration and formatting issues ([527fa1b](https://github.com/yamshy/resume-assistant/commit/527fa1bed3c1b6160bfbb1e13bc1371c608c4e96))
* update uv commands to modern syntax ([96f36b0](https://github.com/yamshy/resume-assistant/commit/96f36b03eb729a8f41e39c7a687271f134f60701))


### Features

* add chat endpoint and UI integration ([741e5e9](https://github.com/yamshy/resume-assistant/commit/741e5e95e2b57c5276c948f38bb51fe9552d9de4))
* add chat workspace integration ([dd1e247](https://github.com/yamshy/resume-assistant/commit/dd1e2475651feb6db1fd96d3a18df13a1b4f76fa))
* add conversational chat endpoint ([090c6a5](https://github.com/yamshy/resume-assistant/commit/090c6a572e1aa5247cf3ecac482a5890eb4a4883))
* add knowledge ingestion workflow ([37ec04e](https://github.com/yamshy/resume-assistant/commit/37ec04ed2ae25038bed65a09956dfaee84af2730))
* **init:** scaffold minimal FastAPI + pydanticAI template with src layout, TDD, and uv ([dd5493e](https://github.com/yamshy/resume-assistant/commit/dd5493e37e0d785f4e46b2430629d9270684254b))
* surface knowledge and generation workflows in ui ([3eee591](https://github.com/yamshy/resume-assistant/commit/3eee5912889bee9ea3242507fc5b4a90d5c71582))
* unify chat workflow interface ([7511306](https://github.com/yamshy/resume-assistant/commit/75113069804605d4e410144241ea17b10bab3b91))
* unify resume workflow with knowledge ingestion ([f7dac7b](https://github.com/yamshy/resume-assistant/commit/f7dac7b753ddb677f9142695aea006510836dc89))
