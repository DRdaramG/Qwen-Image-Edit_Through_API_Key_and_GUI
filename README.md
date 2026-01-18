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

```bash
git clone <레포지토리_URL>
cd Qwen-Image-Edit_Through_API_Key_and_GUI
```

## 3) 가상환경 생성 및 활성화 (권장)

```bash
python -m venv .venv
```

- Windows:

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

1. **왼쪽 상단**의 🔍 버튼으로 입력 이미지를 선택합니다.
2. **지시 프롬프트**에 원하는 변경 내용을 적습니다.
3. 필요하면 **금지 프롬프트**에 피하고 싶은 요소를 입력합니다.
4. **하단**의 API 키 입력칸에 DashScope API 키를 입력합니다.
5. **생성** 버튼을 눌러 결과를 받아옵니다.
6. **오른쪽 결과 이미지**가 표시되면 **PNG로 저장** 버튼으로 저장합니다.

## 참고

- API 키는 DashScope에서 발급받아 사용합니다.
- 결과 이미지는 PNG로 저장됩니다.
