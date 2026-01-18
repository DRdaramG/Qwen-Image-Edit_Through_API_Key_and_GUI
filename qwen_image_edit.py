import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

import dashscope
from dashscope import MultiModalConversation
import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send images and a prompt to Qwen-Image-Edit and save the result."
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("DASHSCOPE_API_KEY"),
        help="DashScope API key (defaults to DASHSCOPE_API_KEY env var)",
    )
    parser.add_argument(
        "--image",
        action="append",
        required=True,
        help="Input image path or URL (can be provided multiple times)",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt text describing the edit",
    )
    parser.add_argument(
        "--output",
        default="qwen_edit_output.png",
        help="Output image filename",
    )
    parser.add_argument(
        "--negative-prompt",
        default="",
        help="Negative prompt text",
    )
    parser.add_argument(
        "--watermark",
        action="store_true",
        default=True,
        help="Enable watermark (default: enabled)",
    )
    parser.add_argument(
        "--no-watermark",
        action="store_false",
        dest="watermark",
        help="Disable watermark",
    )
    parser.add_argument(
        "--base-url",
        default="https://dashscope-intl.aliyuncs.com/api/v1",
        help="DashScope base API URL",
    )
    return parser.parse_args()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def image_to_payload(path_or_url: str) -> Dict[str, str]:
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


def build_messages(images: List[str], prompt: str) -> List[Dict[str, Any]]:
    content: List[Dict[str, str]] = [image_to_payload(item) for item in images]
    content.append({"text": prompt})
    return [{"role": "user", "content": content}]


def extract_image_url(response: Dict[str, Any]) -> str:
    try:
        choices = response["output"]["choices"]
        message = choices[0]["message"]
        for item in message.get("content", []):
            if "image" in item:
                return item["image"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected response format from Qwen-Image-Edit") from exc

    raise ValueError("No image found in Qwen-Image-Edit response")


def download_image(url: str, output_path: str) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    Path(output_path).write_bytes(response.content)


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise ValueError("API key is required (use --api-key or DASHSCOPE_API_KEY)")

    dashscope.base_http_api_url = args.base_url

    messages = build_messages(args.image, args.prompt)

    response = MultiModalConversation.call(
        api_key=args.api_key,
        model="qwen-image-edit",
        messages=messages,
        result_format="message",
        stream=False,
        watermark=args.watermark,
        negative_prompt=args.negative_prompt,
    )

    print(json.dumps(response, ensure_ascii=False, indent=2))

    image_url = extract_image_url(response)
    download_image(image_url, args.output)
    print(f"Saved output image to {args.output}")


if __name__ == "__main__":
    main()
