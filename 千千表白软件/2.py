import os
import json
import sys
import time
import ctypes  # 导入ctypes库来调用Windows API

# --- 辅助函数：获取资源的绝对路径 ---
# 无论是在开发环境运行还是打包成exe后运行，都能正确定位文件
def resource_path(relative_path):
    """ 获取资源的绝对路径，适用于开发环境和PyInstaller打包后 """
    try:
        # 如果是打包后的 .exe 文件, 路径在 .exe 所在的目录
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            # 在开发环境中，是相对于当前脚本文件的路径
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    except Exception:
        # 如果出现意外，返回原始路径
        return relative_path

# --- Windows API 弹窗函数 ---
def win_message_box(title, text, style):
    """
    使用 ctypes 调用 Windows 的 MessageBoxW API 来显示一个原生弹窗。
    - title: 弹窗的标题
    - text: 弹窗显示的内容
    - style: 弹窗的样式 (决定按钮和图标)
    返回用户点击的按钮类型 (例如 IDYES, IDNO)
    """
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

# --- 定义 Windows MessageBox 的常量 ---
# 按钮样式
MB_OK = 0x00000000
MB_YESNO = 0x00000004
# 图标样式
MB_ICONQUESTION = 0x00000020
MB_ICONINFORMATION = 0x00000040
# 返回值
IDYES = 6
IDNO = 7
IDOK = 1


# --- 动态加载模块，并在失败时显示原生错误弹窗 ---
try:
    import webview
except ImportError:
    win_message_box("缺少模块", "请先安装 pywebview 模块 (pip install pywebview)", MB_OK | MB_ICONINFORMATION)
    sys.exit()
try:
    import pygame
except ImportError:
    win_message_box("缺少模块", "请先安装 pygame 模块 (pip install pygame)", MB_OK | MB_ICONINFORMATION)
    sys.exit()


# --- 内嵌的 HTML 模板 ---
# (这部分代码保持不变)
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>生日快乐</title>
<style>
    body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        background: #000;
        height: 100%;
    }
    canvas {
        position: absolute;
        width: 100%;
        height: 100%;
    }
    .text-canvas {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 9999;
        pointer-events: none;
    }
    .heart-text {
        position: fixed;
        top: 35%;
        left: 50%;
        transform: translateX(-50%);
        z-index: 100;
        pointer-events: none;
        display: none;
    }
    .heart-text h4 {
        font-family: "STKaiti";
        font-size: 40px;
        color: #f584b7;
        text-align: center;
        white-space: nowrap;
    }
</style>
</head>

<body>
    <canvas id="rain-canvas"></canvas>
    <canvas class="text-canvas"></canvas>
    <div class="heart-text">
        <h4>&#128151;{{HEART_TEXT_HTML}}</h4>
    </div>
    <canvas id="heart-canvas" style="display:none;"></canvas>

<script>
// ==================== 字符雨效果 ====================
function initRainEffect() {
    var canvas = document.getElementById('rain-canvas');
    var ctx = canvas.getContext('2d');
    canvas.height = window.innerHeight;
    canvas.width = window.innerWidth;
    var texts = 'I LOVE U'.split('');
    var fontSize = 16;
    var columns = canvas.width / fontSize;
    var drops = [];
    for (var x = 0; x < columns; x++) drops[x] = 1;
    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#f584b7';
        ctx.font = fontSize + 'px arial';
        for (var i = 0; i < drops.length; i++) {
            var text = texts[Math.floor(Math.random() * texts.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > canvas.height || Math.random() > 0.95) drops[i] = 0;
            drops[i]++;
        }
    }
    setInterval(draw, 33);
    window.addEventListener('resize', function() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        columns = canvas.width / fontSize;
        drops = [];
        for (var x = 0; x < columns; x++) drops[x] = 1;
    });
}
// ==================== 心形效果 ====================
function initHeartEffect() {
    var settings = { particles: { length: 500, duration: 2, velocity: 100, effect: -0.75, size: 30 } };
    var Point = function(x, y) { this.x = x || 0; this.y = y || 0; };
    Point.prototype = {
        clone: function() { return new Point(this.x, this.y); },
        length: function(length) {
            if (typeof length === 'undefined') return Math.sqrt(this.x * this.x + this.y * this.y);
            this.normalize(); this.x *= length; this.y *= length; return this;
        },
        normalize: function() { var length = this.length(); this.x /= length; this.y /= length; return this; }
    };
    var Particle = function() { this.position = new Point(); this.velocity = new Point(); this.acceleration = new Point(); this.age = 0; };
    Particle.prototype = {
        initialize: function(x, y, dx, dy) {
            this.position.x = x; this.position.y = y;
            this.velocity.x = dx; this.velocity.y = dy;
            this.acceleration.x = dx * settings.particles.effect; this.acceleration.y = dy * settings.particles.effect;
            this.age = 0;
        },
        update: function(deltaTime) {
            this.position.x += this.velocity.x * deltaTime; this.position.y += this.velocity.y * deltaTime;
            this.velocity.x += this.acceleration.x * deltaTime; this.velocity.y += this.acceleration.y * deltaTime;
            this.age += deltaTime;
        },
        draw: function(context, image) {
            function ease(t) { return (--t) * t * t + 1; }
            var size = image.width * ease(this.age / settings.particles.duration);
            context.globalAlpha = 1 - this.age / settings.particles.duration;
            context.drawImage(image, this.position.x - size / 2, this.position.y - size / 2, size, size);
        }
    };
    var ParticlePool = function(length) {
        var particles = new Array(length);
        for (var i = 0; i < particles.length; i++) particles[i] = new Particle();
        var firstActive = 0, firstFree = 0, duration = settings.particles.duration;
        return {
            add: function(x, y, dx, dy) {
                particles[firstFree].initialize(x, y, dx, dy);
                firstFree++; if (firstFree === particles.length) firstFree = 0;
                if (firstActive === firstFree) firstActive++; if (firstActive === particles.length) firstActive = 0;
            },
            update: function(deltaTime) {
                var i;
                if (firstActive < firstFree) for (i = firstActive; i < firstFree; i++) particles[i].update(deltaTime);
                if (firstFree < firstActive) {
                    for (i = firstActive; i < particles.length; i++) particles[i].update(deltaTime);
                    for (i = 0; i < firstFree; i++) particles[i].update(deltaTime);
                }
                while (particles[firstActive].age >= duration && firstActive !== firstFree) {
                    firstActive++; if (firstActive === particles.length) firstActive = 0;
                }
            },
            draw: function(context, image) {
                var i;
                if (firstActive < firstFree) for (i = firstActive; i < firstFree; i++) particles[i].draw(context, image);
                if (firstFree < firstActive) {
                    for (i = firstActive; i < particles.length; i++) particles[i].draw(context, image);
                    for (i = 0; i < firstFree; i++) particles[i].draw(context, image);
                }
            }
        };
    };
    function startHeartEffect() {
        var canvas = document.getElementById('heart-canvas');
        var context = canvas.getContext('2d');
        canvas.style.display = 'block';
        canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight;
        document.querySelector('.heart-text').style.display = 'block';
        var particles = new ParticlePool(settings.particles.length);
        var particleRate = settings.particles.length / settings.particles.duration;
        var time;
        function pointOnHeart(t) { return new Point(160 * Math.pow(Math.sin(t), 3), 130 * Math.cos(t) - 50 * Math.cos(2 * t) - 20 * Math.cos(3 * t) - 10 * Math.cos(4 * t) + 25); }
        var image = (function() {
            var canvas = document.createElement('canvas'), context = canvas.getContext('2d');
            canvas.width = settings.particles.size; canvas.height = settings.particles.size;
            function to(t) {
                var point = pointOnHeart(t);
                point.x = settings.particles.size / 2 + point.x * settings.particles.size / 350;
                point.y = settings.particles.size / 2 - point.y * settings.particles.size / 350;
                return point;
            }
            context.beginPath();
            var t = -Math.PI; var point = to(t); context.moveTo(point.x, point.y);
            while (t < Math.PI) { t += 0.01; point = to(t); context.lineTo(point.x, point.y); }
            context.closePath(); context.fillStyle = '#ea80b0'; context.fill();
            var image = new Image(); image.src = canvas.toDataURL(); return image;
        })();
        function render() {
            requestAnimationFrame(render);
            var newTime = new Date().getTime() / 1000, deltaTime = newTime - (time || newTime);
            time = newTime;
            context.clearRect(0, 0, canvas.width, canvas.height);
            var amount = particleRate * deltaTime;
            for (var i = 0; i < amount; i++) {
                var pos = pointOnHeart(Math.PI - 2 * Math.PI * Math.random());
                var dir = pos.clone().length(settings.particles.velocity);
                particles.add(canvas.width / 2 + pos.x, canvas.height / 2 - pos.y, dir.x, -dir.y);
            }
            particles.update(deltaTime); particles.draw(context, image);
        }
        window.addEventListener('resize', function() { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; });
        render();
    }
    return { start: startHeartEffect };
}
// ==================== 文字特效 ====================
function initTextEffect() {
    var Drawing = {
        canvas: null, context: null, renderFn: null,
        requestFrame: window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame || function(callback) { window.setTimeout(callback, 1000 / 60); },
        init: function(el) {
            this.canvas = document.querySelector(el); this.context = this.canvas.getContext('2d'); this.adjustCanvas();
            window.addEventListener('resize', function(e) { this.adjustCanvas(); }.bind(this));
        },
        loop: function(fn) { this.renderFn = !this.renderFn ? fn : this.renderFn; this.clearFrame(); this.renderFn(); this.requestFrame.call(window, this.loop.bind(this)); },
        adjustCanvas: function() { this.canvas.width = window.innerWidth; this.canvas.height = window.innerHeight; },
        clearFrame: function() { this.context.clearRect(0, 0, this.canvas.width, this.canvas.height); },
        getArea: function() { return { w: this.canvas.width, h: this.canvas.height }; },
        drawCircle: function(p, c) { this.context.fillStyle = c.render(); this.context.beginPath(); this.context.arc(p.x, p.y, p.z, 0, 2 * Math.PI, true); this.context.closePath(); this.context.fill(); }
    };
    var Point = function(args) { this.x = args.x; this.y = args.y; this.z = args.z; this.a = args.a; this.h = args.h; };
    var Color = function(r, g, b, a) { this.r = r; this.g = g; this.b = b; this.a = a; this.render = function() { return 'rgba(' + this.r + ',' + this.g + ',' + this.b + ',' + this.a + ')'; }; };
    var Dot = function(x, y) {
        this.p = new Point({ x: x, y: y, z: 5, a: 1, h: 0 });
        this.e = 0.07; this.s = true; this.c = new Color(255, 255, 255, this.p.a); this.t = this.clone(); this.q = [];
    };
    Dot.prototype = {
        clone: function() { return new Point({ x: this.x, y: this.y, z: this.z, a: this.a, h: this.h }); },
        _draw: function() { this.c.a = this.p.a; Drawing.drawCircle(this.p, this.c); },
        _moveTowards: function(n) {
            var details = this.distanceTo(n, true), dx = details[0], dy = details[1], d = details[2], e = this.e * d;
            if (this.p.h === -1) { this.p.x = n.x; this.p.y = n.y; return true; }
            if (d > 1) { this.p.x -= ((dx / d) * e); this.p.y -= ((dy / d) * e); }
            else { if (this.p.h > 0) this.p.h--; else return true; }
            return false;
        },
        _update: function() {
            if (this._moveTowards(this.t)) {
                var p = this.q.shift();
                if (p) { this.t.x = p.x || this.p.x; this.t.y = p.y || this.p.y; this.t.z = p.z || this.p.z; this.t.a = p.a || this.p.a; this.p.h = p.h || 0; }
                else {
                    if (this.s) { this.p.x -= Math.sin(Math.random() * 3.142); this.p.y -= Math.sin(Math.random() * 3.142); }
                    else { this.move(new Point({ x: this.p.x + (Math.random() * 50) - 25, y: this.p.y + (Math.random() * 50) - 25 })); }
                }
            }
            var d = this.p.a - this.t.a; this.p.a = Math.max(0.1, this.p.a - (d * 0.05));
            d = this.p.z - this.t.z; this.p.z = Math.max(1, this.p.z - (d * 0.05));
        },
        distanceTo: function(n, details) { var dx = this.p.x - n.x, dy = this.p.y - n.y, d = Math.sqrt(dx * dx + dy * dy); return details ? [dx, dy, d] : d; },
        move: function(p, avoidStatic) { if (!avoidStatic || (avoidStatic && this.distanceTo(p) > 1)) this.q.push(p); },
        render: function() { this._update(); this._draw(); }
    };
    var Shape = {
        dots: [], width: 0, height: 0, cx: 0, cy: 0,
        compensate: function() { var a = Drawing.getArea(); this.cx = a.w / 2 - this.width / 2; this.cy = a.h / 2 - this.height / 2; },
        shuffleIdle: function() { var a = Drawing.getArea(); for (var d = 0; d < this.dots.length; d++) if (!this.dots[d].s) this.dots[d].move({ x: Math.random() * a.w, y: Math.random() * a.h }); },
        switchShape: function(n, fast) {
            var size, a = Drawing.getArea();
            this.width = n.w; this.height = n.h; this.compensate();
            if (n.dots.length > this.dots.length) { size = n.dots.length - this.dots.length; for (var d = 1; d <= size; d++) this.dots.push(new Dot(a.w / 2, a.h / 2)); }
            var d = 0, i;
            while (n.dots.length > 0) {
                i = Math.floor(Math.random() * n.dots.length);
                this.dots[d].e = fast ? 0.25 : (this.dots[d].s ? 0.14 : 0.11);
                if (this.dots[d].s) this.dots[d].move(new Point({ z: Math.random() * 20 + 10, a: Math.random(), h: 18 }));
                else this.dots[d].move(new Point({ z: Math.random() * 5 + 5, h: fast ? 18 : 30 }));
                this.dots[d].s = true;
                this.dots[d].move(new Point({ x: n.dots[i].x + this.cx, y: n.dots[i].y + this.cy, a: 1, z: 5, h: 0 }));
                n.dots = n.dots.slice(0, i).concat(n.dots.slice(i + 1));
                d++;
            }
            for (var i = d; i < this.dots.length; i++) {
                if (this.dots[i].s) {
                    this.dots[i].move(new Point({ z: Math.random() * 20 + 10, a: Math.random(), h: 20 }));
                    this.dots[i].s = false; this.dots[i].e = 0.04;
                    this.dots[i].move(new Point({ x: Math.random() * a.w, y: Math.random() * a.h, a: 0.3, z: Math.random() * 4, h: 0 }));
                }
            }
        },
        render: function() { for (var d = 0; d < this.dots.length; d++) this.dots[d].render(); }
    };
    var ShapeBuilder = {
        gap: 13, shapeCanvas: document.createElement('canvas'), shapeContext: null, fontSize: 500, fontFamily: 'Avenir, Helvetica Neue, Helvetica, Arial, sans-serif',
        init: function() { this.shapeContext = this.shapeCanvas.getContext('2d'); this.fit(); },
        fit: function() {
            this.shapeCanvas.width = Math.floor(window.innerWidth / this.gap) * this.gap;
            this.shapeCanvas.height = Math.floor(window.innerHeight / this.gap) * this.gap;
            this.shapeContext.fillStyle = 'red'; this.shapeContext.textBaseline = 'middle'; this.shapeContext.textAlign = 'center';
        },
        processCanvas: function() {
            var pixels = this.shapeContext.getImageData(0, 0, this.shapeCanvas.width, this.shapeCanvas.height).data;
            var dots = [], x = 0, y = 0, fx = this.shapeCanvas.width, fy = this.shapeCanvas.height, w = 0, h = 0;
            for (var p = 0; p < pixels.length; p += (4 * this.gap)) {
                if (pixels[p + 3] > 0) {
                    dots.push(new Point({ x: x, y: y }));
                    w = x > w ? x : w; h = y > h ? y : h; fx = x < fx ? x : fx; fy = y < fy ? y : fy;
                }
                x += this.gap;
                if (x >= this.shapeCanvas.width) { x = 0; y += this.gap; p += this.gap * 4 * this.shapeCanvas.width; }
            }
            return { dots: dots, w: w + fx, h: h + fy };
        },
        setFontSize: function(s) { this.shapeContext.font = 'bold ' + s + 'px ' + this.fontFamily; },
        letter: function(l) {
            var s = 0; this.fit(); this.setFontSize(this.fontSize);
            s = Math.min(this.fontSize, (this.shapeCanvas.width / this.shapeContext.measureText(l).width) * 0.8 * this.fontSize, (this.shapeCanvas.height / this.fontSize) * (isFinite(l) ? 1 : 0.45) * this.fontSize);
            this.setFontSize(s);
            this.shapeContext.clearRect(0, 0, this.shapeCanvas.width, this.shapeCanvas.height);
            this.shapeContext.fillText(l, this.shapeCanvas.width / 2, this.shapeCanvas.height / 2);
            return this.processCanvas();
        }
    };
    Drawing.init('.text-canvas'); ShapeBuilder.init();
    function simulate(sequence) {
        var current, index = 0;
        function next() {
            if (index < sequence.length) {
                current = sequence[index]; index++;
                if (current === '#countdown 3') {
                    var count = 3;
                    var countdown = setInterval(function() {
                        if (count > 0) Shape.switchShape(ShapeBuilder.letter(count), true);
                        else { clearInterval(countdown); next(); }
                        count--;
                    }, 1000);
                } else if (current === '#rectangle') {
                    setTimeout(function() {
                        document.querySelector('.text-canvas').style.display = 'none';
                        var heartEffect = initHeartEffect(); heartEffect.start();
                    }, 1000);
                } else {
                    Shape.switchShape(ShapeBuilder.letter(current));
                    setTimeout(next, 2000);
                }
            }
        }
        next();
    }
    Drawing.loop(function() { Shape.render(); });
    simulate(['#countdown 3', ...{{HTML_TEXTS_JSON}}, '#rectangle']);
}
window.onload = function() { initRainEffect(); initTextEffect(); };
</script>
<script>
    document.addEventListener('keydown', function(e) {
        if (e.keyCode === 27) { // ESC key
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.close_window === 'function') {
                window.pywebview.api.close_window();
            }
        }
    });
</script>
</body>
</html>
'''


class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def close_window(self):
        if self._window:
            self._window.destroy()


def show_confession():
    config_file = resource_path('config.json')

    if not os.path.exists(config_file):
        win_message_box("错误", "配置文件 'config.json' 未找到！", MB_OK | MB_ICONINFORMATION)
        return

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            full_config = json.load(f)
    except Exception as e:
        win_message_box("错误", f"读取配置文件 'config.json' 失败: {e}", MB_OK | MB_ICONINFORMATION)
        return

    # 从配置中读取数据
    popups_config = full_config.get("popups", [])
    delay = full_config.get("delay", 0)
    music_file_raw = full_config.get("music_file", "")
    # 如果音乐文件是相对路径，转换为绝对路径
    music_file = resource_path(music_file_raw) if music_file_raw and not os.path.isabs(music_file_raw) else music_file_raw
    volume = full_config.get("volume", 0.5)
    final_rejection_text = full_config.get("final_rejection_text", "好吧，看来你真的不喜欢我...")

    # 根据配置动态生成最终的 HTML 内容
    html_texts = full_config.get("html_texts", ['亲爱的', '节日快乐', '我爱你'])
    heart_text = full_config.get("heart_text", '我会永远\n陪着你').replace('\n', '<br>')
    html_texts_json = json.dumps(html_texts, ensure_ascii=False)

    final_html = HTML_TEMPLATE.replace('{{HEART_TEXT_HTML}}', heart_text)
    final_html = final_html.replace('{{HTML_TEXTS_JSON}}', html_texts_json)

    if delay > 0:
        time.sleep(delay)

    for config in popups_config:
        is_mandatory = config.get("is_mandatory", False)
        title = config.get("title", "提示")
        content = config.get("content", "")

        # --- 使用原生弹窗 ---
        # 如果是强制弹窗，则循环直到用户点击"是"
        if is_mandatory:
            while True:
                response = win_message_box(title, content, MB_YESNO | MB_ICONQUESTION)
                if response == IDYES:
                    break # 用户点击"是"，跳出循环
        else:
            response = win_message_box(title, content, MB_YESNO | MB_ICONQUESTION)

        # 检查用户是否点击了"是"
        if response == IDYES:
            try:
                if music_file and os.path.exists(music_file):
                    pygame.mixer.init()
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.set_volume(float(volume))
                    pygame.mixer.music.play(-1)

                api = Api()
                window = webview.create_window(' ', html=final_html, fullscreen=True, on_top=True, js_api=api)
                api.set_window(window)
                webview.start()

                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception as e:
                win_message_box("错误", f"程序运行出错: {e}", MB_OK | MB_ICONINFORMATION)
            return # 无论成功或失败，只要同意了就结束程序

    # 如果循环结束都没有同意，则显示最终拒绝信息
    win_message_box("提示", final_rejection_text, MB_OK | MB_ICONINFORMATION)


if __name__ == "__main__":
    # --- 主程序入口 ---
    # 不再需要Tkinter窗口，直接调用主逻辑
    show_confession()