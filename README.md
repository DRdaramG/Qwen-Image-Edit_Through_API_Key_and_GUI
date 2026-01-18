# Qwen Image Edit GUI 사용법

이 프로젝트는 Qwen-Image-Edit 모델을 데스크탑 GUI로 사용할 수 있게 해주는 간단한 파이썬 앱입니다.

## 1) 파이썬 설치

- Windows: [python.org](https://www.python.org/downloads/)에서 최신 Python 3을 설치합니다.
- macOS: 터미널에서 `python3 --version`으로 설치 여부를 확인하거나, [python.org](https://www.python.org/downloads/)에서 설치합니다.

설치 후 아래 명령으로 정상 설치 여부를 확인합니다.

```bash
python --version
```

## 2) 프로젝트 다운로드

qwen_image_edit_gui.py 파일과 requirements.txt 파일을 이용하려는 위치에 다운로드하여 압축을 풀어 놓습니다.

## 3) 가상환경 생성 및 활성화 (권장)

```bash
python -m venv .venv
```

- Windows:
만일 자꾸 실패하신다면 해당 폴더 안의 activate 숼 스크립트를 관리자 권한으로 실행하셔도 됩니다.
```bash
.venv\Scripts\activate
```

- macOS / Linux:

```bash
source .venv/bin/activate
```

## 4) 의존성 설치

```bash
pip install -r requirements.txt
```

## 5) GUI 실행

아래 명령으로 GUI 앱을 실행합니다.

```bash
python qwen_image_edit_gui.py
```

## 6) 사용 방법 요약

1. **왼쪽 상단**의 🔍 버튼으로 입력 이미지 1을 선택합니다.
2. 필요하면 **이미지 2 포함**, **이미지 3 포함** 체크 후 각각의 이미지 선택 버튼으로 추가 이미지를 고릅니다.
3. **지시 프롬프트**에 원하는 변경 내용을 적습니다.
4. 필요하면 **금지 프롬프트**에 피하고 싶은 요소를 입력합니다.
5. **하단**의 API 키 입력칸에 DashScope API 키를 입력합니다.
6. **생성** 버튼을 눌러 결과를 받아옵니다.
7. **오른쪽 결과 이미지**가 표시되면 **PNG로 저장** 버튼으로 저장합니다.

## 참고

- API 키는 알리바바 클라우드에서 발급받아 사용합니다. (https://modelstudio.console.alibabacloud.com/)
- 결과 이미지는 PNG로 저장됩니다.
- 선택한 이미지는 위에서 아래 순서대로 input1, input2, input3으로 전송됩니다. 프롬프팅을 할 때 고려하여 주십시오.
