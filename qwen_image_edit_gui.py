import base64
import io
import mimetypes
import os
import threading
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import dashscope
from dashscope import MultiModalConversation
from PIL import Image, ImageTk
import requests
import tkinter as tk
from tkinter import filedialog, messagebox

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/api/v1"
PREVIEW_SIZE = (200, 200)
OUTPUT_SIZE = (420, 420)


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def image_to_payload(path_or_url: str) -> dict:
    if is_url(path_or_url):
        return {"image": path_or_url}

    path = Path(path_or_url)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path_or_url}")

    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "image/png"

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{encoded}"
    return {"image": data_uri}


def extract_image_url(response: dict) -> str:
    try:
        choices = response["output"]["choices"]
        message = choices[0]["message"]
        for item in message.get("content", []):
            if "image" in item:
                return item["image"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected response format from Qwen-Image-Edit") from exc

    raise ValueError("No image found in Qwen-Image-Edit response")


def download_image(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def load_thumbnail(image_path: Path, size: tuple[int, int]) -> ImageTk.PhotoImage:
    image = Image.open(image_path)
    image.thumbnail(size)
    return ImageTk.PhotoImage(image)


class QwenImageEditApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Qwen Image Edit")
        self.geometry("900x600")
        self.resizable(True, True)

        self.selected_image_1: Optional[Path] = None
        self.selected_image_2: Optional[Path] = None
        self.selected_image_3: Optional[Path] = None
        self.output_bytes: Optional[bytes] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
        self.output_photo: Optional[ImageTk.PhotoImage] = None
        self.preview_photo_2: Optional[ImageTk.PhotoImage] = None
        self.preview_photo_3: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        left_container = tk.Frame(main_frame)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(12, 0))

        left_canvas = tk.Canvas(left_container, highlightthickness=0)
        left_scrollbar = tk.Scrollbar(
            left_container, orient=tk.VERTICAL, command=left_canvas.yview
        )
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        left_frame = tk.Frame(left_canvas)
        left_canvas_window = left_canvas.create_window(
            (0, 0), window=left_frame, anchor="nw"
        )

        def _sync_left_width(event: tk.Event) -> None:
            left_canvas.itemconfig(left_canvas_window, width=event.width)

        def _sync_left_scrollregion(_: tk.Event) -> None:
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        left_canvas.bind("<Configure>", _sync_left_width)
        left_frame.bind("<Configure>", _sync_left_scrollregion)
        left_canvas.bind_all(
            "<MouseWheel>",
            lambda event: left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )

        select_button = tk.Button(
            left_frame, text="🔍 이미지 1 선택", command=self._select_image_1
        )
        select_button.grid(row=0, column=0, sticky="w")

        left_frame.grid_columnconfigure(0, weight=1)

        preview_frame = tk.Frame(left_frame, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1])
        preview_frame.grid(row=1, column=0, sticky="nsew", pady=8)
        preview_frame.grid_propagate(False)

        self.preview_label = tk.Label(
            preview_frame, text="이미지 1 미리보기", relief=tk.GROOVE
        )
        self.preview_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        image2_frame = tk.Frame(left_frame)
        image2_frame.grid(row=2, column=0, sticky="ew")
        self.image2_enabled = tk.BooleanVar(value=False)
        image2_check = tk.Checkbutton(
            image2_frame, text="이미지 2 포함", variable=self.image2_enabled
        )
        image2_check.pack(side=tk.LEFT)
        image2_button = tk.Button(
            image2_frame, text="🔍 이미지 2 선택", command=self._select_image_2
        )
        image2_button.pack(side=tk.LEFT, padx=8)

        preview_frame_2 = tk.Frame(
            left_frame, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1]
        )
        preview_frame_2.grid(row=3, column=0, sticky="nsew", pady=8)
        preview_frame_2.grid_propagate(False)

        self.preview_label_2 = tk.Label(
            preview_frame_2, text="이미지 2 미리보기", relief=tk.GROOVE
        )
        self.preview_label_2.place(relx=0, rely=0, relwidth=1, relheight=1)

        image3_frame = tk.Frame(left_frame)
        image3_frame.grid(row=4, column=0, sticky="ew")
        self.image3_enabled = tk.BooleanVar(value=False)
        image3_check = tk.Checkbutton(
            image3_frame, text="이미지 3 포함", variable=self.image3_enabled
        )
        image3_check.pack(side=tk.LEFT)
        image3_button = tk.Button(
            image3_frame, text="🔍 이미지 3 선택", command=self._select_image_3
        )
        image3_button.pack(side=tk.LEFT, padx=8)

        preview_frame_3 = tk.Frame(
            left_frame, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1]
        )
        preview_frame_3.grid(row=5, column=0, sticky="nsew", pady=8)
        preview_frame_3.grid_propagate(False)

        self.preview_label_3 = tk.Label(
            preview_frame_3, text="이미지 3 미리보기", relief=tk.GROOVE
        )
        self.preview_label_3.place(relx=0, rely=0, relwidth=1, relheight=1)

        prompt_label = tk.Label(left_frame, text="지시 프롬프트")
        prompt_label.grid(row=6, column=0, sticky="w")

        self.prompt_text = tk.Text(left_frame, height=5, wrap=tk.WORD)
        self.prompt_text.grid(row=7, column=0, sticky="ew", pady=(0, 8))

        negative_label = tk.Label(left_frame, text="금지 프롬프트")
        negative_label.grid(row=8, column=0, sticky="w")

        self.negative_text = tk.Text(left_frame, height=4, wrap=tk.WORD)
        self.negative_text.grid(row=9, column=0, sticky="ew", pady=(0, 8))

        self.generate_button = tk.Button(
            left_frame, text="생성", command=self._start_generation
        )
        self.generate_button.grid(row=10, column=0, sticky="w", pady=4)

        self.status_label = tk.Label(left_frame, text="대기 중")
        self.status_label.grid(row=11, column=0, sticky="w")

        output_title = tk.Label(right_frame, text="결과 이미지")
        output_title.pack(anchor=tk.W)

        self.output_label = tk.Label(
            right_frame, text="결과 이미지가 여기에 표시됩니다.", relief=tk.GROOVE
        )
        self.output_label.pack(fill=tk.BOTH, expand=True, pady=8)

        self.save_button = tk.Button(
            right_frame, text="PNG로 저장", command=self._save_output, state=tk.DISABLED
        )
        self.save_button.pack(anchor=tk.E)

        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        api_label = tk.Label(bottom_frame, text="API 키")
        api_label.pack(side=tk.LEFT)

        self.api_entry = tk.Entry(bottom_frame, show="*")
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        env_api_key = os.getenv("DASHSCOPE_API_KEY")
        if env_api_key:
            self.api_entry.insert(0, env_api_key)

    def _select_image_1(self) -> None:
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("All files", "*")],
        )
        if not file_path:
            return

        self.selected_image_1 = Path(file_path)
        try:
            self.preview_photo = load_thumbnail(self.selected_image_1, PREVIEW_SIZE)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as exc:
            messagebox.showerror("오류", f"이미지 미리보기에 실패했습니다: {exc}")

    def _select_image_2(self) -> None:
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("All files", "*")],
        )
        if not file_path:
            return

        self.selected_image_2 = Path(file_path)
        try:
            self.preview_photo_2 = load_thumbnail(self.selected_image_2, PREVIEW_SIZE)
            self.preview_label_2.configure(image=self.preview_photo_2, text="")
        except Exception as exc:
            messagebox.showerror("오류", f"이미지 미리보기에 실패했습니다: {exc}")

    def _select_image_3(self) -> None:
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("All files", "*")],
        )
        if not file_path:
            return

        self.selected_image_3 = Path(file_path)
        try:
            self.preview_photo_3 = load_thumbnail(self.selected_image_3, PREVIEW_SIZE)
            self.preview_label_3.configure(image=self.preview_photo_3, text="")
        except Exception as exc:
            messagebox.showerror("오류", f"이미지 미리보기에 실패했습니다: {exc}")

    def _start_generation(self) -> None:
        if not self.selected_image_1:
            messagebox.showwarning("안내", "이미지를 선택해주세요.")
            return
        if self.image2_enabled.get() and not self.selected_image_2:
            messagebox.showwarning("안내", "이미지 2를 선택해주세요.")
            return
        if self.image3_enabled.get() and not self.selected_image_3:
            messagebox.showwarning("안내", "이미지 3을 선택해주세요.")
            return

        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("안내", "API 키를 입력해주세요.")
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("안내", "프롬프트를 입력해주세요.")
            return

        negative_prompt = self.negative_text.get("1.0", tk.END).strip()

        self.generate_button.configure(state=tk.DISABLED)
        self.save_button.configure(state=tk.DISABLED)
        self.status_label.configure(text="생성 중...")

        thread = threading.Thread(
            target=self._generate_image,
            args=(
                api_key,
                prompt,
                negative_prompt,
                self.selected_image_1,
                self.selected_image_2,
                self.selected_image_3,
                self.image2_enabled.get(),
                self.image3_enabled.get(),
            ),
            daemon=True,
        )
        thread.start()

    def _generate_image(
        self,
        api_key: str,
        prompt: str,
        negative_prompt: str,
        image_path_1: Path,
        image_path_2: Optional[Path],
        image_path_3: Optional[Path],
        include_image_2: bool,
        include_image_3: bool,
    ) -> None:
        try:
            dashscope.base_http_api_url = DEFAULT_BASE_URL

            content = [image_to_payload(str(image_path_1))]
            if include_image_2 and image_path_2:
                content.append(image_to_payload(str(image_path_2)))
            if include_image_3 and image_path_3:
                content.append(image_to_payload(str(image_path_3)))
            content.append({"text": prompt})

            messages = [
                {
                    "role": "user",
                    "content": content,
                }
            ]

            response = MultiModalConversation.call(
                api_key=api_key,
                model="qwen-image-edit",
                messages=messages,
                result_format="message",
                stream=False,
                watermark=False,
                negative_prompt=negative_prompt,
            )

            image_url = extract_image_url(response)
            self.output_bytes = download_image(image_url)
        except Exception as exc:
            self.after(0, self._set_error, str(exc))
        finally:
            self.after(0, self._set_idle)

        if self.output_bytes:
            self.after(0, self._update_output_preview)

    def _update_output_preview(self) -> None:
        if not self.output_bytes:
            return

        try:
            image = Image.open(io.BytesIO(self.output_bytes))
            image.thumbnail(OUTPUT_SIZE)
            self.output_photo = ImageTk.PhotoImage(image)
            self.output_label.configure(image=self.output_photo, text="")
            self.save_button.configure(state=tk.NORMAL)
        except Exception as exc:
            self._set_error(f"결과 이미지 표시 실패: {exc}")

    def _save_output(self) -> None:
        if not self.output_bytes:
            messagebox.showwarning("안내", "저장할 결과가 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            title="PNG로 저장",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
        )
        if not file_path:
            return

        try:
            Path(file_path).write_bytes(self.output_bytes)
            messagebox.showinfo("완료", f"이미지를 저장했습니다: {file_path}")
        except Exception as exc:
            messagebox.showerror("오류", f"저장 실패: {exc}")

    def _set_error(self, message: str) -> None:
        self.status_label.configure(text=f"오류: {message}")

    def _set_idle(self) -> None:
        self.generate_button.configure(state=tk.NORMAL)
        self.status_label.configure(text="대기 중")


def main() -> None:
    app = QwenImageEditApp()
    app.mainloop()


if __name__ == "__main__":
    main()
