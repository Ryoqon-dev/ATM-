# 프로젝트 문서 안내

현재 프로젝트를 이해하려면 [Word 프로젝트 가이드](ATM_프로젝트_구조및개발가이드.docx)와 [루트 README](../README.md)를 먼저 읽습니다. 코드는 `src/atm_app` 아래에 계층별로 정리되어 있습니다.

| 위치 | 용도 |
| --- | --- |
| `ATM_프로젝트_구조및개발가이드.docx` | 현재 구조와 실행·시험·구현 계약을 한 문서로 정리한 Word 가이드 |
| [design](design/) | 11월 16일 피드백, 기존 상세설계서 HWPX·PDF·Markdown |
| [development](development/README.md) | 구현 전 수립한 인터페이스·데이터·시험 계획과 가상 시드 |
| [results](results/구현현황.md) | 현재 코드 대응, 자동 시험 결과, 구조 정리 검증 |
| [diagrams](diagrams/최종보완/) | UML PNG·SVG·PlantUML |
| [Visual Paradigm 모델](../models/visual-paradigm/) | 기존 VPP 원본 |

기존 HWPX와 PDF는 설계 기준 버전의 기록이며 바이너리 내용을 수정하지 않고 위치만 옮겼습니다. 옛 폴더명이나 개발 전 상태가 남아 있는 경우 현재 README와 Word 가이드를 기준으로 확인합니다. 문서·그림을 재생성하는 코드는 `tools/docs`에 있습니다.
