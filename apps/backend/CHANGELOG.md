# [1.17.0](https://github.com/yamshy/resume-assistant/compare/v1.16.0...v1.17.0) (2025-09-25)


### Features

* refine chat workspace presentation ([#110](https://github.com/yamshy/resume-assistant/issues/110)) ([68bc626](https://github.com/yamshy/resume-assistant/commit/68bc62601b150313ae5b34a5fa8d5badc1e95aa8))

# [1.16.0](https://github.com/yamshy/resume-assistant/compare/v1.15.0...v1.16.0) (2025-09-25)


### Features

* drive ingestion normalization with llm ([#109](https://github.com/yamshy/resume-assistant/issues/109)) ([549ca79](https://github.com/yamshy/resume-assistant/commit/549ca79d284ae2aa8bbf6182d5babd03aa91b539))

# [1.15.0](https://github.com/yamshy/resume-assistant/compare/v1.14.2...v1.15.0) (2025-09-24)


### Bug Fixes

* resolve failing GitHub workflows ([723cc2a](https://github.com/yamshy/resume-assistant/commit/723cc2ac753923db24aca5256a605439247dbe87))


### Features

* change exposed port from 8080 to 8124 ([7e4fce8](https://github.com/yamshy/resume-assistant/commit/7e4fce8e804698e0b1a35012cbed1ec0964a7d0b))

## [1.14.2](https://github.com/yamshy/resume-assistant/compare/v1.14.1...v1.14.2) (2025-09-24)


### Bug Fixes

* gate openai tests on workflow env ([#107](https://github.com/yamshy/resume-assistant/issues/107)) ([c3e4f3e](https://github.com/yamshy/resume-assistant/commit/c3e4f3e8616f78f6ea25845ae07d62d4f319e710))

## [1.14.1](https://github.com/yamshy/resume-assistant/compare/v1.14.0...v1.14.1) (2025-09-24)


### Bug Fixes

* guard live OpenAI tests with secrets context ([#105](https://github.com/yamshy/resume-assistant/issues/105)) ([ecfbe83](https://github.com/yamshy/resume-assistant/commit/ecfbe83e6bfd7d4b203356c3436e30ce4dca3c91))

# [1.14.0](https://github.com/yamshy/resume-assistant/compare/v1.13.2...v1.14.0) (2025-09-24)


### Features

* add API health check ([#104](https://github.com/yamshy/resume-assistant/issues/104)) ([7173b4f](https://github.com/yamshy/resume-assistant/commit/7173b4f32e9b1e5408fa8d97a2290c817837dc0f))

## [1.13.2](https://github.com/yamshy/resume-assistant/compare/v1.13.1...v1.13.2) (2025-09-24)


### Bug Fixes

* guard live OpenAI job when secret missing ([#103](https://github.com/yamshy/resume-assistant/issues/103)) ([2483181](https://github.com/yamshy/resume-assistant/commit/2483181498343c834683f77ab05beb23583000ca))

## [1.13.1](https://github.com/yamshy/resume-assistant/compare/v1.13.0...v1.13.1) (2025-09-24)


### Bug Fixes

* fallback instructor mode for openai clients ([#101](https://github.com/yamshy/resume-assistant/issues/101)) ([1db377c](https://github.com/yamshy/resume-assistant/commit/1db377c4f56efdac73146812671f98cab644f69d))

# [1.13.0](https://github.com/yamshy/resume-assistant/compare/v1.12.2...v1.13.0) (2025-09-24)


### Features

* add OpenAPI schema generation workflow ([#102](https://github.com/yamshy/resume-assistant/issues/102)) ([ea81989](https://github.com/yamshy/resume-assistant/commit/ea81989259bba24a12010e592ff6b864766b8272))

## [1.12.2](https://github.com/yamshy/resume-assistant/compare/v1.12.1...v1.12.2) (2025-09-24)


### Bug Fixes

* **deps:** update dependency openai to v1.109.1 ([#62](https://github.com/yamshy/resume-assistant/issues/62)) ([be0f571](https://github.com/yamshy/resume-assistant/commit/be0f571255c6e9cd507c2e5f176ac2d212d95b1f))

## [1.12.1](https://github.com/yamshy/resume-assistant/compare/v1.12.0...v1.12.1) (2025-09-24)


### Bug Fixes

* add default Dockerfile for release build ([#95](https://github.com/yamshy/resume-assistant/issues/95)) ([d00a4bf](https://github.com/yamshy/resume-assistant/commit/d00a4bf9eb8704e6058aa3ba024787efcbbfe315))

# [1.12.0](https://github.com/yamshy/resume-assistant/compare/v1.11.8...v1.12.0) (2025-09-24)


### Features

* migrate backend to temporal workflow ([#93](https://github.com/yamshy/resume-assistant/issues/93)) ([0ae8302](https://github.com/yamshy/resume-assistant/commit/0ae8302fe293033bfb425eb9911024453da9bd70))

## [1.11.8](https://github.com/yamshy/resume-assistant/compare/v1.11.7...v1.11.8) (2025-09-24)


### Bug Fixes

* **ci:** guard live tests on secret ([#91](https://github.com/yamshy/resume-assistant/issues/91)) ([f270d41](https://github.com/yamshy/resume-assistant/commit/f270d414ca864a31af797450641635cb8b5e4567))
* **deps:** update dependency langgraph-cli to v0.4.2 ([#90](https://github.com/yamshy/resume-assistant/issues/90)) ([9651b9b](https://github.com/yamshy/resume-assistant/commit/9651b9ba0dca07fb1f1a9da0729d75a2eca26eb9))

## [1.11.7](https://github.com/yamshy/resume-assistant/compare/v1.11.6...v1.11.7) (2025-09-24)


### Bug Fixes

* include langgraph cli dependency ([#89](https://github.com/yamshy/resume-assistant/issues/89)) ([14c70bc](https://github.com/yamshy/resume-assistant/commit/14c70bc4ce5b324616f3f1e96680b49756876a0a))

## [1.11.6](https://github.com/yamshy/resume-assistant/compare/v1.11.5...v1.11.6) (2025-09-24)


### Bug Fixes

* **deps:** update dependency pytest-asyncio to v1 ([#66](https://github.com/yamshy/resume-assistant/issues/66)) ([e49a59f](https://github.com/yamshy/resume-assistant/commit/e49a59f051891dc6eae5a82f331fdd81a5655f6e))

## [1.11.5](https://github.com/yamshy/resume-assistant/compare/v1.11.4...v1.11.5) (2025-09-24)


### Bug Fixes

* **deps:** update dependency mypy to v1.18.2 ([#33](https://github.com/yamshy/resume-assistant/issues/33)) ([31d3153](https://github.com/yamshy/resume-assistant/commit/31d3153a8303843554f88ccb985b89e43e98a8e4))

## [1.11.4](https://github.com/yamshy/resume-assistant/compare/v1.11.3...v1.11.4) (2025-09-24)


### Bug Fixes

* **deps:** update dependency langgraph to v0.6.7 ([#85](https://github.com/yamshy/resume-assistant/issues/85)) ([2d98775](https://github.com/yamshy/resume-assistant/commit/2d9877538c71b6e22279bf3792258834d2f5654b))

## [1.11.3](https://github.com/yamshy/resume-assistant/compare/v1.11.2...v1.11.3) (2025-09-24)


### Bug Fixes

* **deps:** update dependency pytest-asyncio to v0.26.0 ([#37](https://github.com/yamshy/resume-assistant/issues/37)) ([ed41fb4](https://github.com/yamshy/resume-assistant/commit/ed41fb4cc21e0917c93ba467dd30015cc50cec65))

## [1.11.2](https://github.com/yamshy/resume-assistant/compare/v1.11.1...v1.11.2) (2025-09-24)


### Bug Fixes

* **deps:** update dependency langchain-core to v0.3.76 ([#82](https://github.com/yamshy/resume-assistant/issues/82)) ([1c94ce2](https://github.com/yamshy/resume-assistant/commit/1c94ce26bc55e1ffc71ef84dd94324d1e1eaf6d1))

## [1.11.1](https://github.com/yamshy/resume-assistant/compare/v1.11.0...v1.11.1) (2025-09-24)


### Bug Fixes

* correct docker cmd syntax ([#86](https://github.com/yamshy/resume-assistant/issues/86)) ([56f0a20](https://github.com/yamshy/resume-assistant/commit/56f0a208ec28d167d8b1a95e5d2c788f69994456))

# [1.11.0](https://github.com/yamshy/resume-assistant/compare/v1.10.0...v1.11.0) (2025-09-24)


### Features

* integrate instructor structured outputs ([#84](https://github.com/yamshy/resume-assistant/issues/84)) ([fd76889](https://github.com/yamshy/resume-assistant/commit/fd76889c3b1be8162fec329fa74572a42dd5bb02))

# [1.10.0](https://github.com/yamshy/resume-assistant/compare/v1.9.1...v1.10.0) (2025-09-24)


### Bug Fixes

* harden llm orchestration and ci release workflows ([285a72c](https://github.com/yamshy/resume-assistant/commit/285a72c5bc6264d532ef2afa5f783bf204cf0439))


### Features

* rebuild resume orchestration on langgraph llm stack ([60dbdb9](https://github.com/yamshy/resume-assistant/commit/60dbdb9a1882215f1dabeb579f9928bea042800f))

## [1.9.1](https://github.com/yamshy/resume-assistant/compare/v1.9.0...v1.9.1) (2025-09-24)


### Bug Fixes

* **deps:** update dependency langsmith to v0.4.30 ([#31](https://github.com/yamshy/resume-assistant/issues/31)) ([9ebe76c](https://github.com/yamshy/resume-assistant/commit/9ebe76c8f0b3404fca91a27f06dca595ad7ef3ea))

# [1.9.0](https://github.com/yamshy/resume-assistant/compare/v1.8.2...v1.9.0) (2025-09-24)


### Bug Fixes

* normalise knowledge store inputs ([#73](https://github.com/yamshy/resume-assistant/issues/73)) ([cd94227](https://github.com/yamshy/resume-assistant/commit/cd94227f486050b627722efbaf6c4d612230959e))


### Features

* compute experience duration from dates ([#76](https://github.com/yamshy/resume-assistant/issues/76)) ([939d65b](https://github.com/yamshy/resume-assistant/commit/939d65bf48096d1a1b7d7c2f31e7da4d76f52b9f))

## [1.8.2](https://github.com/yamshy/resume-assistant/compare/v1.8.1...v1.8.2) (2025-09-24)


### Bug Fixes

* clarify ingestion LLM error handling ([#75](https://github.com/yamshy/resume-assistant/issues/75)) ([594d9d1](https://github.com/yamshy/resume-assistant/commit/594d9d1e9792e395973ac08ea22b828346c39d43))
* skip corrupt cache entries ([#74](https://github.com/yamshy/resume-assistant/issues/74)) ([0e2ed66](https://github.com/yamshy/resume-assistant/commit/0e2ed66d2b451d3e97ef6bbb70d1b5513ee4aa27))

## [1.8.1](https://github.com/yamshy/resume-assistant/compare/v1.8.0...v1.8.1) (2025-09-24)


### Bug Fixes

* prevent duplicate generation metrics ([#77](https://github.com/yamshy/resume-assistant/issues/77)) ([5b46da0](https://github.com/yamshy/resume-assistant/commit/5b46da0934674aa4cf8f4661eed45b47dda73ab7))

# [1.8.0](https://github.com/yamshy/resume-assistant/compare/v1.7.1...v1.8.0) (2025-09-23)


### Features

* redesign workspace ui ([#72](https://github.com/yamshy/resume-assistant/issues/72)) ([7f68ca5](https://github.com/yamshy/resume-assistant/commit/7f68ca56eba21807493566eb0c4b389cf77d5af5))

## [1.7.1](https://github.com/yamshy/resume-assistant/compare/v1.7.0...v1.7.1) (2025-09-23)


### Bug Fixes

* **deps:** update dependency instructor to v1.11.3 ([#30](https://github.com/yamshy/resume-assistant/issues/30)) ([ff06f83](https://github.com/yamshy/resume-assistant/commit/ff06f83305c43f7c1f9c9f8e37989a9462019632))

# [1.7.0](https://github.com/yamshy/resume-assistant/compare/v1.6.1...v1.7.0) (2025-09-23)


### Features

* require llm for resume ingestion ([#71](https://github.com/yamshy/resume-assistant/issues/71)) ([fadbc4c](https://github.com/yamshy/resume-assistant/commit/fadbc4cfb26948e75d84804caf8a77f3b1c383ca))

## [1.6.1](https://github.com/yamshy/resume-assistant/compare/v1.6.0...v1.6.1) (2025-09-23)


### Bug Fixes

* **deps:** update dependency redis to v6 ([#67](https://github.com/yamshy/resume-assistant/issues/67)) ([67e53ac](https://github.com/yamshy/resume-assistant/commit/67e53acefa133f7351499ce4cebb5dccbb6d8204))

# [1.6.0](https://github.com/yamshy/resume-assistant/compare/v1.5.0...v1.6.0) (2025-09-23)


### Features

* redesign workspace into single chat panel ([#70](https://github.com/yamshy/resume-assistant/issues/70)) ([f5776fd](https://github.com/yamshy/resume-assistant/commit/f5776fd883ff73eb7d1d83b0b38f9339f0eb4cda))

# [1.5.0](https://github.com/yamshy/resume-assistant/compare/v1.4.5...v1.5.0) (2025-09-23)


### Features

* add ingestion client resolver for ingestion agent ([#69](https://github.com/yamshy/resume-assistant/issues/69)) ([7cfd3ee](https://github.com/yamshy/resume-assistant/commit/7cfd3eed01b4662188c8c1c47e2f38bc4c386212))

## [1.4.5](https://github.com/yamshy/resume-assistant/compare/v1.4.4...v1.4.5) (2025-09-23)


### Bug Fixes

* **deps:** update dependency fakeredis to v2.31.3 ([#27](https://github.com/yamshy/resume-assistant/issues/27)) ([66610cd](https://github.com/yamshy/resume-assistant/commit/66610cd4b4c6e8c770298b939f2c30cef3719a5f))

## [1.4.4](https://github.com/yamshy/resume-assistant/compare/v1.4.3...v1.4.4) (2025-09-23)


### Bug Fixes

* surface upload errors and api key hint ([#63](https://github.com/yamshy/resume-assistant/issues/63)) ([2f6f7c7](https://github.com/yamshy/resume-assistant/commit/2f6f7c7369ead376a9885c89cf540853a4f7b991))

## [1.4.3](https://github.com/yamshy/resume-assistant/compare/v1.4.2...v1.4.3) (2025-09-23)


### Bug Fixes

* **deps:** update dependency ruff to v0.13.1 ([36bc89e](https://github.com/yamshy/resume-assistant/commit/36bc89e496f48430d7c2e023ea5537dd3ad7aacb))

## [1.4.2](https://github.com/yamshy/resume-assistant/compare/v1.4.1...v1.4.2) (2025-09-23)


### Bug Fixes

* **deps:** update dependency openai to v1.108.2 ([#55](https://github.com/yamshy/resume-assistant/issues/55)) ([da297c4](https://github.com/yamshy/resume-assistant/commit/da297c4d9622d31814420db302e5cb4b68b3b515))

## [1.4.1](https://github.com/yamshy/resume-assistant/compare/v1.4.0...v1.4.1) (2025-09-23)


### Bug Fixes

* **deps:** update dependency anthropic to v0.68.0 ([#18](https://github.com/yamshy/resume-assistant/issues/18)) ([2f70ef2](https://github.com/yamshy/resume-assistant/commit/2f70ef2d8ebdc460feba8e0860595b0c085253ee))

# [1.4.0](https://github.com/yamshy/resume-assistant/compare/v1.3.1...v1.4.0) (2025-09-22)


### Features

* streamline workspace chat composer ([8492f09](https://github.com/yamshy/resume-assistant/commit/8492f097eb853c9fc2c761a27d3b2a5dd86bfd28))

## [1.3.1](https://github.com/yamshy/resume-assistant/compare/v1.3.0...v1.3.1) (2025-09-22)


### Bug Fixes

* **deps:** update dependency pytest to v8.4.2 ([#26](https://github.com/yamshy/resume-assistant/issues/26)) ([5404f07](https://github.com/yamshy/resume-assistant/commit/5404f073ed0bef25dc0a6dfa389555c17d73178b))

# [1.3.0](https://github.com/yamshy/resume-assistant/compare/v1.2.0...v1.3.0) (2025-09-22)


### Features

* tighten claim grounding for skills and roles ([d166c0c](https://github.com/yamshy/resume-assistant/commit/d166c0cbe12e5eb15fe0d781d35e9ff93282a4d0))

# [1.2.0](https://github.com/yamshy/resume-assistant/compare/v1.1.0...v1.2.0) (2025-09-22)


### Features

* add agent orchestration for resume generation ([cc89120](https://github.com/yamshy/resume-assistant/commit/cc8912038bf37019fb53abc25d5afaed55881d5a))

# [1.1.0](https://github.com/yamshy/resume-assistant/compare/v1.0.4...v1.1.0) (2025-09-22)


### Features

* add agent-driven resume ingestion ([1cd28b3](https://github.com/yamshy/resume-assistant/commit/1cd28b31dd6edbde7661dab9195d08cde915f3af))

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
