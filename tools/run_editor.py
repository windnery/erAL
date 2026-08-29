#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
立绘头像可视化微调服务 (Avatar Cropper Server)
运行后自动在浏览器中打开可视化微调界面，支持鼠标拖拽选框、实时 116x116 预览、快捷键保存等。
"""

import os
import sys
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
from PIL import Image
import io

# 兼容 Windows 终端输出
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PORT = 8099


class AvatarEditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def do_GET(self):
        # 访问根目录或 /tools 重定向到 avatar_cropper.html
        if self.path in ['/', '/tools', '/tools/']:
            self.send_response(302)
            self.send_header('Location', '/tools/avatar_cropper.html')
            self.end_headers()
            return
        
        # 获取所有角色及皮肤立绘列表 API
        if self.path == '/api/skins':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            portraits_dir = os.path.join(PROJECT_ROOT, 'frontend', 'assets', 'portraits')
            avatars_dir = os.path.join(PROJECT_ROOT, 'frontend', 'assets', 'avatars')
            
            result = []
            if os.path.exists(portraits_dir):
                for chara in sorted(os.listdir(portraits_dir)):
                    p_char_dir = os.path.join(portraits_dir, chara)
                    if not os.path.isdir(p_char_dir):
                        continue
                    
                    skins = []
                    for f in sorted(os.listdir(p_char_dir)):
                        if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')):
                            base = os.path.splitext(f)[0]
                            has_avatar = os.path.exists(os.path.join(avatars_dir, chara, f"{base}.webp"))
                            skins.append({
                                'filename': f,
                                'basename': base,
                                'portrait_url': f'/frontend/assets/portraits/{chara}/{f}',
                                'avatar_url': f'/frontend/assets/avatars/{chara}/{base}.webp?t={int(os.path.getmtime(os.path.join(avatars_dir, chara, f"{base}.webp")))}' if has_avatar else None,
                                'has_avatar': has_avatar
                            })
                    if skins:
                        result.append({
                            'character': chara,
                            'skins': skins
                        })

            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return

        return super().do_GET()

    def do_POST(self):
        # 保存裁剪后的头像 API
        if self.path == '/api/save_avatar':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body.decode('utf-8'))

                character = data.get('character')
                basename = data.get('basename')
                crop_box = data.get('crop_box') # [x, y, size]

                if not character or not basename or not crop_box:
                    self.send_error(400, "Missing parameters")
                    return

                # 读取原图进行精准裁剪
                portraits_dir = os.path.join(PROJECT_ROOT, 'frontend', 'assets', 'portraits', character)
                avatars_dir = os.path.join(PROJECT_ROOT, 'frontend', 'assets', 'avatars', character)
                os.makedirs(avatars_dir, exist_ok=True)

                portrait_path = None
                for ext in ['.webp', '.png', '.jpg', '.jpeg']:
                    p = os.path.join(portraits_dir, f"{basename}{ext}")
                    if os.path.exists(p):
                        portrait_path = p
                        break

                if not portrait_path:
                    self.send_error(404, "Portrait not found")
                    return

                img = Image.open(portrait_path).convert('RGBA')
                W, H = img.size

                x, y, size = crop_box
                x1 = max(0, int(x))
                y1 = max(0, int(y))
                x2 = min(W, int(x + size))
                y2 = min(H, int(y + size))

                cropped = img.crop((x1, y1, x2, y2))
                avatar = cropped.resize((116, 116), Image.Resampling.LANCZOS)
                
                target_path = os.path.join(avatars_dir, f"{basename}.webp")
                avatar.save(target_path, format='WEBP', quality=95)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'message': f'头像已成功保存: {character}/{basename}.webp',
                    'avatar_url': f'/frontend/assets/avatars/{character}/{basename}.webp?t={int(os.path.getmtime(target_path))}'
                }, ensure_ascii=False).encode('utf-8'))
                print(f"[+] 头像已成功微调并保存: {character} / {basename}.webp")
            except Exception as e:
                self.send_error(500, str(e))
            return

        return super().do_POST()


def start_server():
    server_address = ('127.0.0.1', PORT)
    httpd = HTTPServer(server_address, AvatarEditorHandler)
    url = f"http://127.0.0.1:{PORT}/tools/avatar_cropper.html"
    print("=" * 65)
    print(" 碧蓝航线立绘头像可视化微调编辑器")
    print(f" 服务地址: {url}")
    print(" 提示: 按 Ctrl+C 可停止服务")
    print("=" * 65)
    
    # 自动在默认浏览器中打开
    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        httpd.server_close()


if __name__ == '__main__':
    start_server()
